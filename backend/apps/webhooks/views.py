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
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status
from sentry_sdk import capture_exception

from apps.orders.models import Order
from apps.webhooks.models import IdempotencyKey, WebhookEvent
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


# ============================================
# ⭐ Phase E: Fireblocks Webhook 处理器
# ============================================

import json
from rest_framework.views import APIView

from apps.vesting.services.batch_release_service import (
    handle_release_completed,
    handle_release_failed
)
from apps.vesting.metrics import (
    vesting_webhook_received_total,
    vesting_webhook_completed_total,
    vesting_webhook_duplicate_total
)


class FireblocksWebhookView(APIView):
    """
    Fireblocks Webhook接收器
    
    ⭐ Phase E 安全特性:
    - MOCK模式: 内网限制 + X-MOCK-WEBHOOK头检测
    - LIVE模式: RSA签名验证 + IP白名单
    - 幂等性保障
    """
    
    permission_classes = [AllowAny]
    
    # ⭐ Fireblocks官方出口IP段（需定期更新）
    FIREBLOCKS_IP_WHITELIST = [
        '34.225.112.0/24',
        '52.5.67.0/24',
    ]
    
    def post(self, request):
        """处理Fireblocks webhook事件"""
        # 0. 检测模式
        is_mock = request.headers.get('X-MOCK-WEBHOOK') == 'true'
        mode = getattr(settings, 'FIREBLOCKS_MODE', 'MOCK')
        
        # ========== 安全验证 ⭐ ==========
        
        if mode == 'LIVE' and not is_mock:
            # LIVE模式多层防护
            client_ip = self._get_client_ip(request)
            if not self._is_allowed_ip(client_ip):
                logger.error(
                    f"[Fireblocks] Unauthorized IP: {client_ip}",
                    extra={'ip': client_ip}
                )
                return Response({'error': 'Unauthorized'}, status=403)
            
            signature = request.headers.get('X-Fireblocks-Signature')
            if not signature:
                return Response({'error': 'Missing signature'}, status=400)
            
            if not self._verify_signature(request.body, signature):
                logger.error("[Fireblocks] Signature verification failed")
                return Response({'error': 'Invalid signature'}, status=400)
        
        elif is_mock:
            # MOCK模式限制
            client_ip = self._get_client_ip(request)
            if not self._is_local_ip(client_ip):
                logger.error(f"[MOCK] Unauthorized IP: {client_ip}")
                return Response({'error': 'MOCK mode: localhost only'}, status=403)
        
        # ========== 解析事件 ==========
        
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=400)
        
        event_type = payload.get('type')
        tx_id = payload.get('txId')
        
        if not tx_id:
            return Response({'error': 'Missing txId'}, status=400)
        
        logger.info(
            f"[Fireblocks] Webhook received",
            extra={'event_type': event_type, 'tx_id': tx_id, 'mode': mode}
        )
        
        # ========== 幂等性检查 ⭐ ==========
        
        from apps.webhooks.utils.idempotency import check_and_mark_processed
        
        if check_and_mark_processed(tx_id, 'fireblocks'):
            vesting_webhook_duplicate_total.inc()
            logger.info(
                f"[Fireblocks] Event already processed: {tx_id}",
                extra={'tx_id': tx_id}
            )
            return Response({'status': 'duplicate'}, status=200)
        
        # ========== 事件处理 ==========
        
        if event_type == 'TRANSACTION_STATUS_UPDATED':
            self._handle_transaction_status(payload)
        else:
            logger.warning(
                f"[Fireblocks] Unknown event type: {event_type}",
                extra={'event_type': event_type}
            )
        
        return Response({'status': 'received'}, status=200)
    
    def _handle_transaction_status(self, payload: dict) -> None:
        """处理交易状态更新"""
        tx_id = payload.get('txId')
        status = payload.get('status')
        tx_hash = payload.get('txHash')
        
        from apps.vesting.models import VestingRelease
        
        try:
            release = VestingRelease.objects.get(fireblocks_tx_id=tx_id)
            release_id = str(release.release_id)
            
            if status == 'COMPLETED':
                handle_release_completed(release_id, tx_hash)
                vesting_webhook_completed_total.labels(status='COMPLETED').inc()
                
                logger.info(
                    f"[Fireblocks] Release completed: {release_id}",
                    extra={'release_id': release_id, 'tx_id': tx_id, 'tx_hash': tx_hash}
                )
            
            elif status in ['FAILED', 'CANCELLED']:
                reason = payload.get('subStatus', status)
                handle_release_failed(release_id, reason)
                vesting_webhook_completed_total.labels(status=status).inc()
                
                logger.warning(
                    f"[Fireblocks] Release failed: {release_id}",
                    extra={'release_id': release_id, 'tx_id': tx_id, 'reason': reason}
                )
        
        except VestingRelease.DoesNotExist:
            logger.error(
                f"[Fireblocks] Release not found for tx: {tx_id}",
                extra={'tx_id': tx_id}
            )
    
    def _get_client_ip(self, request) -> str:
        """获取客户端真实IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def _is_allowed_ip(self, ip: str) -> bool:
        """检查IP是否在白名单"""
        import ipaddress
        
        try:
            client_ip = ipaddress.ip_address(ip)
            for cidr in self.FIREBLOCKS_IP_WHITELIST:
                if client_ip in ipaddress.ip_network(cidr):
                    return True
            return False
        except ValueError:
            return False
    
    def _is_local_ip(self, ip: str) -> bool:
        """检查是否本地IP"""
        return ip in ['127.0.0.1', 'localhost', '::1']
    
    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """验证RSA签名（支持双公钥）"""
        from apps.webhooks.utils.fireblocks_crypto import verify_fireblocks_signature
        
        public_key = getattr(settings, 'FIREBLOCKS_WEBHOOK_PUBLIC_KEY', '')
        if public_key and verify_fireblocks_signature(payload, signature, public_key):
            return True
        
        public_key_2 = getattr(settings, 'FIREBLOCKS_WEBHOOK_PUBLIC_KEY_2', '')
        if public_key_2 and verify_fireblocks_signature(payload, signature, public_key_2):
            logger.info("[Fireblocks] Verified with backup key")
            return True
        
        return False


# ============================================
# Webhook 重放 API（Retool 对接）
# ============================================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def replay_webhook_event(request):
    """
    POST /api/v1/webhooks/replay
    Body: { "event_id": "uuid" }
    
    重放失败的 webhook 事件
    
    ⭐ Retool 对接：管理员手动重放
    """
    event_id = request.data.get('event_id')
    
    if not event_id:
        return Response(
            {'error': 'Missing event_id parameter'},
            status=http_status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 查询 webhook 事件记录
        event = WebhookEvent.objects.get(event_id=event_id)
        
        # 检查是否可重放
        if event.processing_status not in ['failed', 'pending']:
            return Response(
                {'error': f'Cannot replay event with status: {event.processing_status}'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        # 重置状态
        event.processing_status = 'pending'
        event.error_message = None
        event.save(update_fields=['processing_status', 'error_message'])
        
        # 根据来源重新处理
        try:
            if event.source == 'fireblocks':
                # Fireblocks webhook 重放
                from apps.webhooks.handlers import handle_vesting_release_status
                handle_vesting_release_status(event.payload)
                
                # 更新状态
                event.processing_status = 'processed'
                event.processed_at = timezone.now()
                event.save()
                
            elif event.source == 'stripe':
                # Stripe webhook 重放（如需要）
                logger.info(f"Stripe webhook replay not implemented yet")
                return Response(
                    {'error': 'Stripe webhook replay not implemented'},
                    status=http_status.HTTP_501_NOT_IMPLEMENTED
                )
            
            logger.info(
                f"Webhook event replayed successfully",
                extra={
                    'event_id': str(event.event_id),
                    'source': event.source,
                    'tx_id': event.tx_id,
                    'admin': request.user.email
                }
            )
            
            return Response({
                'status': 'replayed',
                'event_id': str(event.event_id),
                'message': 'Webhook event replayed successfully'
            })
            
        except Exception as e:
            # 重放失败
            event.processing_status = 'failed'
            event.error_message = str(e)
            event.save()
            
            logger.error(
                f"Webhook replay failed: {e}",
                exc_info=True,
                extra={'event_id': str(event.event_id)}
            )
            
            return Response(
                {'error': f'Replay failed: {str(e)}'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except WebhookEvent.DoesNotExist:
        return Response(
            {'error': 'Event not found'},
            status=http_status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
        )
