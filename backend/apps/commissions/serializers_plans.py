"""
Commission Plan 序列化器（Phase F）
"""
from decimal import Decimal
from rest_framework import serializers
from django.db import transaction

from apps.commissions.models import CommissionPlan, CommissionPlanTier


class CommissionPlanTierSerializer(serializers.ModelSerializer):
    """佣金方案层级序列化器"""
    
    rate_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        coerce_to_string=True
    )
    min_order_amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        coerce_to_string=True
    )
    
    class Meta:
        model = CommissionPlanTier
        fields = [
            'tier_id', 'level', 'rate_percent',
            'hold_days', 'min_order_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tier_id', 'created_at', 'updated_at']


class CommissionPlanSerializer(serializers.ModelSerializer):
    """佣金方案序列化器"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    tiers = CommissionPlanTierSerializer(many=True)
    
    class Meta:
        model = CommissionPlan
        fields = [
            'plan_id', 'site', 'site_code', 'name', 'description',
            'max_levels', 'is_default', 'is_active',
            'tiers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['plan_id', 'created_at', 'updated_at']
    
    def validate_tiers(self, value):
        """验证层级配置"""
        if not value:
            raise serializers.ValidationError("至少需要一个层级配置")
        
        # 验证 level 唯一且连续
        levels = sorted([tier['level'] for tier in value])
        if levels != list(range(1, len(levels) + 1)):
            raise serializers.ValidationError(
                "层级编号必须从1开始且连续（如：1,2,3）"
            )
        
        # 验证 max_levels 一致
        max_level = max(levels)
        if 'max_levels' in self.initial_data:
            if max_level != self.initial_data['max_levels']:
                raise serializers.ValidationError(
                    f"max_levels={self.initial_data['max_levels']} "
                    f"但层级配置最大为 L{max_level}"
                )
        
        return value
    
    def create(self, validated_data):
        """创建方案（含层级）"""
        tiers_data = validated_data.pop('tiers')
        
        with transaction.atomic():
            # 创建方案
            plan = CommissionPlan.objects.create(**validated_data)
            
            # 创建层级
            for tier_data in tiers_data:
                CommissionPlanTier.objects.create(
                    plan=plan,
                    **tier_data
                )
        
        return plan
    
    def update(self, instance, validated_data):
        """更新方案（含层级）"""
        tiers_data = validated_data.pop('tiers', None)
        
        with transaction.atomic():
            # 更新方案基本信息
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # 更新层级（简单策略：删除旧的，创建新的）
            if tiers_data is not None:
                instance.tiers.all().delete()
                for tier_data in tiers_data:
                    CommissionPlanTier.objects.create(
                        plan=instance,
                        **tier_data
                    )
        
        return instance


class CommissionPlanListSerializer(serializers.ModelSerializer):
    """佣金方案列表序列化器（简化版）"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    tier_count = serializers.IntegerField(
        source='tiers.count',
        read_only=True
    )
    
    class Meta:
        model = CommissionPlan
        fields = [
            'plan_id', 'site_code', 'name', 'description',
            'max_levels', 'tier_count', 'is_default',
            'is_active', 'created_at'
        ]

