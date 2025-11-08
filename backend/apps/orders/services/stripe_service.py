"""
Stripe 支付服务

⭐ 功能：
- 创建 PaymentIntent
- 确认支付
- 取消支付
- Mock 模式（开发测试）

使用示例：
>>> if settings.MOCK_STRIPE:
...     client_secret = create_mock_payment_intent(order_id, amount)
... else:
...     intent = create_payment_intent(amount, metadata, idempotency_key)
...     client_secret = intent.client_secret
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)

# 尝试导入 Stripe
try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("stripe library not installed")


class StripeError(Exception):
    """Stripe 操作错误"""
    pass


def create_payment_intent(
    amount: Decimal,
    metadata: Optional[Dict[str, str]] = None,
    idempotency_key: Optional[str] = None
) -> Any:
    """
    创建 Stripe PaymentIntent
    
    ⚠️ 金额转换：使用 to_cents() 确保精度
    ⚠️ 幂等性：透传 idempotency_key 给 Stripe
    
    Args:
        amount: 金额（Decimal，USD）
        metadata: 元数据（如 order_id）
        idempotency_key: 幂等键（可选但推荐）
    
    Returns:
        PaymentIntent 对象
    
    Raises:
        StripeError: 创建失败
    
    Examples:
        >>> intent = create_payment_intent(
        ...     amount=Decimal('100.50'),
        ...     metadata={'order_id': str(order_id)},
        ...     idempotency_key='order-123'
        ... )
        >>> client_secret = intent.client_secret
    """
    if not STRIPE_AVAILABLE:
        raise StripeError("Stripe library not available")
    
    from apps.core.utils.money import to_cents
    
    # 转换为分
    amount_cents = to_cents(amount)
    
    # 构造请求参数
    params = {
        'amount': amount_cents,
        'currency': 'usd',
        'metadata': metadata or {},
        'automatic_payment_methods': {
            'enabled': True,
        },
    }
    
    # 幂等键（透传给Stripe）
    if idempotency_key:
        params['idempotency_key'] = idempotency_key
    
    try:
        intent = stripe.PaymentIntent.create(**params)
        
        logger.info(
            f"Created PaymentIntent: {intent.id}, amount={amount}",
            extra={
                'payment_intent_id': intent.id,
                'amount': str(amount),
                'amount_cents': amount_cents
            }
        )
        
        return intent
        
    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe API error: {e}",
            exc_info=True,
            extra={'amount': str(amount)}
        )
        raise StripeError(f"Failed to create PaymentIntent: {e}") from e


def confirm_payment_intent(payment_intent_id: str) -> Any:
    """
    确认 PaymentIntent
    
    Args:
        payment_intent_id: PaymentIntent ID
    
    Returns:
        PaymentIntent 对象
    
    Raises:
        StripeError: 确认失败
    """
    if not STRIPE_AVAILABLE:
        raise StripeError("Stripe library not available")
    
    try:
        intent = stripe.PaymentIntent.confirm(payment_intent_id)
        
        logger.info(
            f"Confirmed PaymentIntent: {intent.id}",
            extra={'payment_intent_id': intent.id}
        )
        
        return intent
        
    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe API error: {e}",
            exc_info=True,
            extra={'payment_intent_id': payment_intent_id}
        )
        raise StripeError(f"Failed to confirm PaymentIntent: {e}") from e


def cancel_payment_intent(payment_intent_id: str) -> Any:
    """
    取消 PaymentIntent
    
    Args:
        payment_intent_id: PaymentIntent ID
    
    Returns:
        PaymentIntent 对象
    
    Raises:
        StripeError: 取消失败
    """
    if not STRIPE_AVAILABLE:
        raise StripeError("Stripe library not available")
    
    try:
        intent = stripe.PaymentIntent.cancel(payment_intent_id)
        
        logger.info(
            f"Cancelled PaymentIntent: {intent.id}",
            extra={'payment_intent_id': intent.id}
        )
        
        return intent
        
    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe API error: {e}",
            exc_info=True,
            extra={'payment_intent_id': payment_intent_id}
        )
        raise StripeError(f"Failed to cancel PaymentIntent: {e}") from e


def create_mock_payment_intent(order_id: uuid.UUID, amount: Decimal) -> str:
    """
    创建 Mock PaymentIntent（开发测试用）
    
    ⚠️ 仅在 MOCK_STRIPE=true 时使用
    
    Args:
        order_id: 订单ID
        amount: 金额
    
    Returns:
        str: Mock client_secret
    
    Examples:
        >>> if settings.MOCK_STRIPE:
        ...     client_secret = create_mock_payment_intent(order_id, amount)
        ...     # 'pi_mock_{order_id}_secret_{random}'
    """
    import secrets
    
    # 生成假的 client_secret
    client_secret = f"pi_mock_{order_id}_secret_{secrets.token_urlsafe(16)}"
    
    logger.info(
        f"Created MOCK PaymentIntent for order {order_id}, amount={amount}",
        extra={
            'order_id': str(order_id),
            'amount': str(amount),
            'mock': True
        }
    )
    
    return client_secret


def get_payment_intent(payment_intent_id: str) -> Any:
    """
    获取 PaymentIntent 详情
    
    Args:
        payment_intent_id: PaymentIntent ID
    
    Returns:
        PaymentIntent 对象
    
    Raises:
        StripeError: 获取失败
    """
    if not STRIPE_AVAILABLE:
        raise StripeError("Stripe library not available")
    
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent
    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe API error: {e}",
            exc_info=True,
            extra={'payment_intent_id': payment_intent_id}
        )
        raise StripeError(f"Failed to retrieve PaymentIntent: {e}") from e


