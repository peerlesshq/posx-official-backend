"""
Webhook幂等性模型 - 防止重复处理（全局表）
支持Stripe与Fireblocks webhook事件去重
"""
import uuid
from django.db import models


class IdempotencyKey(models.Model):
    """
    幂等键模型（全局）
    
    用途：
    - Stripe webhook事件去重
    - Fireblocks webhook事件去重
    - 防止重复处理导致的数据不一致
    
    清理策略：
    - 48小时后自动清理（Celery定时任务）
    - 保留payload用于排查
    """
    SOURCE_STRIPE = 'stripe'
    SOURCE_FIREBLOCKS = 'fireblocks'
    
    SOURCE_CHOICES = [
        (SOURCE_STRIPE, 'Stripe'),
        (SOURCE_FIREBLOCKS, 'Fireblocks'),
    ]
    
    key_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="记录唯一标识"
    )
    key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="幂等键（webhook事件ID）"
    )
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        db_index=True,
        help_text="来源系统"
    )
    processed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="处理时间"
    )
    payload = models.JSONField(
        null=True,
        blank=True,
        help_text="原始payload（用于排查）"
    )
    
    class Meta:
        db_table = 'idempotency_keys'
        indexes = [
            models.Index(fields=['key', 'source']),
            models.Index(fields=['source', 'processed_at']),
            models.Index(fields=['processed_at']),
        ]
        verbose_name = 'Idempotency Key'
        verbose_name_plural = 'Idempotency Keys'
    
    def __str__(self):
        return f"{self.source}: {self.key[:20]}..."



