"""
Tier Admin Serializers（产品配置管理序列化器）

⭐ 权限：IsAdminUser（超级管理员）
⭐ 用途：前端可视化管理产品
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import Tier


class TierCreateSerializer(serializers.ModelSerializer):
    """产品创建序列化器"""
    
    class Meta:
        model = Tier
        fields = [
            'name',
            'description',
            'list_price_usd',
            'tokens_per_unit',
            'total_units',
            'display_order',
            'is_active',
            # 促销字段
            'bonus_tokens_per_unit',
            'promotional_price_usd',
            'promotion_valid_from',
            'promotion_valid_until',
        ]
    
    def validate_list_price_usd(self, value):
        """验证原价"""
        if value <= 0:
            raise serializers.ValidationError("原价必须大于0")
        return value
    
    def validate_tokens_per_unit(self, value):
        """验证代币数量"""
        if value <= 0:
            raise serializers.ValidationError("单位代币数量必须大于0")
        return value
    
    def validate_total_units(self, value):
        """验证总库存"""
        if value <= 0:
            raise serializers.ValidationError("总库存必须大于0")
        return value
    
    def validate(self, attrs):
        """交叉验证"""
        # 验证促销价必须低于原价
        promotional_price = attrs.get('promotional_price_usd')
        list_price = attrs.get('list_price_usd')
        
        if promotional_price and list_price:
            if promotional_price >= list_price:
                raise serializers.ValidationError({
                    'promotional_price_usd': '促销价必须低于原价'
                })
        
        # 验证促销时间范围
        valid_from = attrs.get('promotion_valid_from')
        valid_until = attrs.get('promotion_valid_until')
        
        if valid_from and valid_until:
            if valid_from >= valid_until:
                raise serializers.ValidationError({
                    'promotion_valid_until': '促销结束时间必须晚于开始时间'
                })
        
        # 如果设置了促销价，必须设置时间范围
        if promotional_price and not (valid_from and valid_until):
            raise serializers.ValidationError({
                'promotional_price_usd': '设置促销价时必须指定促销时间范围'
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        创建产品
        
        ⭐ 自动注入：
        - site：从 request.site 获取
        - sold_units：初始化为 0
        - available_units：等于 total_units
        """
        # 从 context 获取站点
        request = self.context.get('request')
        if not hasattr(request, 'site'):
            raise serializers.ValidationError("缺少站点上下文")
        
        # 自动设置字段
        validated_data['site'] = request.site
        validated_data['sold_units'] = 0
        validated_data['available_units'] = validated_data['total_units']
        validated_data['version'] = 0  # 乐观锁初始版本
        
        return super().create(validated_data)


class TierUpdateSerializer(serializers.ModelSerializer):
    """产品更新序列化器"""
    
    class Meta:
        model = Tier
        fields = [
            'name',
            'description',
            'list_price_usd',
            'tokens_per_unit',
            'total_units',  # 可调整总库存
            'display_order',
            'is_active',
            # 促销字段
            'bonus_tokens_per_unit',
            'promotional_price_usd',
            'promotion_valid_from',
            'promotion_valid_until',
        ]
    
    def validate_total_units(self, value):
        """
        验证总库存
        
        规则：
        - 新总库存 >= 已售数量
        """
        if self.instance and value < self.instance.sold_units:
            raise serializers.ValidationError(
                f"总库存不能低于已售数量 ({self.instance.sold_units})"
            )
        return value
    
    def validate(self, attrs):
        """交叉验证（同创建）"""
        promotional_price = attrs.get('promotional_price_usd')
        list_price = attrs.get('list_price_usd', self.instance.list_price_usd if self.instance else None)
        
        if promotional_price and list_price:
            if promotional_price >= list_price:
                raise serializers.ValidationError({
                    'promotional_price_usd': '促销价必须低于原价'
                })
        
        valid_from = attrs.get('promotion_valid_from')
        valid_until = attrs.get('promotion_valid_until')
        
        if valid_from and valid_until:
            if valid_from >= valid_until:
                raise serializers.ValidationError({
                    'promotion_valid_until': '促销结束时间必须晚于开始时间'
                })
        
        return attrs
    
    def update(self, instance, validated_data):
        """
        更新产品
        
        ⭐ 自动更新：
        - available_units：根据新 total_units 重新计算
        """
        # 如果更新了 total_units，重新计算 available_units
        if 'total_units' in validated_data:
            new_total = validated_data['total_units']
            validated_data['available_units'] = new_total - instance.sold_units
        
        return super().update(instance, validated_data)


class TierAdjustInventorySerializer(serializers.Serializer):
    """调整库存序列化器"""
    
    adjustment = serializers.IntegerField(
        required=True,
        help_text="库存调整量（正数=增加，负数=减少）"
    )
    reason = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="调整原因"
    )
    
    def validate_adjustment(self, value):
        """验证调整量"""
        if value == 0:
            raise serializers.ValidationError("调整量不能为0")
        return value
    
    def validate(self, attrs):
        """验证调整后的库存是否合法"""
        adjustment = attrs['adjustment']
        tier = self.context.get('tier')
        
        if not tier:
            raise serializers.ValidationError("缺少产品上下文")
        
        new_total = tier.total_units + adjustment
        
        # 新总库存不能小于已售数量
        if new_total < tier.sold_units:
            raise serializers.ValidationError({
                'adjustment': f"调整后总库存 ({new_total}) 不能低于已售数量 ({tier.sold_units})"
            })
        
        # 新总库存不能为负
        if new_total < 0:
            raise serializers.ValidationError({
                'adjustment': f"调整后总库存不能为负数"
            })
        
        return attrs


class TierAdminDetailSerializer(serializers.ModelSerializer):
    """产品详情序列化器（管理员视图）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = Tier
        fields = [
            'tier_id',
            'site_code',
            'site_name',
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
            'display_order',
            'version',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'tier_id',
            'site_code',
            'site_name',
            'sold_units',
            'available_units',
            'version',
            'created_at',
            'updated_at',
        ]

