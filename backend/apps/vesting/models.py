"""
Vesting模型 - 代币分期释放管理
支持TGE立即释放 + Linear线性释放
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class VestingPolicy(models.Model):
    """
    释放策略模板
    
    示例：
    - 10% TGE, 90% 分12个月线性释放
    """
    policy_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE)
    
    # 策略信息
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # TGE配置
    tge_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text='TGE立即释放百分比 (0-100)'
    )
    
    # Linear配置
    cliff_months = models.IntegerField(
        default=0,
        help_text='锁定期（月）'
    )
    linear_periods = models.IntegerField(
        help_text='分期数量'
    )
    period_unit = models.CharField(
        max_length=10,
        choices=[
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
        ],
        default='month'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vesting_policies'
        unique_together = ['site', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tge_percent}% TGE + {self.linear_periods} periods)"


class VestingSchedule(models.Model):
    """
    释放计划
    
    为每个订单创建一个schedule
    """
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE)
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='vesting_schedule')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    allocation = models.ForeignKey('allocations.Allocation', on_delete=models.CASCADE)
    policy = models.ForeignKey(VestingPolicy, on_delete=models.PROTECT)
    
    # 金额
    total_tokens = models.DecimalField(max_digits=18, decimal_places=6)
    tge_tokens = models.DecimalField(max_digits=18, decimal_places=6)
    locked_tokens = models.DecimalField(max_digits=18, decimal_places=6)
    
    # 时间
    unlock_start_date = models.DateField(help_text='线性释放开始日期')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vesting_schedules'
        indexes = [
            models.Index(fields=['site', 'user']),
            models.Index(fields=['unlock_start_date']),
        ]
    
    def __str__(self):
        return f"Schedule {self.order_id} - {self.total_tokens} tokens"


class VestingRelease(models.Model):
    """
    释放明细（每期）
    
    状态流转：
    - locked: 未解锁
    - unlocked: 已解锁，可发放
    - processing: 发放中（Fireblocks processing）
    - released: 已发放（链上confirmed）
    """
    STATUS_LOCKED = 'locked'
    STATUS_UNLOCKED = 'unlocked'
    STATUS_PROCESSING = 'processing'
    STATUS_RELEASED = 'released'
    
    STATUS_CHOICES = [
        (STATUS_LOCKED, 'Locked'),
        (STATUS_UNLOCKED, 'Unlocked'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_RELEASED, 'Released'),
    ]
    
    release_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    schedule = models.ForeignKey(VestingSchedule, on_delete=models.CASCADE, related_name='releases')
    
    # 期数信息
    period_no = models.IntegerField(help_text='期数（0=TGE）')
    release_date = models.DateField(help_text='计划释放日期')
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))]
    )
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_LOCKED,
        db_index=True
    )
    
    # ========== Task 3: Fireblocks字段 ⭐ ==========
    
    # Fireblocks交易信息
    chain_amount = models.DecimalField(
        max_digits=24,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='链上实际转账数量'
    )
    
    fireblocks_tx_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text='Fireblocks交易ID'
    )
    
    tx_hash = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='链上交易哈希'
    )
    
    # 时间戳
    unlocked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='解锁时间'
    )
    
    released_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='发放完成时间'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vesting_releases'
        unique_together = ['schedule', 'period_no']
        indexes = [
            models.Index(fields=['status', 'unlocked_at']),
            models.Index(fields=['fireblocks_tx_id']),
            models.Index(fields=['release_date']),
        ]
    
    def __str__(self):
        return f"Release P{self.period_no} - {self.amount} ({self.status})"

