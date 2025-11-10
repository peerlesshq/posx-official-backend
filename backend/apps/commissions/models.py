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
    
    ⚠️ 已废弃：建议使用 CommissionPlan（Phase F 多层级方案）
    保留用于向后兼容
    
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


class CommissionPlan(models.Model):
    """
    佣金方案（Phase F，多层级配置化）
    
    ⚠️ 安全：
    - site_id 受 RLS 保护
    - 每个站点可有多个方案（标准/高级/VIP）
    
    用途：
    - 支持 2-10 级佣金配置
    - 灵活的方案管理（标准/高级）
    - 默认方案设置
    
    示例：
    - 标准方案：L1=12%, L2=4%（2级）
    - 高级方案：L1=15%, L2=5%, L3=2%（3级）
    - VIP方案：L1=20%, L2=8%, L3=3%, L4=1%（4级）
    """
    
    plan_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="方案唯一标识"
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='commission_plans',
        help_text="所属站点（RLS隔离）"
    )
    name = models.CharField(
        max_length=100,
        help_text="方案名称（标准/高级/VIP）"
    )
    description = models.TextField(
        blank=True,
        help_text="方案描述"
    )
    max_levels = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="最大层级数（1-10）"
    )
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否为默认方案"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="方案激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commission_plans'
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'name'],
                name='uq_commission_plan_site_name'
            ),
        ]
        indexes = [
            models.Index(fields=['site', 'is_default']),
            models.Index(fields=['site', 'is_active']),
        ]
        verbose_name = 'Commission Plan'
        verbose_name_plural = 'Commission Plans'
    
    def __str__(self):
        default_marker = ' [默认]' if self.is_default else ''
        return f"{self.site.code} - {self.name}{default_marker}"


class CommissionPlanTier(models.Model):
    """
    佣金方案层级配置（Phase F）
    
    关联：CommissionPlan 的具体层级设置
    
    示例：
    - Plan "标准方案"
      - L1: 12%, hold 7天
      - L2: 4%, hold 7天
    - Plan "高级方案"
      - L1: 15%, hold 7天
      - L2: 5%, hold 7天
      - L3: 2%, hold 7天
    """
    
    tier_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="层级唯一标识"
    )
    plan = models.ForeignKey(
        CommissionPlan,
        on_delete=models.CASCADE,
        related_name='tiers',
        help_text="所属方案"
    )
    level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="层级编号（1-10）"
    )
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="佣金比例（%）"
    )
    hold_days = models.PositiveIntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text="持有天数"
    )
    min_order_amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="最小订单金额（USD，可选条件）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commission_plan_tiers'
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'level'],
                name='uq_commission_plan_tier_plan_level'
            ),
        ]
        indexes = [
            models.Index(fields=['plan', 'level']),
        ]
        verbose_name = 'Commission Plan Tier'
        verbose_name_plural = 'Commission Plan Tiers'
        ordering = ['plan', 'level']
    
    def __str__(self):
        return f"{self.plan.name} L{self.level}: {self.rate_percent}%"



