"""
代理树模型

⭐ RLS 安全：
- AgentTree 受 RLS 保护（site_id 隔离）
- 支持递归查询（CTE）

功能：
- 多层级代理结构（树形）
- 记录代理深度（便于查询）
- 支持激活/停用
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class AgentTree(models.Model):
    """
    代理树关系表
    
    字段说明：
    - agent: 代理用户（User）
    - parent: 上级代理（自关联）
    - depth: 深度（1=直接推荐，2=二级...）
    - path: 路径（便于快速查询上下线）格式：/root_id/parent_id/agent_id/
    - active: 激活状态
    """
    
    tree_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="关系唯一标识"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID（RLS隔离）"
    )
    agent = models.UUIDField(
        db_index=True,
        help_text="代理用户ID（关联 users.user_id）"
    )
    parent = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="上级代理ID（NULL=根节点）"
    )
    depth = models.PositiveSmallIntegerField(
        default=1,
        help_text="深度（1=直接推荐）"
    )
    path = models.TextField(
        help_text="路径（/root/parent/agent/）"
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_trees'
        indexes = [
            models.Index(fields=['site_id', 'agent']),
            models.Index(fields=['site_id', 'parent']),
            models.Index(fields=['site_id', 'active']),
            models.Index(fields=['depth']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['site_id', 'agent', 'parent'],
                name='unique_site_agent_parent'
            ),
        ]
        verbose_name = 'Agent Tree'
        verbose_name_plural = 'Agent Trees'
    
    def __str__(self):
        return f"Agent {self.agent} (depth={self.depth})"


class AgentStats(models.Model):
    """
    代理统计表（预计算）
    
    ⚠️ 本表数据由定时任务或触发器维护
    用于快速查询代理业绩
    
    字段说明：
    - agent: 代理用户ID
    - total_customers: 累计客户数（下线）
    - direct_customers: 直接客户数
    - total_sales: 累计销售额
    - total_commissions: 累计佣金
    - last_order_at: 最后订单时间
    """
    
    stat_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="统计记录ID"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID（RLS隔离）"
    )
    agent = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="代理用户ID"
    )
    total_customers = models.PositiveIntegerField(
        default=0,
        help_text="累计客户数"
    )
    direct_customers = models.PositiveIntegerField(
        default=0,
        help_text="直接客户数（depth=1）"
    )
    total_sales = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=0,
        help_text="累计销售额（USD）"
    )
    total_commissions = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=0,
        help_text="累计佣金"
    )
    last_order_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="最后订单时间"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_stats'
        indexes = [
            models.Index(fields=['site_id', 'agent']),
            models.Index(fields=['total_sales']),
            models.Index(fields=['last_order_at']),
        ]
        verbose_name = 'Agent Stats'
        verbose_name_plural = 'Agent Stats'
    
    def __str__(self):
        return f"Stats for Agent {self.agent}"


class AgentProfile(models.Model):
    """
    代理扩展资料（Phase F）
    
    ⚠️ 安全：
    - site_id 受 RLS 保护
    - balance_usd 使用悲观锁更新
    
    用途：
    - 代理等级管理（bronze/silver/gold/platinum）
    - 余额账户（内部结算）
    - KYC 状态追踪
    - 累计收入与提现统计
    """
    
    LEVEL_BRONZE = 'bronze'
    LEVEL_SILVER = 'silver'
    LEVEL_GOLD = 'gold'
    LEVEL_PLATINUM = 'platinum'
    
    LEVEL_CHOICES = [
        (LEVEL_BRONZE, 'Bronze'),
        (LEVEL_SILVER, 'Silver'),
        (LEVEL_GOLD, 'Gold'),
        (LEVEL_PLATINUM, 'Platinum'),
    ]
    
    KYC_PENDING = 'pending'
    KYC_APPROVED = 'approved'
    KYC_REJECTED = 'rejected'
    
    KYC_CHOICES = [
        (KYC_PENDING, 'Pending'),
        (KYC_APPROVED, 'Approved'),
        (KYC_REJECTED, 'Rejected'),
    ]
    
    profile_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="资料唯一标识"
    )
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='agent_profile',
        help_text="关联用户"
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='agent_profiles',
        help_text="所属站点（RLS隔离）"
    )
    agent_level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default=LEVEL_BRONZE,
        db_index=True,
        help_text="代理等级"
    )
    balance_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="可提现余额（USD）"
    )
    total_earned_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="累计收入（USD）"
    )
    total_withdrawn_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="累计提现（USD）"
    )
    kyc_status = models.CharField(
        max_length=20,
        choices=KYC_CHOICES,
        default=KYC_PENDING,
        db_index=True,
        help_text="KYC 认证状态"
    )
    kyc_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="KYC 提交时间"
    )
    kyc_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="KYC 批准时间"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="账户激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_profiles'
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'user'],
                name='uq_agent_profile_site_user'
            ),
            models.CheckConstraint(
                check=models.Q(balance_usd__gte=0),
                name='chk_agent_profile_balance_non_negative'
            ),
        ]
        indexes = [
            models.Index(fields=['site', 'agent_level']),
            models.Index(fields=['site', 'balance_usd']),
            models.Index(fields=['site', 'is_active']),
            models.Index(fields=['kyc_status']),
        ]
        verbose_name = 'Agent Profile'
        verbose_name_plural = 'Agent Profiles'
    
    def __str__(self):
        return f"{self.user.email} - {self.agent_level} (${self.balance_usd})"


class WithdrawalRequest(models.Model):
    """
    提现申请（Phase F）
    
    ⚠️ 安全：
    - 通过 agent_profile.site_id 受 RLS 保护
    - account_info 加密存储（JSONField + 应用层加密）
    
    流程：
    1. submitted: Agent 提交申请，扣减余额（悲观锁）
    2. approved: 管理员审核通过
    3. completed: 线下转账完成
    4. rejected/cancelled: 审核拒绝或取消，返还余额
    """
    
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    METHOD_BANK = 'bank_transfer'
    METHOD_PAYPAL = 'paypal'
    METHOD_CRYPTO = 'crypto'
    
    METHOD_CHOICES = [
        (METHOD_BANK, 'Bank Transfer'),
        (METHOD_PAYPAL, 'PayPal'),
        (METHOD_CRYPTO, 'Cryptocurrency'),
    ]
    
    request_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="申请唯一标识"
    )
    agent_profile = models.ForeignKey(
        AgentProfile,
        on_delete=models.PROTECT,
        related_name='withdrawal_requests',
        help_text="代理资料"
    )
    amount_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="提现金额（USD）"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED,
        db_index=True,
        help_text="申请状态"
    )
    withdrawal_method = models.CharField(
        max_length=50,
        choices=METHOD_CHOICES,
        help_text="提现方式"
    )
    account_info = models.JSONField(
        help_text="账户信息（加密存储）：{bank_name, account_number, ...}"
    )
    admin_note = models.TextField(
        blank=True,
        help_text="管理员备注"
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_withdrawals',
        help_text="审核人"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="审核时间"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="完成时间"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['submitted', 'approved', 'rejected', 'completed', 'cancelled']),
                name='chk_withdrawal_status'
            ),
        ]
        indexes = [
            models.Index(fields=['agent_profile', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['approved_by']),
        ]
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
    
    def __str__(self):
        return f"{self.agent_profile.user.email} - ${self.amount_usd} ({self.status})"


class CommissionStatement(models.Model):
    """
    佣金对账单（月度，Phase F）
    
    ⚠️ 生成方式：
    - Celery 定时任务（每月1号凌晨）
    - 手动触发（管理员）
    
    用途：
    - 财务对账
    - Agent 自查
    - 导出 PDF
    """
    
    statement_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="对账单唯一标识"
    )
    agent_profile = models.ForeignKey(
        AgentProfile,
        on_delete=models.PROTECT,
        related_name='statements',
        help_text="代理资料"
    )
    period_start = models.DateField(
        help_text="统计周期开始日期"
    )
    period_end = models.DateField(
        help_text="统计周期结束日期"
    )
    balance_start_of_period = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="期初余额（USD）"
    )
    balance_end_of_period = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="期末余额（USD）"
    )
    total_commissions_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="本期佣金总额"
    )
    paid_commissions_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="已结算佣金"
    )
    pending_commissions_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="未结算佣金（hold + ready）"
    )
    withdrawals_in_period = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text="本期提现金额（USD）"
    )
    order_count = models.PositiveIntegerField(
        default=0,
        help_text="本期订单数"
    )
    customer_count = models.PositiveIntegerField(
        default=0,
        help_text="本期新增客户数"
    )
    pdf_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="PDF 文件 URL"
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="生成时间"
    )
    
    class Meta:
        db_table = 'commission_statements'
        constraints = [
            models.UniqueConstraint(
                fields=['agent_profile', 'period_start', 'period_end'],
                name='uq_statement_agent_period'
            ),
        ]
        indexes = [
            models.Index(fields=['agent_profile', 'period_start']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['generated_at']),
        ]
        verbose_name = 'Commission Statement'
        verbose_name_plural = 'Commission Statements'
    
    def __str__(self):
        return f"{self.agent_profile.user.email} - {self.period_start} to {self.period_end}"



