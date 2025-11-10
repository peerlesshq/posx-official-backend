"""
Chargeback 处理服务（Phase F 补充）

⚠️ 业务规则：
- 虽然业务禁止退款，但 Stripe chargeback 仍可能发生
- 需要回冲已结算的佣金
- 如果 Agent 余额不足，记录欠款

流程：
1. Stripe dispute 触发 charge.dispute.created
2. 查询该订单的所有已结算佣金（status='paid'）
3. 扣减 Agent 余额（悲观锁）
4. 如余额不足，创建负余额记录（TODO: 或欠款记录）
"""
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
import logging

from apps.agents.models import AgentProfile
from apps.commissions.models import Commission

logger = logging.getLogger(__name__)


def process_chargeback_for_order(order):
    """
    处理订单 Chargeback（回冲佣金）
    
    触发时机：
    - Stripe charge.dispute.created
    - 订单 disputed=True
    
    逻辑：
    1. 查询该订单的所有已结算佣金（status='paid'）
    2. 逐条扣减 Agent 余额
    3. 创建负向佣金记录（用于审计）
    4. 如余额不足，记录告警（允许负余额或记欠款）
    
    参数:
        order: Order 实例（disputed=True）
    
    返回:
        {
            'processed': 5,  # 处理条数
            'total_clawed_back': Decimal('16.00'),
            'insufficient_balance_count': 0
        }
    """
    # 查询已结算佣金
    paid_commissions = Commission.objects.filter(
        order=order,
        status='paid'
    ).select_related('agent', 'order__site')
    
    if not paid_commissions.exists():
        logger.info(
            f"No paid commissions to chargeback for order {order.order_id}"
        )
        return {
            'processed': 0,
            'total_clawed_back': Decimal('0'),
            'insufficient_balance_count': 0
        }
    
    processed_count = 0
    total_amount = Decimal('0')
    insufficient_count = 0
    
    for commission in paid_commissions:
        try:
            # 扣减余额
            result = deduct_balance_for_chargeback(
                commission.agent,
                commission.order.site,
                commission.commission_amount_usd,
                commission
            )
            
            if result['success']:
                processed_count += 1
                total_amount += commission.commission_amount_usd
            else:
                insufficient_count += 1
                logger.warning(
                    f"Insufficient balance for chargeback",
                    extra={
                        'commission_id': str(commission.commission_id),
                        'agent_id': str(commission.agent.user_id),
                        'amount': str(commission.commission_amount_usd),
                        'current_balance': str(result['current_balance'])
                    }
                )
        
        except Exception as e:
            logger.error(
                f"Failed to process chargeback for commission {commission.commission_id}: {e}",
                exc_info=True
            )
    
    logger.info(
        f"Chargeback processed for order {order.order_id}",
        extra={
            'order_id': str(order.order_id),
            'processed': processed_count,
            'total_clawed_back': str(total_amount),
            'insufficient_balance': insufficient_count
        }
    )
    
    return {
        'processed': processed_count,
        'total_clawed_back': total_amount,
        'insufficient_balance_count': insufficient_count
    }


def deduct_balance_for_chargeback(user, site, amount_usd, commission):
    """
    扣减余额（Chargeback）
    
    ⚠️ 与提现扣减的区别：
    - 允许余额为负（记录欠款）
    - 创建负向佣金记录（审计）
    
    参数:
        user: User 实例（Agent）
        site: Site 实例
        amount_usd: Decimal 扣减金额
        commission: Commission 实例（原佣金记录）
    
    返回:
        {
            'success': True/False,
            'current_balance': Decimal,
            'new_balance': Decimal
        }
    """
    from apps.agents.services.balance import get_or_create_agent_profile
    
    # 获取 Profile
    profile = get_or_create_agent_profile(user, site)
    
    # 金额量化
    amount = amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    with transaction.atomic():
        # 悲观锁
        profile = AgentProfile.objects.select_for_update().get(
            profile_id=profile.profile_id
        )
        
        old_balance = profile.balance_usd
        
        # 扣减余额（允许为负）⭐
        profile.balance_usd -= amount
        
        # 记录是否余额不足
        insufficient = old_balance < amount
        
        profile.save(update_fields=['balance_usd', 'updated_at'])
        
        logger.warning(
            f"Chargeback deducted balance: -${amount}",
            extra={
                'profile_id': str(profile.profile_id),
                'commission_id': str(commission.commission_id),
                'old_balance': str(old_balance),
                'new_balance': str(profile.balance_usd),
                'amount': str(amount),
                'insufficient': insufficient
            }
        )
        
        # TODO: 创建负向佣金记录（用于审计）
        # NegativeCommission.objects.create(
        #     original_commission=commission,
        #     amount=-amount,
        #     reason='chargeback'
        # )
    
    return {
        'success': True,
        'current_balance': old_balance,
        'new_balance': profile.balance_usd,
        'insufficient': insufficient
    }

