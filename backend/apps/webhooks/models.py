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
    
    key_id = models.BigAutoField(primary_key=True)
    key = models.CharField(
        max_length=200,
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
        unique_together = ['source', 'key']  # ⭐ 唯一约束（线程安全）
        indexes = [
            models.Index(fields=['source', 'key']),
            models.Index(fields=['processed_at']),
        ]
        verbose_name = 'Idempotency Key'
        verbose_name_plural = 'Idempotency Keys'
    
    def __str__(self):
        return f"{self.source}: {self.key[:20]}..."


class WebhookEvent(models.Model):
    """
    Webhook 事件记录（用于监控和重放）
    
    ⭐ Retool 对接：
    - 记录所有 webhook 事件
    - 支持失败重放
    - 监控处理延迟
    
    用途：
    - 监控 webhook 处理状态
    - 重放失败事件
    - 审计和排查
    """
    
    STATUS_PENDING = 'pending'
    STATUS_PROCESSED = 'processed'
    STATUS_FAILED = 'failed'
    STATUS_DUPLICATE = 'duplicate'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSED, 'Processed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_DUPLICATE, 'Duplicate'),
    ]
    
    event_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="事件唯一标识"
    )
    source = models.CharField(
        max_length=50,
        db_index=True,
        help_text="来源系统（fireblocks/stripe）"
    )
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="事件类型（TRANSACTION_STATUS_UPDATED等）"
    )
    
    # 关联标识
    tx_id = models.CharField(
        max_length=200,
        db_index=True,
        help_text="交易ID或类似标识"
    )
    
    # 原始数据
    payload = models.JSONField(
        help_text="原始 payload"
    )
    
    # 处理状态
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text="处理状态"
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="错误信息（失败时）"
    )
    
    latency_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="处理延迟（毫秒）"
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="事件接收时间"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="处理完成时间"
    )
    
    class Meta:
        db_table = 'webhook_events'
        indexes = [
            models.Index(fields=['source', 'processing_status']),
            models.Index(fields=['tx_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['source', 'event_type']),
        ]
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
    
    def __str__(self):
        return f"{self.source} - {self.event_type} ({self.processing_status})"



