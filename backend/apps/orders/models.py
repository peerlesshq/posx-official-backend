"""
Order模型 - 订单（受RLS保护）
支持4态状态机：pending → paid/failed/cancelled
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


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



