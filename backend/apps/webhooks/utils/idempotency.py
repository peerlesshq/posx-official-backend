"""
Webhook幂等性管理

⭐ Phase D & E: 双重幂等保障
- 第一层：IdempotencyKey（event_id）
- 第二层：业务状态检查（pending状态）

防止：
- Stripe/Fireblocks重试导致重复处理
- 并发webhook导致重复触发
"""
import logging
from django.db import IntegrityError, transaction
from django.core.cache import cache
from django.conf import settings
from apps.webhooks.models import IdempotencyKey

logger = logging.getLogger(__name__)


def check_and_mark_processed(key: str, source: str = 'stripe') -> bool:
    """
    检查并标记幂等键
    
    ⭐ Phase D & E: 幂等性保障
    使用数据库唯一约束保证线程安全
    
    参数:
        key: 幂等键（如event_id、txId）
        source: 来源（stripe/fireblocks）
    
    返回:
        True: 已处理过（重复）
        False: 首次处理（已标记）
    
    线程安全: 使用数据库唯一约束
    
    Examples:
        >>> if check_and_mark_processed('evt_xxx', 'stripe'):
        >>>     logger.info("Event already processed")
        >>>     return Response(status=200)
    """
    try:
        with transaction.atomic():
            IdempotencyKey.objects.create(
                source=source,
                key=key
            )
        
        logger.debug(f"[Idempotency] First processing: {source}:{key}")
        return False
        
    except IntegrityError:
        # 唯一约束冲突 = 已处理过
        logger.info(f"[Idempotency] Duplicate: {source}:{key}")
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

