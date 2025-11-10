"""
Error Code Models

⭐ 错误码注册表：统一管理所有业务错误码
"""
import uuid
from django.db import models
from django.core.validators import RegexValidator


class ErrorCode(models.Model):
    """
    错误码注册表
    
    ⭐ 用途：
    - 错误码治理（防止野生错误码）
    - 文档自动生成
    - 监控告警配置
    - CI 校验
    
    域划分：
    - AUTH: 认证/会话
    - WALLET: 钱包连接
    - CUSTODY: 托管/Fireblocks
    - CHAIN: 资产与链
    - PAY: 支付/网关
    - RISK: 风控/合规
    - KYC: KYC/KYB
    - RATE: 速率与配额
    - SYS: 系统/依赖
    """
    
    DOMAIN_AUTH = 'AUTH'
    DOMAIN_WALLET = 'WALLET'
    DOMAIN_CUSTODY = 'CUSTODY'
    DOMAIN_CHAIN = 'CHAIN'
    DOMAIN_PAY = 'PAY'
    DOMAIN_RISK = 'RISK'
    DOMAIN_KYC = 'KYC'
    DOMAIN_RATE = 'RATE'
    DOMAIN_SYS = 'SYS'
    
    DOMAIN_CHOICES = [
        (DOMAIN_AUTH, 'Authentication'),
        (DOMAIN_WALLET, 'Wallet Connection'),
        (DOMAIN_CUSTODY, 'Custody/Fireblocks'),
        (DOMAIN_CHAIN, 'Chain/Assets'),
        (DOMAIN_PAY, 'Payment'),
        (DOMAIN_RISK, 'Risk/Compliance'),
        (DOMAIN_KYC, 'KYC/KYB'),
        (DOMAIN_RATE, 'Rate Limiting'),
        (DOMAIN_SYS, 'System'),
    ]
    
    SEVERITY_BLOCKING = 'BLOCKING'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_LOW = 'LOW'
    
    SEVERITY_CHOICES = [
        (SEVERITY_BLOCKING, 'Blocking'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_LOW, 'Low'),
    ]
    
    UI_DIALOG = 'DIALOG'
    UI_BANNER = 'BANNER'
    UI_TOAST = 'TOAST'
    UI_INLINE = 'INLINE'
    
    UI_CHOICES = [
        (UI_DIALOG, 'Modal Dialog'),
        (UI_BANNER, 'Page Banner'),
        (UI_TOAST, 'Toast'),
        (UI_INLINE, 'Inline'),
    ]
    
    error_code_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]+-\d{4}$',
                message='Code must be in format DOMAIN-XXXX (e.g. CUSTODY-1015)'
            )
        ],
        help_text="错误码（格式：DOMAIN-XXXX）"
    )
    domain = models.CharField(
        max_length=20,
        choices=DOMAIN_CHOICES,
        db_index=True,
        help_text="域"
    )
    http_status = models.IntegerField(
        help_text="HTTP 状态码（400/401/403/404/409/429/500/502/503）"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        db_index=True,
        help_text="严重度"
    )
    ui_type = models.CharField(
        max_length=20,
        choices=UI_CHOICES,
        default=UI_TOAST,
        help_text="UI 展示方式"
    )
    retryable = models.BooleanField(
        default=False,
        help_text="是否可重试"
    )
    default_msg_key = models.CharField(
        max_length=100,
        help_text="默认文案 Key（用于 i18n）"
    )
    default_actions = models.JSONField(
        default=list,
        help_text='默认恢复动作，如 ["RETRY", "CONTACT_SUPPORT"]'
    )
    owner_team = models.CharField(
        max_length=100,
        blank=True,
        help_text="负责团队"
    )
    runbook_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="运维手册 URL"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="是否启用"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'error_codes'
        indexes = [
            models.Index(fields=['domain', 'is_active']),
            models.Index(fields=['severity']),
            models.Index(fields=['code']),
        ]
        verbose_name = 'Error Code'
        verbose_name_plural = 'Error Codes'
        ordering = ['domain', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.default_msg_key}"


class ErrorMessage(models.Model):
    """
    错误消息多语言文案
    
    ⭐ 用途：
    - 支持多语言（en/zh/ja等）
    - 前端按 language 渲染
    - 独立管理文案（无需代码更新）
    """
    
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    msg_key = models.CharField(
        max_length=100,
        db_index=True,
        help_text="文案 Key"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        db_index=True,
        help_text="语言代码（en/zh/ja）"
    )
    title = models.CharField(
        max_length=255,
        help_text="标题"
    )
    message = models.TextField(
        help_text="消息内容"
    )
    action_labels = models.JSONField(
        default=dict,
        help_text='动作按钮文案，如 {"RETRY": "重试", "CONTACT_SUPPORT": "联系客服"}'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'error_messages'
        constraints = [
            models.UniqueConstraint(
                fields=['msg_key', 'language'],
                name='uq_error_message_key_lang'
            ),
        ]
        indexes = [
            models.Index(fields=['msg_key', 'language']),
        ]
        verbose_name = 'Error Message'
        verbose_name_plural = 'Error Messages'
    
    def __str__(self):
        return f"{self.msg_key} ({self.language})"


