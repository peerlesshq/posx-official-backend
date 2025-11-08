"""
Commission模型 - 佣金（受RLS保护）
支持多级佣金：L1(12%) + L2(4%)
状态机：hold(7天) → ready → paid/cancelled
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Commission(models.Model):
    """
    佣金模型（受RLS保护，通过order.site_id）
    
    ⚠️ 安全：
    - 通过order关联site_id，受RLS保护
    - 幂等性：(order_id, agent_id, level)唯一
    
    状态机（4态）：
    - hold: 持有期（订单paid后创建，hold 7天）
    - ready: 可结算（7天后自动释放）
    - paid: 已结算（管理员批量结算）
    - cancelled: 已取消（订单dispute或取消）
    
    ⚠️ 禁止：
    - 无clawback（已付佣金不追回）
    - paid状态不可逆
    
    佣金等级：
    - level 1: 直推（12%）
    - level 2: 间推（4%）
    """
    STATUS_HOLD = 'hold'
    STATUS_READY = 'ready'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_HOLD, 'Hold'),
        (STATUS_READY, 'Ready'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    commission_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="佣金唯一标识"
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='commissions',
        help_text="关联订单"
    )
    agent = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='earned_commissions',
        help_text="代理人（获得佣金者）"
    )
    level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="佣金等级（1=直推, 2=间推）"
    )
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="佣金比例（%）"
    )
    commission_amount_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="佣金金额（USD）"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_HOLD,
        db_index=True,
        help_text="佣金状态"
    )
    hold_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="持有截止时间（创建后7天）"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="结算时间"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commissions'
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['hold', 'ready', 'paid', 'cancelled']),
                name='chk_commission_status'
            ),
            models.UniqueConstraint(
                fields=['order', 'agent', 'level'],
                name='uq_commission_order_agent_level'
            ),
        ]
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', 'hold_until']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Commission'
        verbose_name_plural = 'Commissions'
    
    def __str__(self):
        return f"L{self.level} {self.agent} - ${self.commission_amount_usd} ({self.status})"


class CommissionConfig(models.Model):
    """
    佣金配置（受RLS保护）
    
    每个站点独立配置佣金等级与比例
    
    示例：
    - NA站点: L1=12%, L2=4%, hold_days=7
    - ASIA站点: L1=10%, L2=5%, hold_days=14
    """
    config_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="配置唯一标识"
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='commission_configs',
        help_text="所属站点"
    )
    level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="佣金等级"
    )
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="佣金比例（%）"
    )
    hold_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text="持有天数"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="配置激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commission_configs'
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'level'],
                name='uq_commission_config_site_level'
            ),
        ]
        indexes = [
            models.Index(fields=['site', 'is_active']),
            models.Index(fields=['level']),
        ]
        verbose_name = 'Commission Config'
        verbose_name_plural = 'Commission Configs'
    
    def __str__(self):
        return f"{self.site.code} L{self.level}: {self.rate_percent}%"



