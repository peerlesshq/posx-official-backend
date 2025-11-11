"""
档位序列化器

⭐ 功能：
- 档位列表（支持过滤）
- 档位详情
- 库存状态
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Tier


class TierSerializer(serializers.ModelSerializer):
    """档位序列化器（完整）- 包含促销信息"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    is_sold_out = serializers.SerializerMethodField()
    sold_percentage = serializers.SerializerMethodField()
    
    # 前端友好的促销信息
    pricing = serializers.SerializerMethodField()
    tokens = serializers.SerializerMethodField()
    inventory = serializers.SerializerMethodField()
    promotion = serializers.SerializerMethodField()
    
    class Meta:
        model = Tier
        fields = [
            'tier_id',
            'site_code',
            'name',
            'description',
            'list_price_usd',
            'tokens_per_unit',
            'bonus_tokens_per_unit',
            'promotional_price_usd',
            'promotion_valid_from',
            'promotion_valid_until',
            'total_units',
            'sold_units',
            'available_units',
            'is_sold_out',
            'sold_percentage',
            'display_order',
            'is_active',
            'created_at',
            'updated_at',
            # 前端友好字段
            'pricing',
            'tokens',
            'inventory',
            'promotion',
        ]
        read_only_fields = ['tier_id', 'site_code', 'created_at', 'updated_at']
    
    def get_is_sold_out(self, obj):
        """是否售罄"""
        return obj.available_units == 0
    
    def get_sold_percentage(self, obj):
        """售出百分比"""
        if obj.total_units == 0:
            return 0
        return round((obj.sold_units / obj.total_units) * 100, 2)
    
    def get_pricing(self, obj):
        """
        价格信息（前端友好）
        
        Returns:
        {
            "original_price": "0.10",
            "current_price": "0.08",
            "is_on_sale": true,
            "discount_percentage": "20.00"
        }
        """
        original_price = obj.list_price_usd
        current_price = obj.get_current_price()
        is_on_sale = obj.is_promotion_active()
        
        discount_percentage = Decimal('0')
        if is_on_sale and original_price > 0:
            discount_percentage = ((original_price - current_price) / original_price) * 100
        
        return {
            'original_price': str(original_price),
            'current_price': str(current_price),
            'is_on_sale': is_on_sale,
            'discount_percentage': str(discount_percentage.quantize(Decimal('0.01')))
        }
    
    def get_tokens(self, obj):
        """
        代币信息（前端友好）
        
        Returns:
        {
            "base_tokens": "999.0",
            "bonus_tokens": "100.0",
            "total_tokens": "1099.0"
        }
        """
        base_tokens = obj.tokens_per_unit
        bonus_tokens = obj.bonus_tokens_per_unit
        total_tokens = base_tokens + bonus_tokens
        
        return {
            'base_tokens': str(base_tokens),
            'bonus_tokens': str(bonus_tokens),
            'total_tokens': str(total_tokens)
        }
    
    def get_inventory(self, obj):
        """
        库存信息（前端友好）
        
        Returns:
        {
            "total": 10000,
            "available": 8523,
            "sold": 1477,
            "sold_percentage": 14.77
        }
        """
        return {
            'total': obj.total_units,
            'available': obj.available_units,
            'sold': obj.sold_units,
            'sold_percentage': self.get_sold_percentage(obj)
        }
    
    def get_promotion(self, obj):
        """
        促销信息（前端友好）
        
        Returns:
        {
            "active": true,
            "ends_at": "2025-11-30T23:59:59Z"
        }
        或
        {
            "active": false
        }
        """
        is_active = obj.is_promotion_active()
        result = {'active': is_active}
        
        if is_active and obj.promotion_valid_until:
            result['ends_at'] = obj.promotion_valid_until.isoformat()
        
        return result


class TierListSerializer(serializers.ModelSerializer):
    """档位列表序列化器（精简）- 包含促销信息"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    is_sold_out = serializers.SerializerMethodField()
    
    # 前端友好的简化信息
    current_price = serializers.SerializerMethodField()
    total_tokens = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    
    class Meta:
        model = Tier
        fields = [
            'tier_id',
            'site_code',
            'name',
            'description',
            'list_price_usd',
            'current_price',
            'tokens_per_unit',
            'bonus_tokens_per_unit',
            'total_tokens',
            'available_units',
            'is_sold_out',
            'is_on_sale',
            'is_active',
            'display_order',
        ]
    
    def get_is_sold_out(self, obj):
        """是否售罄"""
        return obj.available_units == 0
    
    def get_current_price(self, obj):
        """当前有效价格"""
        return str(obj.get_current_price())
    
    def get_total_tokens(self, obj):
        """总代币数"""
        return str(obj.get_total_tokens_per_unit())
    
    def get_is_on_sale(self, obj):
        """是否促销中"""
        return obj.is_promotion_active()


