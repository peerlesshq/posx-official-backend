"""
Notifications Models

⭐ 核心数据模型（5个）:
1. NotificationTemplate - 通知模板
2. Notification - 通知记录
3. NotificationChannelTask - 渠道发送任务
4. NotificationPreference - 用户偏好设置
5. NotificationReadReceipt - 公告已读回执

所有表均受 RLS 保护（通过 site_id 隔离）
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class NotificationTemplate(models.Model):
    """
    通知模板

    ⚠️ 安全：
    - site_id 可空：NULL=全局模板，有值=站点覆盖模板
    - 支持模板继承（parent_template_id）
    - 受 RLS 保护

    用途：
    - 支持多语言模板
    - 渠道特定配置（Email 主题/Slack Blocks）
    - 站点可覆盖全局模板
    """

    CHANNEL_IN_APP = 'in_app'
    CHANNEL_EMAIL = 'email'
    CHANNEL_SLACK = 'slack'
    CHANNEL_WEBHOOK = 'webhook'

    CHANNEL_CHOICES = [
        (CHANNEL_IN_APP, 'In-App'),
        (CHANNEL_EMAIL, 'Email'),
        (CHANNEL_SLACK, 'Slack'),
        (CHANNEL_WEBHOOK, 'Webhook'),
    ]

    template_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="模板唯一标识"
    )
    site_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="站点ID（NULL=全局模板，有值=站点覆盖模板）"
    )
    parent_template_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="父模板ID（用于模板继承）"
    )
    name = models.CharField(
        max_length=100,
        help_text="模板名称（如 order.payment.success）"
    )
    category = models.CharField(
        max_length=50,
        db_index=True,
        help_text="分类（finance/order/security/system/agent）"
    )
    subcategory = models.CharField(
        max_length=50,
        help_text="子分类（payment_success/commission_ready）"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="语言代码（en/zh/ja）"
    )
    title_template = models.TextField(
        help_text="标题模板（支持 Django Template 语法）"
    )
    body_template = models.TextField(
        help_text="正文模板（支持 Django Template 语法）"
    )
    channels = models.JSONField(
        default=list,
        help_text='支持的渠道列表，如 ["in_app", "email"]'
    )
    channel_configs = models.JSONField(
        default=dict,
        help_text='渠道特定配置（邮件主题/Slack Blocks）'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="激活状态"
    )
    created_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="创建者（管理员用户ID）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_templates'
        constraints = [
            models.UniqueConstraint(
                fields=['site_id', 'name'],
                name='uq_notification_template_site_name'
            ),
        ]
        indexes = [
            models.Index(fields=['site_id', 'is_active']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['name', 'language']),
        ]
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'

    def __str__(self):
        site_prefix = f"[{self.site_id}] " if self.site_id else "[Global] "
        return f"{site_prefix}{self.name} ({self.language})"


class Notification(models.Model):
    """
    通知记录

    ⚠️ 安全：
    - site_id 受 RLS 策略保护
    - recipient_id 由应用层过滤
    - 支持站点广播（recipient_type='site_broadcast', recipient_id=NULL）

    状态机：
    - 创建后立即可见（visible_at）
    - 用户标记已读（read_at）
    - 可选过期时间（expires_at）
    """

    RECIPIENT_USER = 'user'
    RECIPIENT_AGENT = 'agent'
    RECIPIENT_ADMIN = 'admin'
    RECIPIENT_SITE_BROADCAST = 'site_broadcast'

    RECIPIENT_CHOICES = [
        (RECIPIENT_USER, 'User'),
        (RECIPIENT_AGENT, 'Agent'),
        (RECIPIENT_ADMIN, 'Admin'),
        (RECIPIENT_SITE_BROADCAST, 'Site Broadcast'),
    ]

    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Info'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    notification_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="通知唯一标识"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID（RLS 隔离）"
    )
    recipient_type = models.CharField(
        max_length=20,
        choices=RECIPIENT_CHOICES,
        db_index=True,
        help_text="接收者类型"
    )
    recipient_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="用户ID（site_broadcast时为NULL）"
    )
    category = models.CharField(
        max_length=50,
        db_index=True,
        help_text="分类"
    )
    subcategory = models.CharField(
        max_length=50,
        help_text="子分类"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        db_index=True,
        help_text="严重度"
    )
    source_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="来源类型（order/commission/withdrawal/admin_action）"
    )
    source_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="来源对象ID（订单ID/佣金ID等）"
    )
    title = models.CharField(
        max_length=255,
        help_text="标题（已渲染）"
    )
    body = models.TextField(
        help_text="正文（已渲染）"
    )
    payload = models.JSONField(
        default=dict,
        help_text="原始数据（金额使用字符串）"
    )
    action_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="跳转链接（App Deep Link）"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="已读时间"
    )
    visible_at = models.DateTimeField(
        db_index=True,
        help_text="可见时间（支持定时发布）"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="过期时间"
    )
    created_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="创建者（系统/管理员）"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications'
        constraints = [
            models.CheckConstraint(
                check=models.Q(recipient_type__in=['user', 'agent', 'admin', 'site_broadcast']),
                name='chk_notifications_recipient_type'
            ),
            models.CheckConstraint(
                check=models.Q(severity__in=['info', 'warning', 'high', 'critical']),
                name='chk_notifications_severity'
            ),
            # site_broadcast 时 recipient_id 必须为 NULL
            models.CheckConstraint(
                check=(
                    models.Q(recipient_type='site_broadcast', recipient_id__isnull=True) |
                    ~models.Q(recipient_type='site_broadcast', recipient_id__isnull=False)
                ),
                name='chk_notifications_broadcast_recipient'
            ),
        ]
        indexes = [
            models.Index(fields=['site_id', 'recipient_id', 'read_at']),
            models.Index(fields=['site_id', 'visible_at']),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['recipient_type', 'created_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-visible_at', '-created_at']

    def __str__(self):
        return f"[{self.severity}] {self.title[:50]}"


class NotificationChannelTask(models.Model):
    """
    渠道发送任务

    ⚠️ 说明：
    - 描述每个渠道的发送状态
    - 支持失败重试（最多3次）
    - 通过 notification 关联继承 RLS 保护

    状态机：
    - pending: 待发送
    - sent: 已发送
    - failed: 发送失败（可重试）
    """

    CHANNEL_IN_APP = 'in_app'
    CHANNEL_EMAIL = 'email'
    CHANNEL_SLACK = 'slack'
    CHANNEL_WEBHOOK = 'webhook'

    CHANNEL_CHOICES = [
        (CHANNEL_IN_APP, 'In-App'),
        (CHANNEL_EMAIL, 'Email'),
        (CHANNEL_SLACK, 'Slack'),
        (CHANNEL_WEBHOOK, 'Webhook'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    ]

    task_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="任务唯一标识"
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='channel_tasks',
        help_text="关联通知"
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        db_index=True,
        help_text="渠道"
    )
    target = models.CharField(
        max_length=255,
        help_text="目标地址（邮箱/Slack Channel/Webhook URL）"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text="状态"
    )
    payload = models.JSONField(
        default=dict,
        help_text="渠道特定 payload"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="发送成功时间"
    )
    retry_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="重试次数"
    )
    last_error = models.TextField(
        null=True,
        blank=True,
        help_text="最后错误信息"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="下次重试时间"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_channel_tasks'
        constraints = [
            models.CheckConstraint(
                check=models.Q(channel__in=['in_app', 'email', 'slack', 'webhook']),
                name='chk_channel_tasks_channel'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'sent', 'failed']),
                name='chk_channel_tasks_status'
            ),
        ]
        indexes = [
            models.Index(fields=['notification']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['channel', 'status']),
        ]
        verbose_name = 'Notification Channel Task'
        verbose_name_plural = 'Notification Channel Tasks'

    def __str__(self):
        return f"{self.channel} - {self.status} (retry: {self.retry_count})"


class NotificationPreference(models.Model):
    """
    用户偏好设置

    ⚠️ 安全：
    - site_id 受 RLS 保护
    - 用户可配置每个分类的订阅状态
    - 支持免打扰时间段
    """

    preference_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="偏好设置ID"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID"
    )
    user_id = models.UUIDField(
        db_index=True,
        help_text="用户ID"
    )
    channel = models.CharField(
        max_length=20,
        help_text="渠道"
    )
    category = models.CharField(
        max_length=50,
        help_text="通知分类"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="是否启用"
    )
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="免打扰开始时间"
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="免打扰结束时间"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        constraints = [
            models.UniqueConstraint(
                fields=['site_id', 'user_id', 'channel', 'category'],
                name='uq_notification_preference'
            ),
        ]
        indexes = [
            models.Index(fields=['site_id', 'user_id']),
            models.Index(fields=['user_id', 'channel']),
        ]
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.user_id} - {self.channel}/{self.category}"


class NotificationReadReceipt(models.Model):
    """
    公告已读回执

    ⚠️ 用途：
    - 站点广播通知的已读状态追踪
    - 避免为每个用户创建重复通知记录
    - 通过 notification 关联继承 RLS 保护
    """

    receipt_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="回执ID"
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='read_receipts',
        help_text="关联通知（recipient_type='site_broadcast'）"
    )
    user_id = models.UUIDField(
        db_index=True,
        help_text="用户ID"
    )
    read_at = models.DateTimeField(
        auto_now_add=True,
        help_text="阅读时间"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification_read_receipts'
        constraints = [
            models.UniqueConstraint(
                fields=['notification', 'user_id'],
                name='uq_notification_read_receipt'
            ),
        ]
        indexes = [
            models.Index(fields=['notification', 'user_id']),
            models.Index(fields=['user_id', 'read_at']),
        ]
        verbose_name = 'Notification Read Receipt'
        verbose_name_plural = 'Notification Read Receipts'

    def __str__(self):
        return f"{self.user_id} read {self.notification_id} at {self.read_at}"

