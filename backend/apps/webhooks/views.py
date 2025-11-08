"""
Stripe Webhook视图

⭐ Phase D: 完整的Webhook处理流程

安全特性：
1. 签名验证（400返回）
2. 白名单机制（忽略不相关事件）
3. 双重幂等保障（IdempotencyKey + 状态检查）
4. 所有业务异常返回200（避免Stripe重试风暴）
5. 审计日志标准化
"""
import logging
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.webhooks.handlers import (
    verify_stripe_signature,
    handle_payment_succeeded,
    handle_payment_failed,
    handle_dispute_created,
    ALLOWED_EVENT_TYPES
)
from apps.webhooks.utils.idempotency import check_and_mark_processed
from apps.webhooks.utils.audit import log_webhook_event, log_webhook_error

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # ⭐ CSRF由中间件豁免
def stripe_webhook_view(request):
    """
    Stripe Webhook接收端点
    
    ⭐ Phase D 修正：
    - 签名失败 → 400
    - 业务异常 → 200（避免重试）
    - 白名单机制
    - 双重幂等
    
    Returns:
        Response: 
            - 400: 签名验证失败
            - 200: 成功或业务异常（幂等）
    """
    # ============================================
    # 1. 签名验证
    # ⭐ Phase D: 签名失败返回400
    # ============================================
    try:
        event = verify_stripe_signature(request)
    except stripe.SignatureVerificationError as e:
        log_webhook_error(
            event_id='unknown',
            event_type='unknown',
            error_message=f"Signature verification failed: {e}"
        )
        return Response(
            {'error': 'Invalid signature'},
            status=400  # ⭐ 签名失败 → 400
        )
    
    # ============================================
    # 2. 白名单检查
    # ⭐ Phase D: 忽略不相关事件
    # ============================================
    if event.type not in ALLOWED_EVENT_TYPES:
        logger.warning(
            f"Ignored Stripe event: {event.type} (not in whitelist)",
            extra={'event_id': event.id, 'event_type': event.type}
        )
        return Response(status=200)  # ⭐ 忽略但返回200
    
    # ============================================
    # 3. 幂等性检查（第一层）
    # ⭐ Phase D: IdempotencyKey去重
    # ============================================
    if check_and_mark_processed(event.id, 'stripe'):
        logger.info(
            f"Event {event.id} already processed (idempotent skip)",
            extra={'event_id': event.id, 'event_type': event.type}
        )
        return Response(status=200)
    
    # ============================================
    # 4. 事件分发处理
    # ⭐ Phase D: 所有业务异常返回200
    # ============================================
    try:
        if event.type == 'payment_intent.succeeded':
            handle_payment_succeeded(event)
        
        elif event.type == 'payment_intent.payment_failed':
            handle_payment_failed(event)
        
        elif event.type == 'charge.dispute.created':
            handle_dispute_created(event)
        
    except Exception as e:
        # 业务异常：记录日志 + 返回200 ⭐
        log_webhook_error(
            event_id=event.id,
            event_type=event.type,
            error_message=f"Webhook processing failed: {e}",
            payment_intent_id=event.data.object.get('id')
        )
        logger.error(
            f"Webhook processing error: {e}",
            exc_info=True,
            extra={
                'event_id': event.id,
                'event_type': event.type,
                'payment_intent_id': event.data.object.get('id')
            }
        )
        
        # ⭐ 仍返回200，避免Stripe重试风暴
        return Response(status=200)
    
    # 处理成功
    logger.info(
        f"Webhook event processed successfully: {event.type}",
        extra={'event_id': event.id, 'event_type': event.type}
    )
    
    return Response(status=200)

