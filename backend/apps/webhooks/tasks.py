"""
Webhook 清理任务
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django.conf import settings

from apps.webhooks.models import IdempotencyKey

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def cleanup_old_idempotency_keys(self):
    """
    清理过期的幂等键
    
    ⭐ Celery Beat 定时任务（每天凌晨3点运行）
    - 删除超过保留期限的幂等键
    """
    logger.info("Starting cleanup_old_idempotency_keys task")
    
    retention_hours = getattr(settings, 'IDEMPOTENCY_KEY_RETENTION_HOURS', 48)
    cutoff_time = timezone.now() - timedelta(hours=retention_hours)
    
    # 删除过期的键
    deleted_count, _ = IdempotencyKey.objects.filter(
        processed_at__lt=cutoff_time
    ).delete()
    
    logger.info(
        f"Cleaned up {deleted_count} old idempotency keys",
        extra={
            'deleted_count': deleted_count,
            'retention_hours': retention_hours,
            'cutoff_time': cutoff_time.isoformat()
        }
    )
    
    return deleted_count
