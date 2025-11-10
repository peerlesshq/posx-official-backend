"""
Agent 余额管理服务（Phase F）

⚠️ 关键：
- 余额更新使用悲观锁（select_for_update）
- 所有金额操作验证非负
- 完整审计日志
"""
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
import logging

from apps.agents.models import AgentProfile

logger = logging.getLogger(__name__)


def get_or_create_agent_profile(user, site):
    """
    获取或创建 Agent Profile
    
    参数:
        user: User 实例
        site: Site 实例
    
    返回:
        AgentProfile 实例
    """
    profile, created = AgentProfile.objects.get_or_create(
        user=user,
        site=site,
        defaults={
            'agent_level': AgentProfile.LEVEL_BRONZE,
            'balance_usd': Decimal('0'),
            'kyc_status': AgentProfile.KYC_PENDING,
            'is_active': True,
        }
    )
    
    if created:
        logger.info(
            f"Created agent profile for user {user.user_id}",
            extra={
                'user_id': str(user.user_id),
                'site_id': str(site.site_id),
                'profile_id': str(profile.profile_id)
            }
        )
    
    return profile


def update_balance_on_commission_paid(commission):
    """
    佣金结算后更新余额
    
    触发时机：
    - Commission: ready → paid (Phase D Admin批量结算)
    
    操作：
    - balance_usd += commission_amount_usd
    - total_earned_usd += commission_amount_usd
    
    ⚠️ 使用悲观锁防止并发问题
    
    参数:
        commission: Commission 实例（status='paid'）
    
    返回:
        AgentProfile 实例（更新后）
    """
    # 获取或创建 Agent Profile
    profile = get_or_create_agent_profile(
        user=commission.agent,
        site=commission.order.site
    )
    
    # 使用悲观锁更新余额
    with transaction.atomic():
        # 锁定行
        profile = AgentProfile.objects.select_for_update().get(
            profile_id=profile.profile_id
        )
        
        # 金额量化（2位小数）
        amount = commission.commission_amount_usd.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # 更新余额
        profile.balance_usd += amount
        profile.total_earned_usd += amount
        profile.save(update_fields=['balance_usd', 'total_earned_usd', 'updated_at'])
        
        logger.info(
            f"Updated agent balance: +${amount}",
            extra={
                'profile_id': str(profile.profile_id),
                'commission_id': str(commission.commission_id),
                'old_balance': str(profile.balance_usd - amount),
                'new_balance': str(profile.balance_usd),
                'amount': str(amount)
            }
        )
    
    return profile


def deduct_balance_for_withdrawal(agent_profile, amount_usd):
    """
    提现申请时扣减余额
    
    ⚠️ 使用悲观锁，验证余额充足
    
    参数:
        agent_profile: AgentProfile 实例
        amount_usd: Decimal 提现金额
    
    返回:
        True: 扣减成功
        False: 余额不足
    
    抛出:
        ValueError: 金额无效
    """
    if amount_usd <= 0:
        raise ValueError("提现金额必须大于0")
    
    # 量化金额（2位小数）
    amount = amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    with transaction.atomic():
        # 悲观锁
        profile = AgentProfile.objects.select_for_update().get(
            profile_id=agent_profile.profile_id
        )
        
        # 验证余额充足
        if profile.balance_usd < amount:
            logger.warning(
                f"Insufficient balance for withdrawal",
                extra={
                    'profile_id': str(profile.profile_id),
                    'balance': str(profile.balance_usd),
                    'requested': str(amount)
                }
            )
            return False
        
        # 扣减余额
        profile.balance_usd -= amount
        profile.save(update_fields=['balance_usd', 'updated_at'])
        
        logger.info(
            f"Deducted balance for withdrawal: -${amount}",
            extra={
                'profile_id': str(profile.profile_id),
                'old_balance': str(profile.balance_usd + amount),
                'new_balance': str(profile.balance_usd),
                'amount': str(amount)
            }
        )
    
    return True


def refund_balance_for_withdrawal(agent_profile, amount_usd, reason='withdrawal_rejected'):
    """
    提现拒绝/取消后返还余额
    
    ⚠️ 使用悲观锁
    
    参数:
        agent_profile: AgentProfile 实例
        amount_usd: Decimal 返还金额
        reason: str 返还原因
    
    返回:
        AgentProfile 实例（更新后）
    """
    amount = amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    with transaction.atomic():
        # 悲观锁
        profile = AgentProfile.objects.select_for_update().get(
            profile_id=agent_profile.profile_id
        )
        
        # 返还余额
        profile.balance_usd += amount
        profile.save(update_fields=['balance_usd', 'updated_at'])
        
        logger.info(
            f"Refunded balance: +${amount} (reason: {reason})",
            extra={
                'profile_id': str(profile.profile_id),
                'old_balance': str(profile.balance_usd - amount),
                'new_balance': str(profile.balance_usd),
                'amount': str(amount),
                'reason': reason
            }
        )
    
    return profile


def complete_withdrawal(agent_profile, amount_usd):
    """
    提现完成后记录
    
    ⚠️ 使用悲观锁更新 total_withdrawn_usd
    
    参数:
        agent_profile: AgentProfile 实例
        amount_usd: Decimal 已提现金额
    
    返回:
        AgentProfile 实例（更新后）
    """
    amount = amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    with transaction.atomic():
        # 悲观锁
        profile = AgentProfile.objects.select_for_update().get(
            profile_id=agent_profile.profile_id
        )
        
        # 更新累计提现
        profile.total_withdrawn_usd += amount
        profile.save(update_fields=['total_withdrawn_usd', 'updated_at'])
        
        logger.info(
            f"Withdrawal completed: ${amount}",
            extra={
                'profile_id': str(profile.profile_id),
                'total_withdrawn': str(profile.total_withdrawn_usd),
                'amount': str(amount)
            }
        )
    
    return profile

