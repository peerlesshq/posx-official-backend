"""
Promo Code 验证服务

⭐ 核心功能：
1. 验证 Promo Code 有效性
2. 计算折扣金额
3. 计算额外代币奖励
4. 检查使用限制

使用示例：
>>> result = validate_promo_code(
...     code='SUMMER2025',
...     site_id=site.site_id,
...     user=request.user,
...     tier=tier,
...     order_amount=Decimal('100.00')
... )
>>> if result['valid']:
...     discount = result['discount_amount']
...     bonus = result['bonus_tokens']
"""
import logging
from typing import Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db.models import Q
import uuid

logger = logging.getLogger(__name__)


class PromoCodeError(Exception):
    """Promo Code 错误基类"""
    pass


class PromoCodeNotFoundError(PromoCodeError):
    """Promo Code 不存在"""
    pass


class PromoCodeExpiredError(PromoCodeError):
    """Promo Code 已过期"""
    pass


class PromoCodeExhaustedError(PromoCodeError):
    """Promo Code 使用次数已用完"""
    pass


class PromoCodeNotApplicableError(PromoCodeError):
    """Promo Code 不适用"""
    pass


def quantize_amount(amount: Decimal) -> Decimal:
    """
    量化金额到2位小数
    
    ⭐ 统一精度策略（与佣金计算保持一致）
    - 使用 ROUND_HALF_UP（银行家舍入）
    """
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def quantize_tokens(tokens: Decimal) -> Decimal:
    """
    量化代币到6位小数
    """
    return tokens.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def validate_promo_code(
    code: str,
    site_id: uuid.UUID,
    user,
    tier,
    order_amount: Decimal
) -> Dict:
    """
    验证 Promo Code
    
    Args:
        code: 促销码
        site_id: 站点ID
        user: 用户实例
        tier: Tier 实例
        order_amount: 订单金额（应用折扣前）
    
    Returns:
        Dict: {
            'valid': bool,
            'promo': PromoCode instance (if valid),
            'discount_amount': Decimal,
            'bonus_tokens': Decimal,
            'error': str (if not valid),
            'error_code': str (if not valid)
        }
    
    Raises:
        PromoCodeError: 验证失败时抛出具体异常
    """
    from apps.orders.models import PromoCode, PromoCodeUsage
    
    # 统一code为大写
    code = code.upper().strip()
    
    # 1. 检查代码是否存在
    try:
        promo = PromoCode.objects.select_related('site').prefetch_related('applicable_tiers').get(
            code=code
        )
    except PromoCode.DoesNotExist:
        logger.warning(
            f"Promo code not found: {code}",
            extra={'code': code, 'site_id': str(site_id)}
        )
        return {
            'valid': False,
            'error': f'促销码不存在: {code}',
            'error_code': 'PROMO_CODE_NOT_FOUND',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 2. 检查站点匹配
    if promo.site.site_id != site_id:
        logger.warning(
            f"Promo code site mismatch: {code}",
            extra={
                'code': code,
                'promo_site_id': str(promo.site.site_id),
                'request_site_id': str(site_id)
            }
        )
        return {
            'valid': False,
            'error': '促销码不适用于当前站点',
            'error_code': 'PROMO_CODE_SITE_MISMATCH',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 3. 检查激活状态
    if not promo.is_active:
        logger.warning(
            f"Promo code inactive: {code}",
            extra={'code': code}
        )
        return {
            'valid': False,
            'error': '促销码已停用',
            'error_code': 'PROMO_CODE_INACTIVE',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 4. 检查有效期
    now = timezone.now()
    if now < promo.valid_from:
        logger.warning(
            f"Promo code not yet valid: {code}",
            extra={'code': code, 'valid_from': promo.valid_from.isoformat()}
        )
        return {
            'valid': False,
            'error': f'促销码尚未生效，生效时间：{promo.valid_from.strftime("%Y-%m-%d %H:%M")}',
            'error_code': 'PROMO_CODE_NOT_YET_VALID',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    if now > promo.valid_until:
        logger.warning(
            f"Promo code expired: {code}",
            extra={'code': code, 'valid_until': promo.valid_until.isoformat()}
        )
        return {
            'valid': False,
            'error': f'促销码已过期，截止时间：{promo.valid_until.strftime("%Y-%m-%d %H:%M")}',
            'error_code': 'PROMO_CODE_EXPIRED',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 5. 检查总使用次数限制
    if promo.max_uses is not None and promo.current_uses >= promo.max_uses:
        logger.warning(
            f"Promo code exhausted: {code}",
            extra={'code': code, 'current_uses': promo.current_uses, 'max_uses': promo.max_uses}
        )
        return {
            'valid': False,
            'error': '促销码使用次数已达上限',
            'error_code': 'PROMO_CODE_EXHAUSTED',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 6. 检查用户使用次数限制
    user_usage_count = PromoCodeUsage.objects.filter(
        promo_code=promo,
        user=user
    ).count()
    
    if user_usage_count >= promo.uses_per_user:
        logger.warning(
            f"User exceeded promo code usage limit: {code}",
            extra={
                'code': code,
                'user_id': str(user.user_id),
                'user_usage_count': user_usage_count,
                'uses_per_user': promo.uses_per_user
            }
        )
        return {
            'valid': False,
            'error': f'您已达到该促销码的最大使用次数（{promo.uses_per_user}次）',
            'error_code': 'PROMO_CODE_USER_LIMIT_EXCEEDED',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 7. 检查最低订单金额
    if order_amount < promo.min_order_amount:
        logger.warning(
            f"Order amount below minimum: {code}",
            extra={
                'code': code,
                'order_amount': str(order_amount),
                'min_order_amount': str(promo.min_order_amount)
            }
        )
        return {
            'valid': False,
            'error': f'订单金额不满足最低要求（最低 ${promo.min_order_amount}）',
            'error_code': 'PROMO_CODE_MIN_AMOUNT_NOT_MET',
            'promo': None,
            'discount_amount': Decimal('0'),
            'bonus_tokens': Decimal('0'),
        }
    
    # 8. 检查适用 Tier
    applicable_tiers = promo.applicable_tiers.all()
    if applicable_tiers.exists():
        # 如果配置了适用 Tier，则必须匹配
        if tier not in applicable_tiers:
            logger.warning(
                f"Promo code not applicable to tier: {code}",
                extra={
                    'code': code,
                    'tier_id': str(tier.tier_id),
                    'tier_name': tier.name
                }
            )
            return {
                'valid': False,
                'error': '促销码不适用于当前产品',
                'error_code': 'PROMO_CODE_TIER_NOT_APPLICABLE',
                'promo': None,
                'discount_amount': Decimal('0'),
                'bonus_tokens': Decimal('0'),
            }
    
    # 9. 计算折扣金额和额外代币
    discount_amount = Decimal('0')
    bonus_tokens = Decimal('0')
    
    if promo.discount_type == PromoCode.DISCOUNT_TYPE_PERCENTAGE:
        # 百分比折扣
        raw_discount = order_amount * (promo.discount_value / Decimal('100'))
        discount_amount = quantize_amount(raw_discount)
        
    elif promo.discount_type == PromoCode.DISCOUNT_TYPE_FIXED:
        # 固定金额折扣
        discount_amount = quantize_amount(promo.discount_value)
        # 确保折扣不超过订单金额
        if discount_amount > order_amount:
            discount_amount = order_amount
    
    elif promo.discount_type == PromoCode.DISCOUNT_TYPE_BONUS_TOKENS:
        # 仅额外代币
        bonus_tokens = quantize_tokens(promo.bonus_tokens_value)
    
    elif promo.discount_type == PromoCode.DISCOUNT_TYPE_COMBO:
        # 组合优惠
        if promo.discount_value > 0:
            # 百分比折扣
            raw_discount = order_amount * (promo.discount_value / Decimal('100'))
            discount_amount = quantize_amount(raw_discount)
        
        if promo.bonus_tokens_value > 0:
            bonus_tokens = quantize_tokens(promo.bonus_tokens_value)
    
    logger.info(
        f"Promo code validated successfully: {code}",
        extra={
            'code': code,
            'user_id': str(user.user_id),
            'tier_id': str(tier.tier_id),
            'order_amount': str(order_amount),
            'discount_amount': str(discount_amount),
            'bonus_tokens': str(bonus_tokens)
        }
    )
    
    return {
        'valid': True,
        'promo': promo,
        'discount_amount': discount_amount,
        'bonus_tokens': bonus_tokens,
        'error': None,
        'error_code': None,
    }


def get_promo_code_summary(promo) -> Dict:
    """
    获取 Promo Code 摘要信息（用于前端展示）
    
    Args:
        promo: PromoCode 实例
    
    Returns:
        Dict: 格式化的摘要信息
    """
    discount_description = ""
    
    if promo.discount_type == promo.DISCOUNT_TYPE_PERCENTAGE:
        discount_description = f"{promo.discount_value}% 折扣"
    elif promo.discount_type == promo.DISCOUNT_TYPE_FIXED:
        discount_description = f"${promo.discount_value} 折扣"
    elif promo.discount_type == promo.DISCOUNT_TYPE_BONUS_TOKENS:
        discount_description = f"+{promo.bonus_tokens_value} 代币"
    elif promo.discount_type == promo.DISCOUNT_TYPE_COMBO:
        parts = []
        if promo.discount_value > 0:
            parts.append(f"{promo.discount_value}% 折扣")
        if promo.bonus_tokens_value > 0:
            parts.append(f"+{promo.bonus_tokens_value} 代币")
        discount_description = " + ".join(parts)
    
    now = timezone.now()
    is_valid = promo.is_active and promo.valid_from <= now <= promo.valid_until
    
    uses_remaining = None
    if promo.max_uses is not None:
        uses_remaining = max(0, promo.max_uses - promo.current_uses)
    
    return {
        'code': promo.code,
        'name': promo.name,
        'description': promo.description,
        'discount_description': discount_description,
        'is_valid': is_valid,
        'valid_from': promo.valid_from.isoformat(),
        'valid_until': promo.valid_until.isoformat(),
        'min_order_amount': str(promo.min_order_amount),
        'uses_remaining': uses_remaining,
        'uses_per_user': promo.uses_per_user,
    }

