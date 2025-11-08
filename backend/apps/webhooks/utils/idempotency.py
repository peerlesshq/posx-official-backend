"""
Webhook幂等性管理

⭐ Phase D: 双重幂等保障
- 第一层：IdempotencyKey（event_id）
- 第二层：业务状态检查（pending状态）

防止：
- Stripe重试导致重复处理
- 并发webhook导致重复触发
"""
import logging
from django.core.cache import cache
from django.conf import settings
from apps.webhooks.models import IdempotencyKey

logger = logging.getLogger(__name__)


def check_and_mark_processed(event_id: str, source: str = 'stripe') -> bool:
    """
    检查事件是否已处理，并标记为已处理（原子操作）
    
    ⭐ Phase D: 幂等性第一层保障
    
    Args:
        event_id: Stripe事件ID
        source: 事件来源（stripe, manual等）
    
    Returns:
        bool: True表示已处理（幂等跳过），False表示首次处理
    
    Examples:
        >>> if check_and_mark_processed('evt_xxx', 'stripe'):
        >>>     logger.info("Event already processed")
        >>>     return Response(status=200)
    """
    try:
        # 尝试创建幂等记录（unique约束保证原子性）
        IdempotencyKey.objects.create(
            key=event_id,
            source=source
        )
        # 创建成功 → 首次处理
        logger.debug(f"Event {event_id} marked as processed")
        return False
        
    except Exception:
        # 创建失败（违反unique约束）→ 已处理
        logger.info(
            f"Event {event_id} already processed (idempotent skip)",
            extra={'event_id': event_id, 'source': source}
        )
        return True


def is_event_processed(event_id: str) -> bool:
    """
    仅检查事件是否已处理（不标记）
    
    Args:
        event_id: 事件ID
    
    Returns:
        bool: True表示已处理
    """
    return IdempotencyKey.objects.filter(key=event_id).exists()

