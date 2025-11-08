"""
Webhook审计日志工具

⭐ Phase D: 标准化Webhook事件审计日志

功能：
- 统一日志格式
- 结构化extra字段
- 便于日志聚合和查询
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


def log_webhook_event(
    event_id: str,
    event_type: str,
    action: str,
    order_id: Optional[str] = None,
    site_id: Optional[str] = None,
    payment_intent_id: Optional[str] = None,
    old_status: Optional[str] = None,
    new_status: Optional[str] = None,
    **kwargs
) -> None:
    """
    记录Webhook事件审计日志
    
    Args:
        event_id: Stripe事件ID
        event_type: 事件类型
        action: 处理动作
        order_id: 订单ID（可选）
        site_id: 站点ID（可选）
        payment_intent_id: PaymentIntent ID（可选）
        old_status: 原状态（可选）
        new_status: 新状态（可选）
        **kwargs: 其他自定义字段
    """
    log_data = {
        'event_id': event_id,
        'event_type': event_type,
        'site_id': site_id,
        'order_id': order_id,
        'payment_intent_id': payment_intent_id,
        'old_status': old_status,
        'new_status': new_status,
        'actor': 'stripe_webhook',
        'action': action,
        'timestamp': timezone.now().isoformat(),
        **kwargs  # 允许扩展
    }
    
    logger.info(f"Webhook: {action}", extra=log_data)


def log_webhook_error(
    event_id: str,
    event_type: str,
    error_message: str,
    **kwargs
) -> None:
    """
    记录Webhook错误日志
    
    Args:
        event_id: Stripe事件ID
        event_type: 事件类型
        error_message: 错误消息
        **kwargs: 其他自定义字段
    """
    log_data = {
        'event_id': event_id,
        'event_type': event_type,
        'error': error_message,
        'actor': 'stripe_webhook',
        'timestamp': timezone.now().isoformat(),
        **kwargs
    }
    
    logger.error(f"Webhook error: {error_message}", extra=log_data)

