"""
佣金计算任务

⭐ Phase D 核心功能：
- 从订单快照读取佣金配置
- 计算推荐链佣金（含环路检测）
- 金额精度统一（ROUND_HALF_UP）
- 原子性创建佣金记录
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Set
from uuid import UUID
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.orders.models import Order
from apps.users.models import User
from apps.commissions.models import Commission
from apps.orders_snapshots.models import OrderCommissionSnapshot

logger = logging.getLogger(__name__)


def quantize_commission(amount: Decimal) -> Decimal:
    """
    量化佣金金额到2位小数
    
    ⭐ Phase D P0: 统一精度策略
    - 与 Stripe to_cents/from_cents 保持一致
    - 使用 ROUND_HALF_UP（银行家舍入）
    """
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_referral_chain(user: User, max_levels: int = 2) -> List[dict]:
    """
    获取推荐链路
    
    ⭐ Phase D P0: 环路检测
    
    Args:
        user: 当前用户
        max_levels: 最大层级（默认2层）
        
    Returns:
        list: 推荐链列表 [{'agent': User, 'level': 1}, ...]
    """
    chain = []
    visited: Set[UUID] = set()  # ⭐ 环路检测
    current_user = user
    
    for level in range(1, max_levels + 1):
        if not current_user.referrer:
            break
        
        # ⭐ 环路检测
        if current_user.referrer.user_id in visited:
            logger.error(
                f"Circular referral detected: {current_user.user_id} → "
                f"{current_user.referrer.user_id}",
                extra={
                    'user_id': str(current_user.user_id),
                    'referrer_id': str(current_user.referrer.user_id),
                    'visited': [str(uid) for uid in visited]
                }
            )
            break
        
        visited.add(current_user.referrer.user_id)
        chain.append({
            'agent': current_user.referrer,
            'level': level
        })
        current_user = current_user.referrer
    
    return chain


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_commission_for_order(self, order_id: str):
    """
    计算订单佣金（Celery 任务）
    
    ⭐ Phase D 核心逻辑：
    1. 从快照读取佣金配置
    2. 获取推荐链（含环路检测）
    3. 计算各级佣金（精度统一）
    4. 原子性创建佣金记录
    
    Args:
        order_id: 订单ID（字符串）
    """
    logger.info(
        f"Starting commission calculation for order {order_id}",
        extra={'order_id': order_id, 'task_id': self.request.id}
    )
    
    try:
        # 1. 获取订单
        order = Order.objects.select_related('buyer__referrer', 'site').get(
            order_id=UUID(order_id)
        )
        
        # 2. 检查订单状态
        if order.status != Order.STATUS_PAID:
            logger.warning(
                f"Order {order_id} status is {order.status}, not paid. Skip commission.",
                extra={'order_id': order_id, 'status': order.status}
            )
            return
        
        # 3. 获取佣金快照
        try:
            snapshot = OrderCommissionSnapshot.objects.get(order=order)
        except OrderCommissionSnapshot.DoesNotExist:
            logger.error(
                f"Commission snapshot not found for order {order_id}",
                extra={'order_id': order_id}
            )
            return
        
        # 4. 获取推荐链（含环路检测）⭐
        referral_chain = get_referral_chain(order.buyer, max_levels=2)
        
        if not referral_chain:
            logger.info(
                f"No referral chain for order {order_id}, no commission to calculate",
                extra={'order_id': order_id}
            )
            return
        
        # 5. 计算锁定时长
        hold_days = getattr(settings, 'COMMISSION_HOLD_DAYS', 7)
        hold_until = timezone.now() + timedelta(days=hold_days)
        
        # 6. 原子性创建佣金记录
        commissions_created = []
        
        with transaction.atomic():
            for chain_item in referral_chain:
                agent = chain_item['agent']
                level = chain_item['level']
                
                # 获取对应层级的费率
                rate_percent = None
                if level == 1:
                    rate_percent = snapshot.level_1_rate_percent
                elif level == 2:
                    rate_percent = snapshot.level_2_rate_percent
                
                if not rate_percent or rate_percent <= 0:
                    continue
                
                # ⭐ 计算佣金金额（精度统一）
                raw_amount = order.final_price_usd * (rate_percent / Decimal('100'))
                commission_amount = quantize_commission(raw_amount)  # ⭐ 量化到2位
                
                # 创建佣金记录
                commission = Commission.objects.create(
                    order=order,
                    agent=agent,
                    level=level,
                    rate_percent=rate_percent,
                    commission_amount_usd=commission_amount,
                    status=Commission.STATUS_HOLD,
                    hold_until=hold_until
                )
                
                commissions_created.append(commission)
                
                logger.info(
                    f"Commission created: level={level}, agent={agent.user_id}, "
                    f"amount={commission_amount}",
                    extra={
                        'commission_id': str(commission.commission_id),
                        'order_id': order_id,
                        'agent_id': str(agent.user_id),
                        'level': level,
                        'rate': str(rate_percent),
                        'amount': str(commission_amount)
                    }
                )
        
        logger.info(
            f"Commission calculation completed for order {order_id}: "
            f"{len(commissions_created)} commissions created",
            extra={
                'order_id': order_id,
                'commissions_count': len(commissions_created),
                'total_amount': str(sum(c.commission_amount_usd for c in commissions_created))
            }
        )
    
    except Order.DoesNotExist:
        logger.error(
            f"Order {order_id} not found",
            extra={'order_id': order_id}
        )
    
    except Exception as e:
        logger.error(
            f"Commission calculation failed for order {order_id}: {e}",
            exc_info=True,
            extra={'order_id': order_id}
        )
        # 重试
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3)
def release_held_commissions(self):
    """
    释放锁定期已过的佣金
    
    ⭐ Celery Beat 定时任务（每小时运行）
    - 将 status='hold' 且 hold_until <= now 的佣金更新为 'ready'
    """
    logger.info("Starting release_held_commissions task")
    
    cutoff_time = timezone.now()
    
    # 查询符合条件的佣金
    held_commissions = Commission.objects.filter(
        status=Commission.STATUS_HOLD,
        hold_until__lte=cutoff_time
    )
    
    count = held_commissions.count()
    
    if count == 0:
        logger.info("No held commissions to release")
        return
    
    # 批量更新
    updated_count = held_commissions.update(
        status=Commission.STATUS_READY,
        updated_at=timezone.now()
    )
    
    logger.info(
        f"Released {updated_count} held commissions",
        extra={
            'released_count': updated_count,
            'cutoff_time': cutoff_time.isoformat()
        }
    )
