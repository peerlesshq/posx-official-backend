"""
佣金计划模型

⭐ RLS 安全：
- CommissionPlan 和 CommissionPlanTier 都受 RLS 保护
- site_id 由数据库触发器保护（不可变）

功能：
- 版本化管理（同站点 name+version 唯一）
- 支持两种模式：level（层级固定）、solar_diff（太阳线差额）
- 时间范围控制（effective_from/to）
- 激活状态管理（单站点同名仅一个版本 active）
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CommissionPlan(models.Model):
    """
    佣金计划（主表）
    
    字段说明：
    - name: 计划名称（如 "Standard Plan"）
    - version: 版本号（同名计划的递增版本）
    - mode: 计算模式
      * 'level': 层级固定费率（如1级12%、2级5%）
      * 'solar_diff': 太阳线差额（高级别-低级别）
    - diff_reward_enabled: 是否启用差额奖励
    - effective_from/to: 生效时间范围
    - is_active: 激活状态（同站点同名仅一个 active）
    """
    
    MODE_LEVEL = 'level'
    MODE_SOLAR_DIFF = 'solar_diff'
    MODE_CHOICES = [
        (MODE_LEVEL, 'Level-based'),
        (MODE_SOLAR_DIFF, 'Solar Differential'),
    ]
    
    plan_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="计划唯一标识"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID（RLS隔离）"
    )
    name = models.CharField(
        max_length=100,
        help_text="计划名称"
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="版本号"
    )
    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default=MODE_LEVEL,
        help_text="计算模式"
    )
    diff_reward_enabled = models.BooleanField(
        default=False,
        help_text="是否启用差额奖励"
    )
    effective_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="生效开始时间"
    )
    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text="生效结束时间"
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="激活状态（同站点同名仅一个active）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commission_plans'
        indexes = [
            models.Index(fields=['site_id', 'name', 'version']),
            models.Index(fields=['site_id', 'is_active']),
            models.Index(fields=['effective_from', 'effective_to']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['site_id', 'name', 'version'],
                name='unique_site_plan_version'
            ),
        ]
        verbose_name = 'Commission Plan'
        verbose_name_plural = 'Commission Plans'
    
    def __str__(self):
        return f"{self.name} v{self.version} ({'Active' if self.is_active else 'Inactive'})"


class CommissionPlanTier(models.Model):
    """
    佣金计划层级配置
    
    字段说明：
    - level: 层级（1-10）
    - rate_percent: 费率百分比（如 12.00 表示 12%）
    - min_sales: 该层级最低销售额要求
    - diff_cap_percent: 差额封顶百分比（仅 solar_diff 模式）
    - hold_days: 佣金冻结天数
    """
    
    tier_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="层级配置唯一标识"
    )
    plan = models.ForeignKey(
        CommissionPlan,
        on_delete=models.CASCADE,
        related_name='tiers',
        help_text="所属计划"
    )
    level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="层级（1-10）"
    )
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="费率百分比（0-100）"
    )
    min_sales = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="该层级最低销售额"
    )
    diff_cap_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="差额封顶百分比（仅solar_diff模式）"
    )
    hold_days = models.PositiveSmallIntegerField(
        default=7,
        help_text="佣金冻结天数"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'commission_plan_tiers'
        indexes = [
            models.Index(fields=['plan', 'level']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'level'],
                name='unique_plan_level'
            ),
        ]
        ordering = ['level']
        verbose_name = 'Commission Plan Tier'
        verbose_name_plural = 'Commission Plan Tiers'
    
    def __str__(self):
        return f"Level {self.level}: {self.rate_percent}%"



