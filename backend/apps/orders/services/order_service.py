"""
订单服务

⭐ 核心功能：
1. 幂等性检查（site_id + idempotency_key）
2. 库存乐观锁
3. 创建Order + OrderItem
4. 创建OrderCommissionPolicySnapshot（Phase B）
5. 创建Stripe PaymentIntent

使用示例：
>>> order, client_secret = create_order(
...     site_id=site.site_id,
...     tier_id=tier_id,
...     quantity=1,
...     wallet_address='0xabc...',
...     referral_code='NA-ABC123',
...     idempotency_key='order-123',
...     user=request.user
... )
"""
import logging
from typing import Tuple, Optional
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)


class OrderServiceError(Exception):
    """订单服务错误基类"""
    pass


class ValidationError(OrderServiceError):
    """验证错误"""
    pass


class InventoryError(OrderServiceError):
    """库存错误"""
    pass


def create_order(
    site_id: uuid.UUID,
    tier_id: uuid.UUID,
    quantity: int,
    wallet_address: str,
    referral_code: Optional[str] = None,
    promo_code: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    user = None
) -> Tuple['Order', str]:
    """
    创建订单（幂等）
    
    ⚠️ 事务内操作：
    1. 幂等性检查
    2. 校验tier和数量
    3. 锁定库存（乐观锁）
    4. 验证 Promo Code（如提供）
    5. 计算金额（含折扣）
    6. 计算代币（含额外奖励）
    7. 创建Order + OrderItem
    8. 记录 Promo Code 使用
    9. 创建OrderCommissionPolicySnapshot
    10. 创建Stripe PaymentIntent
    
    Args:
        site_id: 站点ID
        tier_id: 档位ID
        quantity: 数量
        wallet_address: 买家钱包地址
        referral_code: 推荐码（可选）
        promo_code: 促销码（可选）
        idempotency_key: 幂等键（可选但推荐）
        user: 用户实例（可选）
    
    Returns:
        Tuple[Order, str]: (order, client_secret)
    
    Raises:
        ValidationError: 验证失败
        InventoryError: 库存不足/锁定失败
        OrderServiceError: 其他错误
    
    Examples:
        >>> order, client_secret = create_order(
        ...     site_id=site.site_id,
        ...     tier_id=tier_id,
        ...     quantity=1,
        ...     wallet_address='0xabc...',
        ...     promo_code='SUMMER2025',
        ...     idempotency_key='test-key-123'
        ... )
    """
    from apps.orders.models import Order, OrderItem, PromoCode, PromoCodeUsage
    from apps.tiers.models import Tier
    from apps.users.models import User
    from apps.tiers.services.inventory import lock_inventory
    from apps.orders_snapshots.services import OrderSnapshotService
    from .stripe_service import create_payment_intent, create_mock_payment_intent
    from .promo_service import validate_promo_code
    from apps.users.utils.wallet import normalize_address
    from django.db.models import F
    
    # 1. 幂等性检查
    if idempotency_key:
        existing_order = Order.objects.filter(
            site__site_id=site_id,
            idempotency_key=idempotency_key
        ).first()
        
        if existing_order:
            logger.info(
                f"Idempotent request: returning existing order {existing_order.order_id}",
                extra={
                    'order_id': str(existing_order.order_id),
                    'idempotency_key': idempotency_key
                }
            )
            # 注意：模型中没有stripe_client_secret字段
            # 需要重新生成或从Stripe获取
            # 简化处理：返回空字符串，前端可以重新请求
            return existing_order, ''
    
    # 2. 校验数量
    if quantity < 1:
        raise ValidationError(f"Quantity must be >= 1: {quantity}")
    
    max_quantity = getattr(settings, 'MAX_QUANTITY_PER_ORDER', 1000)
    if quantity > max_quantity:
        raise ValidationError(f"Quantity exceeds maximum: {quantity} > {max_quantity}")
    
    # 3. 标准化钱包地址
    try:
        wallet_address = normalize_address(wallet_address)
    except Exception as e:
        raise ValidationError(f"Invalid wallet address: {e}")
    
    # 4. 查询推荐人（如果提供推荐码）
    referrer_user = None
    if referral_code:
        try:
            referrer_user = User.objects.get(referral_code=referral_code, is_active=True)
        except User.DoesNotExist:
            logger.warning(f"Invalid referral code: {referral_code}")
            # 不阻止订单创建，只是没有推荐人
    
    # 开始事务
    with transaction.atomic():
        # 5. 锁定库存（乐观锁）⭐
        success, error_code = lock_inventory(tier_id, quantity)
        
        if not success:
            logger.warning(
                f"Failed to lock inventory: {error_code}",
                extra={'tier_id': str(tier_id), 'quantity': quantity}
            )
            raise InventoryError(error_code)
        
        # 6. 获取tier信息
        try:
            tier = Tier.objects.get(tier_id=tier_id)
        except Tier.DoesNotExist:
            raise ValidationError(f"Tier not found: {tier_id}")
        
        # 7. 计算金额（改进：支持促销价和 Promo Code）
        # 7.1 获取当前有效价格（促销价或原价）
        unit_price = tier.get_current_price()
        list_price_total = unit_price * quantity
        
        # 7.2 应用 Promo Code（如果提供）
        discount = Decimal('0')
        promo_bonus_tokens = Decimal('0')
        promo_code_instance = None
        
        if promo_code:
            try:
                validation_result = validate_promo_code(
                    code=promo_code,
                    site_id=site_id,
                    user=user,
                    tier=tier,
                    order_amount=list_price_total
                )
                
                if validation_result['valid']:
                    discount = validation_result['discount_amount']
                    promo_bonus_tokens = validation_result['bonus_tokens']
                    promo_code_instance = validation_result['promo']
                    
                    logger.info(
                        f"Promo code applied: {promo_code}",
                        extra={
                            'promo_code': promo_code,
                            'discount': str(discount),
                            'bonus_tokens': str(promo_bonus_tokens)
                        }
                    )
                else:
                    # 验证失败，记录警告但不阻止订单创建
                    logger.warning(
                        f"Promo code validation failed: {promo_code}, error: {validation_result['error']}",
                        extra={
                            'promo_code': promo_code,
                            'error_code': validation_result.get('error_code'),
                            'error': validation_result.get('error')
                        }
                    )
                    # 可选：根据业务需求决定是否抛出异常
                    # raise ValidationError(validation_result['error'])
            except Exception as e:
                logger.error(
                    f"Error validating promo code: {e}",
                    exc_info=True,
                    extra={'promo_code': promo_code}
                )
                # 不阻止订单创建，仅记录错误
        
        final_price = list_price_total - discount
        
        # 确保最终价格不为负
        if final_price < Decimal('0'):
            final_price = Decimal('0')
        
        # 8. 计算代币数量（改进：支持 Tier 赠送和 Promo Code 奖励）
        # 8.1 基础代币
        base_tokens = tier.tokens_per_unit * quantity
        
        # 8.2 Tier 赠送代币
        tier_bonus_tokens = tier.bonus_tokens_per_unit * quantity
        
        # 8.3 Promo Code 额外代币（已在上面计算）
        
        # 8.4 总代币
        total_tokens = base_tokens + tier_bonus_tokens + promo_bonus_tokens
        token_amount = total_tokens
        
        # 9. 计算过期时间
        expire_minutes = getattr(settings, 'ORDER_EXPIRE_MINUTES', 15)
        expires_at = timezone.now() + timedelta(minutes=expire_minutes)
        
        # 10. 创建订单
        order = Order.objects.create(
            site=tier.site,  # 使用ForeignKey
            buyer=user,  # 使用ForeignKey
            referrer=referrer_user,
            wallet_address=wallet_address,
            list_price_usd=list_price_total,
            discount_usd=discount,
            final_price_usd=final_price,
            status='pending',
            idempotency_key=idempotency_key,
            expires_at=expires_at
        )
        
        # 11. 创建OrderItem
        OrderItem.objects.create(
            order=order,
            tier=tier,
            quantity=quantity,
            unit_price_usd=unit_price,
            token_amount=token_amount
        )
        
        # 11.5 记录 Promo Code 使用（如果应用了）⭐
        if promo_code_instance:
            try:
                PromoCodeUsage.objects.create(
                    promo_code=promo_code_instance,
                    order=order,
                    user=user,
                    discount_applied=discount,
                    bonus_tokens_applied=promo_bonus_tokens
                )
                
                # 更新促销码使用次数（使用 F 表达式避免竞态条件）
                PromoCode.objects.filter(promo_id=promo_code_instance.promo_id).update(
                    current_uses=F('current_uses') + 1
                )
                
                logger.info(
                    f"Promo code usage recorded: {promo_code}",
                    extra={
                        'promo_code': promo_code,
                        'order_id': str(order.order_id),
                        'user_id': str(user.user_id)
                    }
                )
            except Exception as e:
                logger.error(
                    f"Failed to record promo code usage: {e}",
                    exc_info=True,
                    extra={
                        'promo_code': promo_code,
                        'order_id': str(order.order_id)
                    }
                )
                # 记录失败应回滚整个事务
                raise OrderServiceError(f"Failed to record promo code usage: {e}") from e
        
        # 12. 创建佣金快照（Phase B模型）⭐
        try:
            OrderSnapshotService.create_snapshot_for_order(
                order_id=order.order_id,
                site_id=site_id
            )
            logger.info(
                f"Created commission snapshot for order {order.order_id}",
                extra={'order_id': str(order.order_id)}
            )
        except Exception as e:
            logger.error(
                f"Failed to create commission snapshot: {e}",
                exc_info=True,
                extra={'order_id': str(order.order_id)}
            )
            # 快照创建失败应回滚整个事务
            raise OrderServiceError(f"Failed to create commission snapshot: {e}") from e
        
        # 13. 创建Stripe PaymentIntent（或Mock）
        mock_stripe = getattr(settings, 'MOCK_STRIPE', False)
        
        try:
            if mock_stripe:
                # Mock模式（开发测试）
                client_secret = create_mock_payment_intent(order.order_id, final_price)
                payment_intent_id = f"pi_mock_{order.order_id}"
            else:
                # 真实Stripe
                intent = create_payment_intent(
                    amount=final_price,
                    metadata={
                        'order_id': str(order.order_id),
                        'site_id': str(site_id),
                        'tier_id': str(tier_id)
                    },
                    idempotency_key=idempotency_key
                )
                client_secret = intent.client_secret
                payment_intent_id = intent.id
            
            # 更新订单（Stripe信息）
            order.stripe_payment_intent_id = payment_intent_id
            # 注意：模型中缺少stripe_client_secret字段
            # 暂时存储到metadata或直接返回，不保存到DB
            order.save(update_fields=['stripe_payment_intent_id'])
            
        except Exception as e:
            logger.error(
                f"Failed to create PaymentIntent: {e}",
                exc_info=True,
                extra={'order_id': str(order.order_id)}
            )
            # PaymentIntent创建失败应回滚整个事务
            raise OrderServiceError(f"Failed to create payment: {e}") from e
    
    # 事务成功提交
    logger.info(
        f"Order created successfully: {order.order_id}, amount={final_price}",
        extra={
            'order_id': str(order.order_id),
            'tier_id': str(tier_id),
            'quantity': quantity,
            'final_price': str(final_price),
            'idempotency_key': idempotency_key
        }
    )
    
    return order, client_secret


def cancel_order(order_id: uuid.UUID, reason: str = 'USER_CANCELLED') -> 'Order':
    """
    取消订单
    
    ⚠️ 仅 pending 状态可取消
    ⚠️ 自动回补库存
    
    Args:
        order_id: 订单ID
        reason: 取消原因
    
    Returns:
        Order: 已取消的订单
    
    Raises:
        ValidationError: 订单状态不允许取消
        OrderServiceError: 取消失败
    """
    from apps.orders.models import Order
    from apps.tiers.services.inventory import release_inventory
    
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        raise ValidationError(f"Order not found: {order_id}")
    
    # 检查状态
    if order.status != 'pending':
        raise ValidationError(
            f"Cannot cancel order in status: {order.status}. Only pending orders can be cancelled."
        )
    
    with transaction.atomic():
        # 更新订单状态
        order.status = 'cancelled'
        order.cancelled_reason = reason
        order.cancelled_at = timezone.now()
        order.save(update_fields=['status', 'cancelled_reason', 'cancelled_at'])
        
        # 回补库存
        # 获取订单明细中的tier_id和quantity
        order_item = order.items.first()
        if order_item:
            success, error_code = release_inventory(order_item.tier.tier_id, order_item.quantity)
        
        if not success:
            logger.error(
                f"Failed to release inventory when cancelling order: {error_code}",
                extra={'order_id': str(order_id)}
            )
            # 库存回补失败应该告警，但不阻止取消
            # 可以后续通过定时任务修复
        else:
            logger.info(
                f"Released inventory: tier_id={order.tier_id}, quantity={order.quantity}",
                extra={'order_id': str(order_id)}
            )
    
    logger.info(
        f"Order cancelled: {order_id}, reason={reason}",
        extra={'order_id': str(order_id), 'reason': reason}
        )
    
    return order


def get_order_summary(order_id: uuid.UUID) -> dict:
    """
    获取订单摘要
    
    Args:
        order_id: 订单ID
    
    Returns:
        dict: 订单摘要信息
    """
    from apps.orders.models import Order
    
    try:
        order = Order.objects.select_related('tier', 'buyer_user', 'referrer').get(order_id=order_id)
    except Order.DoesNotExist:
        return None
    
    return {
        'order_id': str(order.order_id),
        'status': order.status,
        'tier_name': order.tier.name if order.tier else None,
        'quantity': order.quantity,
        'total_amount': str(order.total_amount),
        'buyer_address': order.buyer_address,
        'referrer_code': order.referrer.referral_code if order.referrer else None,
        'created_at': order.created_at.isoformat(),
        'expires_at': order.expires_at.isoformat() if order.expires_at else None
    }

