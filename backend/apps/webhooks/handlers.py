"""
Webhook事件处理器

⭐ Phase D: Stripe Webhook核心逻辑

功能：
- payment_intent.succeeded → 订单paid + 佣金计算
- payment_intent.payment_failed → 订单failed + 库存回补
- charge.dispute.created → 标记争议（未来）

安全特性：
- 双重幂等保障（IdempotencyKey + 状态检查）
- 白名单机制（仅处理允许的事件）
- 状态互斥（防止并发冲突）
- 库存回补边界条件（防双重回补）
"""
import logging
import stripe
from uuid import UUID
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.orders.models import Order
from apps.tiers.services.inventory import release_inventory
from apps.webhooks.utils.idempotency import check_and_mark_processed
from apps.webhooks.utils.audit import log_webhook_event, log_webhook_error

logger = logging.getLogger(__name__)

# ============================================
# Phase D 修正: Stripe事件白名单
# ⭐ 仅处理必要的事件，其他忽略并返回200
# ============================================
ALLOWED_EVENT_TYPES = {
    'payment_intent.succeeded',
    'payment_intent.payment_failed',
    'charge.dispute.created',  # 未来实现
}


def verify_stripe_signature(request):
    """
    验证Stripe Webhook签名
    
    Args:
        request: Django request对象
    
    Returns:
        stripe.Event: 验证后的事件对象
    
    Raises:
        stripe.SignatureVerificationError: 签名验证失败
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        logger.debug(f"Stripe signature verified for event {event.id}")
        return event
    except stripe.SignatureVerificationError as e:
        logger.error(
            f"Stripe signature verification failed: {e}",
            extra={'sig_header': sig_header[:20] if sig_header else None}
        )
        raise


def handle_payment_succeeded(event):
    """
    处理支付成功事件
    
    ⭐ Phase D 修正：
    1. 双重幂等保障（IdempotencyKey + 状态检查）
    2. 原子状态更新（WHERE status='pending'）
    3. 审计日志标准化
    
    Args:
        event: Stripe event对象
    """
    payment_intent_id = event.data.object['id']
    
    try:
        # 查找订单
        order = Order.objects.select_for_update().get(
            stripe_payment_intent_id=payment_intent_id
        )
    except Order.DoesNotExist:
        log_webhook_error(
            event_id=event.id,
            event_type=event.type,
            error_message=f"Order not found for PaymentIntent {payment_intent_id}",
            payment_intent_id=payment_intent_id
        )
        return
    
    # ⭐ 第二层幂等：状态检查（防止paid→paid重复触发）
    if order.status != 'pending':
        logger.warning(
            f"Order {order.order_id} status is {order.status}, "
            f"expected pending. Skip processing.",
            extra={
                'order_id': str(order.order_id),
                'current_status': order.status,
                'expected_status': 'pending',
                'event_id': event.id
            }
        )
        return
    
    # 原子状态更新（使用WHERE条件确保幂等）⭐
    with transaction.atomic():
        updated_count = Order.objects.filter(
            order_id=order.order_id,
            status='pending'  # ⭐ 再次确认状态
        ).update(
            status='paid',
            paid_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        if updated_count == 0:
            logger.warning(
                f"Order {order.order_id} concurrent update detected",
                extra={'order_id': str(order.order_id), 'event_id': event.id}
            )
            return
        
        # 审计日志 ⭐
        log_webhook_event(
            event_id=event.id,
            event_type=event.type,
            action='order_paid',
            order_id=str(order.order_id),
            site_id=str(order.site_id),
            payment_intent_id=payment_intent_id,
            old_status='pending',
            new_status='paid'
        )
        
        # TODO: 触发佣金计算任务（Phase D后续）
        # calculate_commissions.delay(order_id=str(order.order_id))
        
        logger.info(
            f"Order {order.order_id} marked as paid, commission calculation pending",
            extra={'order_id': str(order.order_id)}
        )


def handle_payment_failed(event):
    """
    处理支付失败事件
    
    ⭐ Phase D 修正：
    1. 状态互斥检查（防止与超时取消冲突）
    2. 原子状态更新 + 库存回补
    3. 审计日志标准化
    
    Args:
        event: Stripe event对象
    """
    payment_intent_id = event.data.object['id']
    
    try:
        order = Order.objects.select_for_update().get(
            stripe_payment_intent_id=payment_intent_id
        )
    except Order.DoesNotExist:
        log_webhook_error(
            event_id=event.id,
            event_type=event.type,
            error_message=f"Order not found for PaymentIntent {payment_intent_id}",
            payment_intent_id=payment_intent_id
        )
        return
    
    # ⭐ 边界条件：防止与超时取消冲突（双重回补）
    if order.status != 'pending':
        logger.info(
            f"Order {order.order_id} status is {order.status}, "
            f"skip inventory release (已由其他流程处理)",
            extra={
                'order_id': str(order.order_id),
                'current_status': order.status,
                'event_id': event.id
            }
        )
        return
    
    # 原子状态更新 + 库存回补 ⭐
    with transaction.atomic():
        updated_count = Order.objects.filter(
            order_id=order.order_id,
            status='pending'  # ⭐ 确保互斥
        ).update(
            status='failed',
            updated_at=timezone.now()
        )
        
        if updated_count == 0:
            # 已被其他流程处理（如超时取消）
            logger.info(
                f"Order {order.order_id} already processed by another flow",
                extra={'order_id': str(order.order_id), 'event_id': event.id}
            )
            return
        
        # 回补库存
        # 获取OrderItem
        order_items = order.items.all()
        for item in order_items:
            try:
                release_inventory(item.tier.tier_id, item.quantity)
                logger.info(
                    f"Inventory released for failed payment: tier={item.tier.tier_id}, qty={item.quantity}",
                    extra={
                        'order_id': str(order.order_id),
                        'tier_id': str(item.tier.tier_id),
                        'quantity': item.quantity
                    }
                )
            except Exception as e:
                logger.error(
                    f"Failed to release inventory: {e}",
                    exc_info=True,
                    extra={'order_id': str(order.order_id), 'tier_id': str(item.tier.tier_id)}
                )
        
        # 审计日志 ⭐
        log_webhook_event(
            event_id=event.id,
            event_type=event.type,
            action='order_failed_inventory_released',
            order_id=str(order.order_id),
            site_id=str(order.site_id),
            payment_intent_id=payment_intent_id,
            old_status='pending',
            new_status='failed'
        )


def handle_dispute_created(event):
    """
    处理争议创建事件（Phase D + Phase F 完整实现）
    
    ⚠️ Phase D: 取消未结算佣金
    ⚠️ Phase F: 回冲已结算佣金（Chargeback）
    
    Args:
        event: Stripe event对象
    """
    from apps.agents.services.chargeback import process_chargeback_for_order
    
    charge_id = event.data.object['id']
    payment_intent_id = event.data.object.get('payment_intent')
    
    # 查询订单
    try:
        order = Order.objects.select_related('site').get(
            stripe_payment_intent_id=payment_intent_id
        )
    except Order.DoesNotExist:
        logger.error(
            f"Order not found for payment_intent {payment_intent_id}",
            extra={'event_id': event.id, 'charge_id': charge_id}
        )
        return
    
    # 标记订单为争议
    old_disputed = order.disputed
    if not old_disputed:
        order.disputed = True
        order.save(update_fields=['disputed', 'updated_at'])
    
    logger.warning(
        f"Dispute created for order {order.order_id}",
        extra={
            'event_id': event.id,
            'order_id': str(order.order_id),
            'charge_id': charge_id,
            'payment_intent_id': payment_intent_id
        }
    )
    
    # Phase D: 取消未结算佣金（hold/ready → cancelled）
    cancelled_commissions = Commission.objects.filter(
        order=order,
        status__in=['hold', 'ready']
    ).update(
        status='cancelled',
        updated_at=timezone.now()
    )
    
    logger.info(
        f"Cancelled {cancelled_commissions} pending commissions",
        extra={'order_id': str(order.order_id)}
    )
    
    # ⭐ Phase F: 回冲已结算佣金（Chargeback）
    chargeback_result = process_chargeback_for_order(order)
    
    logger.warning(
        f"Chargeback processed",
        extra={
            'order_id': str(order.order_id),
            'processed': chargeback_result['processed'],
            'total_clawed_back': str(chargeback_result['total_clawed_back']),
            'insufficient_balance': chargeback_result['insufficient_balance_count']
        }
    )
    
    # 审计日志
    log_webhook_event(
        event=event,
        order=order,
        action='dispute_created_chargeback_processed',
        cancelled_commissions=cancelled_commissions,
        chargeback_processed=chargeback_result['processed'],
        chargeback_amount=str(chargeback_result['total_clawed_back'])
    )

