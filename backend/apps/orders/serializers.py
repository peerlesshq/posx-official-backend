"""
订单序列化器

⭐ 功能：
- 创建订单（幂等）
- 查询订单
- 取消订单
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem
from apps.tiers.models import Tier


class OrderItemSerializer(serializers.ModelSerializer):
    """订单明细序列化器"""
    
    tier_name = serializers.CharField(source='tier.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'item_id',
            'tier',
            'tier_name',
            'quantity',
            'unit_price_usd',
            'token_amount',
            'created_at',
        ]
        read_only_fields = ['item_id', 'created_at']


class OrderCreateRequestSerializer(serializers.Serializer):
    """创建订单请求序列化器"""
    
    tier_id = serializers.UUIDField(
        help_text="档位ID"
    )
    quantity = serializers.IntegerField(
        min_value=1,
        help_text="购买数量"
    )
    wallet_address = serializers.CharField(
        max_length=42,
        help_text="收币钱包地址"
    )
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        help_text="推荐码（可选）"
    )
    
    def validate_wallet_address(self, value):
        """验证钱包地址"""
        from apps.users.utils.wallet import validate_address, normalize_address
        
        if not validate_address(value):
            raise serializers.ValidationError("无效的以太坊地址")
        
        return normalize_address(value)
    
    def validate_quantity(self, value):
        """验证数量"""
        from django.conf import settings
        
        max_quantity = getattr(settings, 'MAX_QUANTITY_PER_ORDER', 1000)
        
        if value > max_quantity:
            raise serializers.ValidationError(
                f"数量超过限制：{value} > {max_quantity}"
            )
        
        return value


class OrderCreateResponseSerializer(serializers.Serializer):
    """创建订单响应序列化器"""
    
    order_id = serializers.UUIDField()
    status = serializers.CharField()
    final_price_usd = serializers.DecimalField(max_digits=18, decimal_places=6)
    expires_at = serializers.DateTimeField()
    stripe = serializers.DictField()


class OrderSerializer(serializers.ModelSerializer):
    """订单序列化器（完整）"""
    
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)
    buyer_referral_code = serializers.CharField(source='buyer.referral_code', read_only=True)
    referrer_code = serializers.CharField(source='referrer.referral_code', read_only=True, allow_null=True)
    site_code = serializers.CharField(source='site.code', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_id',
            'site_code',
            'buyer_email',
            'buyer_referral_code',
            'referrer_code',
            'wallet_address',
            'status',
            'list_price_usd',
            'discount_usd',
            'final_price_usd',
            'stripe_payment_intent_id',
            'idempotency_key',
            'disputed',
            'expires_at',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['order_id', 'created_at', 'updated_at']


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器（精简）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_id',
            'site_code',
            'wallet_address',
            'status',
            'final_price_usd',
            'items_count',
            'expires_at',
            'created_at',
        ]
    
    def get_items_count(self, obj):
        """获取明细数量"""
        return obj.items.count()


class OrderCancelRequestSerializer(serializers.Serializer):
    """取消订单请求序列化器"""
    
    reason = serializers.CharField(
        required=False,
        default='USER_CANCELLED',
        max_length=50,
        help_text="取消原因"
    )


