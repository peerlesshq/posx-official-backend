"""
Webhook 审计日志工具

⭐ Phase D P0: 标准化审计日志格式
"""
import logging
from typing import Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


def log_webhook_event(
    event,
    order=None,
    action: str = '',
    old_status: Optional[str] = None,
    new_status: Optional[str] = None,
    reason: Optional[str] = None,
    **extra_fields
):
    """
    标准化 Webhook 审计日志
    
    ⭐ Phase D P0: 统一日志结构，便于追踪和分析
    
    Args:
        event: Stripe事件对象
        order: 订单对象（如果相关）
        action: 操作类型（如 'payment_succeeded'）
        old_status: 旧状态
        new_status: 新状态
        reason: 原因说明
        **extra_fields: 额外字段
    """
    log_data = {
        # 事件信息
        'event_id': event.id,
        'event_type': event.type,
        
        # 订单信息
        'site_id': str(order.site_id) if order else None,
        'order_id': str(order.order_id) if order else None,
        
        # 支付信息
        'payment_intent_id': event.data.object.get('id'),
        
        # 状态变更
        'old_status': old_status,
        'new_status': new_status,
        
        # 操作信息
        'actor': 'stripe_webhook',
        'action': action,
        'reason': reason,
        
        # 时间戳
        'timestamp': timezone.now().isoformat(),
    }
    
    # 合并额外字段
    log_data.update(extra_fields)
    
    # 移除 None 值（保持日志简洁）
    log_data = {k: v for k, v in log_data.items() if v is not None}
    
    # 记录日志
    logger.info(
        f"Webhook: {action or event.type}",
        extra=log_data
    )
