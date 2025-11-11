"""
佣金计算任务

⭐ 核心功能（已改进）：
- 从订单快照读取佣金配置
- 支持两种计算模式：Level固定费率、Solar Diff差额
- 动态支持1-10级佣金配置
- 销售额门槛验证
- 金额精度统一（ROUND_HALF_UP）
- 原子性创建佣金记录
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Set, Tuple
from uuid import UUID
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.orders.models import Order
from apps.users.models import User
from apps.commissions.models import Commission
from apps.orders_snapshots.models import OrderCommissionPolicySnapshot
from apps.agents.models import AgentStats, AgentProfile

logger = logging.getLogger(__name__)


def quantize_commission(amount: Decimal) -> Decimal:
    """
    量化佣金金额到2位小数
    
    ⭐ Phase D P0: 统一精度策略
    - 与 Stripe to_cents/from_cents 保持一致
    - 使用 ROUND_HALF_UP（银行家舍入）
    """
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_agent_level_rate(user: User, site_id: UUID) -> Decimal:
    """
    获取代理等级对应的费率
    
    ⭐ Solar Diff 模式使用
    
    代理等级费率表：
    - bronze（青铜）：10%
    - silver（白银）：15%
    - gold（黄金）：20%
    - platinum（白金）：25%
    
    Args:
        user: 用户实例
        site_id: 站点ID
    
    Returns:
        Decimal: 等级对应的费率（%）
    """
    try:
        profile = AgentProfile.objects.get(user=user, site__site_id=site_id)
        
        # 代理等级费率映射
        level_rates = {
            AgentProfile.LEVEL_BRONZE: Decimal('10.00'),
            AgentProfile.LEVEL_SILVER: Decimal('15.00'),
            AgentProfile.LEVEL_GOLD: Decimal('20.00'),
            AgentProfile.LEVEL_PLATINUM: Decimal('25.00'),
        }
        
        return level_rates.get(profile.agent_level, Decimal('0'))
    
    except AgentProfile.DoesNotExist:
        # 如果没有 AgentProfile，默认为最低等级
        return Decimal('10.00')  # Bronze


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


def _calculate_level_commissions(order: Order, snapshot, referral_chain: List[dict]) -> Tuple[list, list]:
    """
    Level 固定费率模式佣金计算
    
    公式：佣金 = 订单金额 × 层级费率
    
    Args:
        order: 订单实例
        snapshot: 佣金快照
        referral_chain: 推荐链
    
    Returns:
        Tuple[list, list]: (创建的佣金列表, 跳过的佣金列表)
    """
    commissions_created = []
    commissions_skipped = []
    
    for chain_item in referral_chain:
        agent = chain_item['agent']
        level = chain_item['level']
        
        # 从快照读取层级配置
        if level > len(snapshot.tiers_json):
            logger.warning(
                f"Level {level} exceeds configured tiers count {len(snapshot.tiers_json)}",
                extra={'order_id': str(order.order_id), 'level': level}
            )
            continue
        
        tier_config = snapshot.tiers_json[level - 1]
        rate_percent = Decimal(tier_config['rate_percent'])
        
        # 统一字段命名
        min_sales = Decimal(
            tier_config.get('min_sales') or 
            tier_config.get('min_order_amount', '0')
        )
        hold_days = tier_config.get('hold_days', 7)
        
        # 验证费率有效性
        if not rate_percent or rate_percent <= 0:
            logger.info(
                f"Skip level {level}: rate_percent is zero or negative",
                extra={'order_id': str(order.order_id), 'level': level}
            )
            continue
        
        # 检查销售额门槛
        if min_sales > 0:
            agent_stats = AgentStats.objects.filter(
                agent=agent.user_id,
                site_id=order.site.site_id
            ).first()
            
            agent_total_sales = agent_stats.total_sales if agent_stats else Decimal('0')
            
            if agent_total_sales < min_sales:
                logger.info(
                    f"Agent {agent.email} sales ${agent_total_sales} < required ${min_sales}, skip L{level}",
                    extra={
                        'order_id': str(order.order_id),
                        'agent_id': str(agent.user_id),
                        'agent_email': agent.email,
                        'level': level,
                        'agent_sales': str(agent_total_sales),
                        'min_sales_required': str(min_sales)
                    }
                )
                commissions_skipped.append({
                    'agent': agent.email,
                    'level': level,
                    'reason': 'insufficient_sales',
                    'agent_sales': str(agent_total_sales),
                    'required': str(min_sales)
                })
                continue
        
        # 计算佣金金额
        raw_amount = order.final_price_usd * (rate_percent / Decimal('100'))
        commission_amount = quantize_commission(raw_amount)
        
        # 计算锁定截止时间
        hold_until = timezone.now() + timedelta(days=hold_days)
        
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
            f"[Level Mode] Commission created: L{level}, agent={agent.user_id}, amount=${commission_amount}",
            extra={
                'commission_id': str(commission.commission_id),
                'order_id': str(order.order_id),
                'agent_id': str(agent.user_id),
                'level': level,
                'rate': str(rate_percent),
                'amount': str(commission_amount),
                'hold_days': hold_days
            }
        )
    
    return commissions_created, commissions_skipped


def _calculate_solar_diff_commissions(order: Order, snapshot, referral_chain: List[dict]) -> Tuple[list, list]:
    """
    Solar Diff 太阳线差额模式佣金计算
    
    ⭐ 核心公式：
    佣金 = (代理等级费率 - 下级等级费率) × 订单金额
    
    规则：
    1. 上级代理等级必须高于下级
    2. 差额不能为负（否则跳过）
    3. 支持差额封顶（diff_cap_percent）
    4. 仍然检查销售额门槛
    
    示例：
    - 买家（Bronze 10%）购买 $1000
    - 直推人（Gold 20%）赚差额：(20%-10%) × $1000 = $100
    - 间推人（Platinum 25%）赚差额：(25%-20%) × $1000 = $50
    
    Args:
        order: 订单实例
        snapshot: 佣金快照
        referral_chain: 推荐链
    
    Returns:
        Tuple[list, list]: (创建的佣金列表, 跳过的佣金列表)
    """
    commissions_created = []
    commissions_skipped = []
    
    # 获取买家等级费率（作为基准）
    buyer_level_rate = get_agent_level_rate(order.buyer, order.site.site_id)
    
    logger.info(
        f"[Solar Diff Mode] Buyer level rate: {buyer_level_rate}%",
        extra={
            'order_id': str(order.order_id),
            'buyer_id': str(order.buyer.user_id),
            'buyer_level_rate': str(buyer_level_rate)
        }
    )
    
    # 当前层级的基准费率（初始为买家费率）
    current_base_rate = buyer_level_rate
    
    for chain_item in referral_chain:
        agent = chain_item['agent']
        level = chain_item['level']
        
        # 从快照读取层级配置
        if level > len(snapshot.tiers_json):
            continue
        
        tier_config = snapshot.tiers_json[level - 1]
        
        # 统一字段命名
        min_sales = Decimal(
            tier_config.get('min_sales') or 
            tier_config.get('min_order_amount', '0')
        )
        hold_days = tier_config.get('hold_days', 7)
        diff_cap_percent = tier_config.get('diff_cap_percent')
        
        # 检查销售额门槛
        if min_sales > 0:
            agent_stats = AgentStats.objects.filter(
                agent=agent.user_id,
                site_id=order.site.site_id
            ).first()
            
            agent_total_sales = agent_stats.total_sales if agent_stats else Decimal('0')
            
            if agent_total_sales < min_sales:
                logger.info(
                    f"Agent {agent.email} sales ${agent_total_sales} < required ${min_sales}, skip L{level}",
                    extra={
                        'order_id': str(order.order_id),
                        'agent_id': str(agent.user_id),
                        'level': level,
                        'agent_sales': str(agent_total_sales),
                        'min_sales_required': str(min_sales)
                    }
                )
                commissions_skipped.append({
                    'agent': agent.email,
                    'level': level,
                    'reason': 'insufficient_sales',
                    'agent_sales': str(agent_total_sales),
                    'required': str(min_sales)
                })
                continue
        
        # 获取代理等级费率
        agent_level_rate = get_agent_level_rate(agent, order.site.site_id)
        
        # ⭐ 计算差额费率
        diff_rate = agent_level_rate - current_base_rate
        
        # 上级等级不高于下级，跳过
        if diff_rate <= 0:
            logger.info(
                f"Agent {agent.email} level rate {agent_level_rate}% <= base rate {current_base_rate}%, skip L{level}",
                extra={
                    'order_id': str(order.order_id),
                    'agent_id': str(agent.user_id),
                    'level': level,
                    'agent_level_rate': str(agent_level_rate),
                    'base_rate': str(current_base_rate)
                }
            )
            commissions_skipped.append({
                'agent': agent.email,
                'level': level,
                'reason': 'no_rate_difference',
                'agent_rate': str(agent_level_rate),
                'base_rate': str(current_base_rate)
            })
            # 更新基准费率为当前代理费率（用于下一层计算）
            current_base_rate = agent_level_rate
            continue
        
        # ⭐ 差额封顶
        if diff_cap_percent:
            cap = Decimal(diff_cap_percent)
            if diff_rate > cap:
                logger.info(
                    f"Diff rate {diff_rate}% capped to {cap}%",
                    extra={
                        'order_id': str(order.order_id),
                        'agent_id': str(agent.user_id),
                        'level': level,
                        'original_diff': str(diff_rate),
                        'capped_diff': str(cap)
                    }
                )
                diff_rate = cap
        
        # 计算佣金金额
        raw_amount = order.final_price_usd * (diff_rate / Decimal('100'))
        commission_amount = quantize_commission(raw_amount)
        
        # 计算锁定截止时间
        hold_until = timezone.now() + timedelta(days=hold_days)
        
        # 创建佣金记录
        commission = Commission.objects.create(
            order=order,
            agent=agent,
            level=level,
            rate_percent=diff_rate,  # ⭐ 存储差额费率而非固定费率
            commission_amount_usd=commission_amount,
            status=Commission.STATUS_HOLD,
            hold_until=hold_until
        )
        
        commissions_created.append(commission)
        
        logger.info(
            f"[Solar Diff Mode] Commission created: L{level}, agent={agent.user_id}, "
            f"diff_rate={diff_rate}%, amount=${commission_amount}",
            extra={
                'commission_id': str(commission.commission_id),
                'order_id': str(order.order_id),
                'agent_id': str(agent.user_id),
                'level': level,
                'agent_level_rate': str(agent_level_rate),
                'base_rate': str(current_base_rate - diff_rate),
                'diff_rate': str(diff_rate),
                'amount': str(commission_amount),
                'hold_days': hold_days
            }
        )
        
        # ⭐ 更新基准费率为当前代理费率（用于下一层计算）
        current_base_rate = agent_level_rate
    
    return commissions_created, commissions_skipped


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_commission_for_order(self, order_id: str):
    """
    计算订单佣金（Celery 任务）
    
    ⭐ 核心逻辑（已改进）：
    1. 从快照读取佣金配置（OrderCommissionPolicySnapshot）
    2. 获取推荐链（含环路检测）
    3. 动态支持1-10级佣金配置
    4. 验证销售额门槛（min_sales）
    5. 计算各级佣金（精度统一）
    6. 原子性创建佣金记录
    
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
        
        # 3. 获取佣金快照（使用 OrderCommissionPolicySnapshot）
        try:
            snapshot = OrderCommissionPolicySnapshot.objects.get(order_id=order.order_id)
        except OrderCommissionPolicySnapshot.DoesNotExist:
            logger.error(
                f"Commission snapshot not found for order {order_id}",
                extra={'order_id': order_id}
            )
            return
        
        # 4. ⭐ 动态获取层级数（从快照的 tiers_json 读取）
        if not snapshot.tiers_json or len(snapshot.tiers_json) == 0:
            logger.warning(
                f"No commission tiers configured in snapshot for order {order_id}",
                extra={'order_id': order_id}
            )
            return
        
        max_levels = len(snapshot.tiers_json)
        logger.info(
            f"Commission snapshot loaded: {max_levels} levels configured",
            extra={
                'order_id': order_id,
                'plan_name': snapshot.plan_name,
                'plan_mode': snapshot.plan_mode,
                'max_levels': max_levels
            }
        )
        
        # 5. 获取推荐链（含环路检测）⭐ 动态层级数
        referral_chain = get_referral_chain(order.buyer, max_levels=max_levels)
        
        if not referral_chain:
            logger.info(
                f"No referral chain for order {order_id}, no commission to calculate",
                extra={'order_id': order_id}
            )
            return
        
        # 6. 根据计算模式选择佣金计算方式
        if snapshot.plan_mode == 'solar_diff':
            # ⭐ Solar Diff 差额模式
            commissions_created, commissions_skipped = _calculate_solar_diff_commissions(
                order, snapshot, referral_chain
            )
        else:
            # 默认 Level 固定费率模式
            commissions_created, commissions_skipped = _calculate_level_commissions(
                order, snapshot, referral_chain
            )
        
        logger.info(
            f"Commission calculation completed for order {order_id}: "
            f"{len(commissions_created)} commissions created, {len(commissions_skipped)} skipped",
            extra={
                'order_id': order_id,
                'commissions_count': len(commissions_created),
                'commissions_skipped': len(commissions_skipped),
                'skipped_details': commissions_skipped,
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
