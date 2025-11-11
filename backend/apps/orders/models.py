"""
Order模型 - 订单（受RLS保护）
支持4态状态机：pending → paid/failed/cancelled

新增：
- PromoCode: 促销码模型（支持多种折扣类型）
- PromoCodeUsage: 促销码使用记录（审计+幂等性）
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Order(models.Model):
    """
    订单模型（受RLS保护）
    
    ⚠️ 安全：
    - site_id受RLS策略保护
    - site_id不可变（触发器保护）
    
    状态机（4态，严格禁止其他状态）：
    - pending: 待支付（创建后15分钟内）
    - paid: 已支付（payment_intent.succeeded）
    - failed: 支付失败（payment_intent.payment_failed）
    - cancelled: 已取消（超时或用户主动）
    
    ⚠️ 禁止：
    - 无退款状态（refunded等）
    - 不可逆：paid状态不可改为其他状态（除非dispute标记）
    
    幂等性：
    - idempotency_key: 防重复创建
    - stripe_payment_intent_id: Stripe唯一标识
    """
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    order_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="订单唯一标识"
    )
    buyer = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='orders',
        help_text="购买者"
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='orders',
        help_text="所属站点"
    )
    referrer = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_orders',
        help_text="推荐人"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text="订单状态"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Stripe PaymentIntent ID"
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="幂等键"
    )
    list_price_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="原价总额"
    )
    discount_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="折扣金额"
    )
    final_price_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="实付金额"
    )
    wallet_address = models.CharField(
        max_length=42,
        help_text="收币钱包地址（快照，lowercase）"
    )
    chain = models.CharField(
        max_length=20,
        choices=[
            ('ETH', 'Ethereum'),
            ('POLYGON', 'Polygon'),
            ('BSC', 'BSC'),
            ('TRON', 'TRON'),
        ],
        default='ETH',
        db_index=True,
        help_text="订单所在链（多链支持）"
    )
    disputed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否有争议（Stripe dispute）"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="过期时间（创建后15分钟）"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'paid', 'failed', 'cancelled']),
                name='chk_order_status'
            ),
        ]
        indexes = [
            models.Index(fields=['buyer', 'created_at']),
            models.Index(fields=['site', 'created_at']),
            models.Index(fields=['referrer']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['disputed']),
        ]
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order {self.order_id} ({self.status})"
    
    def save(self, *args, **kwargs):
        """保存前统一钱包地址为lowercase"""
        if self.wallet_address:
            self.wallet_address = self.wallet_address.lower()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    订单明细
    
    记录：
    - 购买的档位
    - 数量
    - 单价快照
    - 代币数量快照
    """
    item_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="明细唯一标识"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="所属订单"
    )
    tier = models.ForeignKey(
        'tiers.Tier',
        on_delete=models.PROTECT,
        help_text="档位（快照）"
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="购买数量"
    )
    unit_price_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="单价快照"
    )
    token_amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="代币数量快照"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['tier']),
        ]
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.tier.name} x{self.quantity}"


class PromoCode(models.Model):
    """
    促销码模型（受RLS保护）
    
    ⚠️ 安全：
    - site_id受RLS策略保护
    - site_id不可变（触发器保护）
    
    支持类型：
    - percentage: 百分比折扣（如 10% off）
    - fixed_amount: 固定金额折扣（如 $5 off）
    - bonus_tokens: 额外代币奖励（如 +100 tokens）
    - combo: 组合优惠（折扣 + 额外代币）
    
    使用限制：
    - max_uses: 总使用次数限制
    - uses_per_user: 每用户使用次数限制
    - 适用 Tier 限制（空=全部适用）
    - 最低订单金额限制
    """
    DISCOUNT_TYPE_PERCENTAGE = 'percentage'
    DISCOUNT_TYPE_FIXED = 'fixed_amount'
    DISCOUNT_TYPE_BONUS_TOKENS = 'bonus_tokens'
    DISCOUNT_TYPE_COMBO = 'combo'
    
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENTAGE, 'Percentage Discount'),
        (DISCOUNT_TYPE_FIXED, 'Fixed Amount Discount'),
        (DISCOUNT_TYPE_BONUS_TOKENS, 'Bonus Tokens Only'),
        (DISCOUNT_TYPE_COMBO, 'Combo (Discount + Tokens)'),
    ]
    
    promo_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="促销码唯一标识"
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='promo_codes',
        help_text="所属站点"
    )
    
    # 基本信息
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="促销码（唯一，不区分大小写）"
    )
    name = models.CharField(
        max_length=100,
        help_text="促销码名称"
    )
    description = models.TextField(
        blank=True,
        help_text="促销码描述"
    )
    
    # 折扣类型和值
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        help_text="折扣类型"
    )
    discount_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="折扣值（百分比或金额，取决于类型）"
    )
    bonus_tokens_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="额外代币奖励"
    )
    
    # 使用限制
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="最大使用次数（null=无限制）"
    )
    uses_per_user = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="每用户最大使用次数"
    )
    current_uses = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="当前使用次数"
    )
    
    # 有效期
    valid_from = models.DateTimeField(
        help_text="生效开始时间"
    )
    valid_until = models.DateTimeField(
        help_text="生效结束时间"
    )
    
    # 适用条件
    min_order_amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="最低订单金额要求（USD）"
    )
    applicable_tiers = models.ManyToManyField(
        'tiers.Tier',
        blank=True,
        related_name='promo_codes',
        help_text="适用的档位（空=适用所有档位）"
    )
    
    # 状态
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="是否激活"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'promo_codes'
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount_type__in=['percentage', 'fixed_amount', 'bonus_tokens', 'combo']),
                name='chk_promo_code_discount_type'
            ),
            models.CheckConstraint(
                check=models.Q(valid_from__lt=models.F('valid_until')),
                name='chk_promo_code_valid_dates'
            ),
        ]
        indexes = [
            models.Index(fields=['site', 'is_active']),
            models.Index(fields=['code']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'
    
    def __str__(self):
        return f"{self.code} ({self.site.code})"
    
    def save(self, *args, **kwargs):
        """保存前统一code为大写"""
        if self.code:
            self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    def is_valid_now(self) -> bool:
        """检查当前时间是否在有效期内"""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until
    
    def has_uses_remaining(self) -> bool:
        """检查是否还有可用次数"""
        if self.max_uses is None:
            return True
        return self.current_uses < self.max_uses


class PromoCodeUsage(models.Model):
    """
    促销码使用记录（审计 + 幂等性）
    
    ⚠️ 安全：
    - 通过order关联site_id，受RLS保护
    - 幂等性：(promo_code, order)唯一约束
    
    记录内容：
    - 使用的促销码
    - 关联的订单
    - 实际应用的折扣金额
    - 实际赠送的额外代币
    """
    usage_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="使用记录唯一标识"
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.PROTECT,
        related_name='usages',
        help_text="使用的促销码"
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='promo_usage',
        help_text="关联的订单（一对一）"
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='promo_usages',
        help_text="使用者"
    )
    
    # 快照（记录当时的折扣值）
    discount_applied = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="实际应用的折扣金额（USD）"
    )
    bonus_tokens_applied = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="实际赠送的额外代币"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promo_code_usages'
        constraints = [
            models.UniqueConstraint(
                fields=['promo_code', 'order'],
                name='uq_promo_code_usage_promo_order'
            ),
        ]
        indexes = [
            models.Index(fields=['promo_code']),
            models.Index(fields=['order']),
            models.Index(fields=['user', 'promo_code']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Promo Code Usage'
        verbose_name_plural = 'Promo Code Usages'
    
    def __str__(self):
        return f"{self.promo_code.code} used in Order {self.order.order_id}"



