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
    """档位序列化器（完整）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    is_sold_out = serializers.SerializerMethodField()
    sold_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Tier
        fields = [
            'tier_id',
            'site_code',
            'name',
            'description',
            'list_price_usd',
            'tokens_per_unit',
            'total_units',
            'sold_units',
            'available_units',
            'is_sold_out',
            'sold_percentage',
            'display_order',
            'is_active',
            'created_at',
            'updated_at',
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


class TierListSerializer(serializers.ModelSerializer):
    """档位列表序列化器（精简）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    is_sold_out = serializers.SerializerMethodField()
    
    class Meta:
        model = Tier
        fields = [
            'tier_id',
            'site_code',
            'name',
            'list_price_usd',
            'tokens_per_unit',
            'available_units',
            'is_sold_out',
            'is_active',
            'display_order',
        ]
    
    def get_is_sold_out(self, obj):
        """是否售罄"""
        return obj.available_units == 0


