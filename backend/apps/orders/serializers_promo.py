"""
Promo Code 序列化器

⭐ 功能：
- 创建/更新 Promo Code（管理员）
- 查询 Promo Code（管理员/用户）
- 验证 Promo Code（用户）
"""
from rest_framework import serializers
from decimal import Decimal
from .models import PromoCode, PromoCodeUsage
from apps.tiers.models import Tier


class PromoCodeSerializer(serializers.ModelSerializer):
    """Promo Code 完整序列化器（管理员）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    applicable_tier_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tier.objects.all(),
        source='applicable_tiers',
        required=False,
        help_text="适用的档位ID列表（空=全部适用）"
    )
    
    class Meta:
        model = PromoCode
        fields = [
            'promo_id',
            'site',
            'site_code',
            'code',
            'name',
            'description',
            'discount_type',
            'discount_value',
            'bonus_tokens_value',
            'max_uses',
            'uses_per_user',
            'current_uses',
            'valid_from',
            'valid_until',
            'min_order_amount',
            'applicable_tier_ids',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['promo_id', 'current_uses', 'created_at', 'updated_at', 'site_code']
    
    def validate(self, data):
        """验证数据"""
        # 验证有效期
        if 'valid_from' in data and 'valid_until' in data:
            if data['valid_from'] >= data['valid_until']:
                raise serializers.ValidationError(
                    {'valid_until': '结束时间必须晚于开始时间'}
                )
        
        # 验证折扣类型和折扣值
        discount_type = data.get('discount_type')
        discount_value = data.get('discount_value', Decimal('0'))
        bonus_tokens_value = data.get('bonus_tokens_value', Decimal('0'))
        
        if discount_type == PromoCode.DISCOUNT_TYPE_PERCENTAGE:
            if discount_value <= 0 or discount_value > 100:
                raise serializers.ValidationError(
                    {'discount_value': '百分比折扣必须在0-100之间'}
                )
        
        elif discount_type == PromoCode.DISCOUNT_TYPE_FIXED:
            if discount_value <= 0:
                raise serializers.ValidationError(
                    {'discount_value': '固定金额折扣必须大于0'}
                )
        
        elif discount_type == PromoCode.DISCOUNT_TYPE_BONUS_TOKENS:
            if bonus_tokens_value <= 0:
                raise serializers.ValidationError(
                    {'bonus_tokens_value': '额外代币必须大于0'}
                )
        
        elif discount_type == PromoCode.DISCOUNT_TYPE_COMBO:
            if discount_value <= 0 and bonus_tokens_value <= 0:
                raise serializers.ValidationError(
                    '组合优惠至少需要设置折扣或额外代币'
                )
        
        return data


class PromoCodeListSerializer(serializers.ModelSerializer):
    """Promo Code 列表序列化器（简化版）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    uses_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = PromoCode
        fields = [
            'promo_id',
            'code',
            'name',
            'description',
            'discount_type',
            'discount_value',
            'bonus_tokens_value',
            'site_code',
            'current_uses',
            'max_uses',
            'uses_remaining',
            'valid_from',
            'valid_until',
            'is_active',
        ]
    
    def get_uses_remaining(self, obj):
        """计算剩余使用次数"""
        if obj.max_uses is None:
            return None
        return max(0, obj.max_uses - obj.current_uses)


class PromoCodeValidateRequestSerializer(serializers.Serializer):
    """验证 Promo Code 请求"""
    
    code = serializers.CharField(
        max_length=50,
        help_text="促销码"
    )
    tier_id = serializers.UUIDField(
        help_text="档位ID"
    )
    quantity = serializers.IntegerField(
        min_value=1,
        help_text="购买数量"
    )


class PromoCodeValidateResponseSerializer(serializers.Serializer):
    """验证 Promo Code 响应"""
    
    valid = serializers.BooleanField(
        help_text="是否有效"
    )
    code = serializers.CharField(
        required=False,
        help_text="促销码"
    )
    discount_amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="折扣金额（USD）"
    )
    bonus_tokens = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="额外代币"
    )
    final_price = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        required=False,
        help_text="最终价格（USD）"
    )
    message = serializers.CharField(
        required=False,
        help_text="提示信息"
    )
    error = serializers.CharField(
        required=False,
        help_text="错误信息（如果验证失败）"
    )
    error_code = serializers.CharField(
        required=False,
        help_text="错误代码（如果验证失败）"
    )


class PromoCodeUsageSerializer(serializers.ModelSerializer):
    """Promo Code 使用记录序列化器"""
    
    promo_code_code = serializers.CharField(source='promo_code.code', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    order_id = serializers.UUIDField(source='order.order_id', read_only=True)
    
    class Meta:
        model = PromoCodeUsage
        fields = [
            'usage_id',
            'promo_code',
            'promo_code_code',
            'order',
            'order_id',
            'user',
            'user_email',
            'discount_applied',
            'bonus_tokens_applied',
            'created_at',
        ]
        read_only_fields = ['usage_id', 'created_at']

