"""
Webhook清理任务
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def cleanup_old_idempotency_keys(self):
    """
    清理过期的幂等键
    
    ⭐ 定时任务：每天凌晨3点运行
    - 删除 processed_at < (now - retention_hours) 的记录
    - 分页处理
    
    Returns:
        dict: {'deleted': int}
    """
    from apps.webhooks.models import IdempotencyKey
    
    retention_hours = getattr(settings, 'IDEMPOTENCY_KEY_RETENTION_HOURS', 48)
    cutoff = timezone.now() - timedelta(hours=retention_hours)
    
    logger.info(f"Cleaning idempotency keys older than {cutoff}")
    
    deleted, _ = IdempotencyKey.objects.filter(
        processed_at__lt=cutoff
    ).delete()
    
    logger.info(f"Deleted {deleted} old idempotency keys")
    return {'deleted': deleted}

