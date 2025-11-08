"""
Stripe Webhook 处理视图

⭐ Phase D 核心功能：
- 签名验证（400失败/200成功）
- 事件白名单机制
- 双重幂等保障（IdempotencyKey + 状态检查）
- 审计日志标准化
- 统一返回码策略
"""
import logging
import stripe
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from sentry_sdk import capture_exception

from apps.orders.models import Order
from apps.webhooks.models import IdempotencyKey
from apps.webhooks.utils.audit import log_webhook_event

logger = logging.getLogger(__name__)

# ============================================
# Stripe 事件白名单
# ⭐ Phase D P0: 明确允许的事件类型
# ============================================
ALLOWED_EVENT_TYPES = {
    'payment_intent.succeeded',
    'payment_intent.payment_failed',
    'charge.dispute.created',
}

stripe.api_key = settings.STRIPE_SECRET_KEY


def check_and_mark_processed(event_id: str, source: str = 'stripe') -> bool:
    """
    检查事件是否已处理（双重幂等第一层）
    
    Args:
        event_id: Stripe事件ID
        source: 事件来源
        
    Returns:
        bool: True表示已处理过，False表示首次处理
    """
    try:
        # 尝试创建幂等键
        IdempotencyKey.objects.create(
            key=event_id,
            source=source,
            processed_at=timezone.now()
        )
        return False  # 首次处理
    except Exception:
        # 键已存在，说明已处理过
        return True


def handle_payment_succeeded(event):
    """
    处理支付成功事件
    
    ⭐ Phase D P0: 双重幂等保障
    1. IdempotencyKey检查（已在外层）
    2. 订单状态检查（pending → paid 互斥）
    """
    payment_intent_id = event.data.object.id
    
    try:
        order = Order.objects.select_for_update().get(
            stripe_payment_intent_id=payment_intent_id
        )
    except Order.DoesNotExist:
        logger.warning(
            f"Order not found for PaymentIntent {payment_intent_id}",
            extra={
                'event_id': event.id,
                'payment_intent_id': payment_intent_id,
                'event_type': event.type
            }
        )
        return
    
    old_status = order.status
    
    # ⭐ 双重幂等第二层：状态检查
    if order.status != Order.STATUS_PENDING:
        log_webhook_event(
            event=event,
            order=order,
            action='payment_succeeded_skip',
            old_status=old_status,
            new_status=order.status,
            reason=f'Order status is {order.status}, not pending'
        )
        return
    
    # ⭐ 原子更新状态（防并发）
    with transaction.atomic():
        updated_count = Order.objects.filter(
            order_id=order.order_id,
            status=Order.STATUS_PENDING  # ⭐ 再次确认
        ).update(
            status=Order.STATUS_PAID,
            paid_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        if updated_count == 0:
            logger.warning(
                f"Order {order.order_id} concurrent update detected",
                extra={
                    'order_id': str(order.order_id),
                    'event_id': event.id
                }
            )
            return
        
        # 触发佣金计算任务
        from apps.commissions.tasks import calculate_commission_for_order
        calculate_commission_for_order.delay(str(order.order_id))
        
        log_webhook_event(
            event=event,
            order=order,
            action='payment_succeeded',
            old_status=old_status,
            new_status='paid'
        )


def handle_payment_failed(event):
    """
    处理支付失败事件
    
    ⭐ Phase D P0: 防止双重库存回补
    - 状态互斥检查（pending → failed）
    - 与超时取消任务互斥
    """
    payment_intent_id = event.data.object.id
    
    try:
        order = Order.objects.select_for_update().get(
            stripe_payment_intent_id=payment_intent_id
        )
    except Order.DoesNotExist:
        logger.warning(
            f"Order not found for PaymentIntent {payment_intent_id}",
            extra={'event_id': event.id, 'payment_intent_id': payment_intent_id}
        )
        return
    
    old_status = order.status
    
    # ⭐ 状态检查（防双重回补）
    if order.status != Order.STATUS_PENDING:
        log_webhook_event(
            event=event,
            order=order,
            action='payment_failed_skip',
            old_status=old_status,
            new_status=order.status,
            reason=f'Order status is {order.status}, skip inventory release'
        )
        return
    
    # ⭐ 原子更新状态
    with transaction.atomic():
        updated_count = Order.objects.filter(
            order_id=order.order_id,
            status=Order.STATUS_PENDING
        ).update(
            status=Order.STATUS_FAILED,
            updated_at=timezone.now()
        )
        
        if updated_count == 0:
            logger.warning(
                f"Order {order.order_id} concurrent update, skip release",
                extra={'order_id': str(order.order_id), 'event_id': event.id}
            )
            return
        
        # 回补库存
        from apps.tiers.services.inventory import release_inventory, InventoryError
        order_item = order.items.first()
        if order_item:
            try:
                release_inventory(order_item.tier.tier_id, order_item.quantity)
                logger.info(
                    f"Inventory released for failed order {order.order_id}",
                    extra={
                        'order_id': str(order.order_id),
                        'tier_id': str(order_item.tier.tier_id),
                        'quantity': order_item.quantity
                    }
                )
            except InventoryError as e:
                logger.error(
                    f"Failed to release inventory: {e}",
                    exc_info=True,
                    extra={'order_id': str(order.order_id)}
                )
        
        log_webhook_event(
            event=event,
            order=order,
            action='payment_failed',
            old_status=old_status,
            new_status='failed'
        )


def handle_dispute_created(event):
    """
    处理争议事件
    
    ⭐ Phase D: 记录日志，不自动退款
    """
    charge_id = event.data.object.id
    
    logger.warning(
        f"Dispute created for charge {charge_id}",
        extra={
            'event_id': event.id,
            'charge_id': charge_id,
            'event_type': event.type
        }
    )
    
    # TODO: 发送通知给管理员
    # send_admin_notification('dispute_created', {'charge_id': charge_id})


@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook_view(request):
    """
    Stripe Webhook 入口
    
    ⭐ Phase D P0 核心特性：
    1. 签名验证（400失败）
    2. 事件白名单
    3. 双重幂等保障
    4. 统一返回码（200）
    5. 审计日志标准化
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # ============================================
    # 1. 签名验证
    # ⭐ Phase D P0: 签名失败返回 400
    # ============================================
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # 无效 payload
        logger.error(f"Invalid payload: {e}")
        return Response(
            {'error': 'Invalid payload'},
            status=400  # ⭐ 签名问题返回 400
        )
    except stripe.error.SignatureVerificationError as e:
        # 无效签名
        logger.error(f"Signature verification failed: {e}")
        return Response(
            {'error': 'Invalid signature'},
            status=400  # ⭐ 签名问题返回 400
        )
    
    # ============================================
    # 2. 事件白名单检查
    # ⭐ Phase D P0: 忽略不在白名单的事件
    # ============================================
    if event.type not in ALLOWED_EVENT_TYPES:
        logger.warning(
            f"Ignored Stripe event: {event.type} (not in whitelist)",
            extra={
                'event_id': event.id,
                'event_type': event.type,
                'allowed_types': list(ALLOWED_EVENT_TYPES)
            }
        )
        return Response(status=200)  # ⭐ 返回200，避免Stripe重试
    
    # ============================================
    # 3. 幂等性检查（第一层）
    # ⭐ Phase D P0: IdempotencyKey 去重
    # ============================================
    if check_and_mark_processed(event.id, 'stripe'):
        logger.info(
            f"Event {event.id} already processed (idempotent skip)",
            extra={'event_id': event.id, 'event_type': event.type}
        )
        return Response(status=200)
    
    # ============================================
    # 4. 事件分发处理
    # ⭐ Phase D P0: 所有业务异常返回 200
    # ============================================
    try:
        if event.type == 'payment_intent.succeeded':
            handle_payment_succeeded(event)
        elif event.type == 'payment_intent.payment_failed':
            handle_payment_failed(event)
        elif event.type == 'charge.dispute.created':
            handle_dispute_created(event)
    
    except Exception as e:
        # ⭐ 业务异常：记录日志 + Sentry + 返回 200
        logger.error(
            f"Webhook processing error: {e}",
            exc_info=True,
            extra={
                'event_id': event.id,
                'event_type': event.type,
                'payment_intent_id': event.data.object.get('id')
            }
        )
        
        # 上报 Sentry
        capture_exception(e)
        
        # ⭐ 返回 200，避免 Stripe 重试风暴
        return Response(status=200)
    
    return Response(status=200)
