"""
佣金定时任务

⭐ Phase D: 两个定时任务
1. release_held_commissions - 释放锁定佣金（每小时）
2. cleanup_old_idempotency_keys - 清理过期幂等键（每天）
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def release_held_commissions(self):
    """
    释放锁定佣金
    
    ⭐ 定时任务：每小时整点运行
    - 查询 status='hold' 且 hold_until <= now 的佣金
    - 状态改为 'ready'
    - 分页处理
    
    Returns:
        dict: {'processed': int, 'released': int}
    """
    from apps.commissions.models import Commission
    
    page_size = 100
    processed = 0
    released = 0
    
    cutoff = timezone.now()
    logger.info(f"Starting release_held_commissions task, cutoff={cutoff}")
    
    while True:
        held_commissions = Commission.objects.filter(
            status='hold',
            hold_until__lte=cutoff
        )[:page_size]
        
        held_list = list(held_commissions)
        if not held_list:
            break
        
        for commission in held_list:
            processed += 1
            
            try:
                with transaction.atomic():
                    updated = Commission.objects.filter(
                        commission_id=commission.commission_id,
                        status='hold'
                    ).update(
                        status='ready',
                        updated_at=timezone.now()
                    )
                    
                    if updated > 0:
                        released += 1
                        logger.debug(f"Released commission {commission.commission_id}")
                        
            except Exception as e:
                logger.error(
                    f"Failed to release commission {commission.commission_id}: {e}",
                    exc_info=True
                )
        
        if len(held_list) < page_size:
            break
    
    result = {'processed': processed, 'released': released}
    logger.info(f"Released {released} commissions", extra=result)
    return result


@shared_task
def calculate_commissions_for_order(order_id: str):
    """
    计算订单佣金（Webhook触发）
    
    ⭐ 使用快照数据，防止计划变更影响已成单佣金
    
    Args:
        order_id: 订单UUID
    """
    from apps.orders.models import Order
    from apps.commissions.models import Commission
    from apps.orders_snapshots.models import OrderCommissionSnapshot
    from apps.users.utils.referral_chain import get_referral_chain
    from apps.core.utils.money import calculate_commission_amount
    from django.conf import settings
    
    try:
        order = Order.objects.select_related('buyer', 'site').get(order_id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order not found: {order_id}")
        return
    
    # 获取快照
    snapshot = OrderCommissionSnapshot.objects.filter(order_id=order_id).first()
    if not snapshot:
        logger.warning(f"No commission snapshot for order {order_id}")
        return
    
    # 获取推荐链（含环路检测）⭐
    try:
        chain = get_referral_chain(order.buyer, max_levels=snapshot.max_levels)
    except Exception as e:
        logger.error(
            f"Failed to get referral chain for order {order_id}: {e}",
            exc_info=True
        )
        return
    
    # 计算每层佣金
    hold_days = settings.COMMISSION_HOLD_DAYS
    hold_until = timezone.now() + timedelta(days=hold_days)
    
    for chain_item in chain:
        agent = chain_item['agent']
        level = chain_item['level']
        
        # 从快照获取该层级费率
        tier = snapshot.tiers.filter(level=level).first()
        if not tier:
            continue
        
        # 计算佣金（使用量化函数）⭐
        commission_amount = calculate_commission_amount(
            order.final_price_usd,
            tier.rate_percent
        )
        
        # 创建佣金记录
        Commission.objects.create(
            site_id=order.site_id,
            agent=agent,
            order=order,
            level=level,
            rate_percent=tier.rate_percent,
            commission_amount_usd=commission_amount,
            status='hold',
            hold_until=hold_until
        )
        
        logger.info(
            f"Commission created: order={order_id}, agent={agent.user_id}, "
            f"level={level}, amount={commission_amount}",
            extra={
                'order_id': order_id,
                'agent_id': str(agent.user_id),
                'level': level,
                'amount': str(commission_amount)
            }
        )

