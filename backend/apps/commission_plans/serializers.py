"""
佣金计划序列化器

⭐ 验证规则：
- 同站点 name+version 唯一
- 激活时检查是否有冲突（同站点同名仅一个 active）
- 批量创建 tiers 时验证 level 唯一性
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import CommissionPlan, CommissionPlanTier


class CommissionPlanTierSerializer(serializers.ModelSerializer):
    """佣金计划层级序列化器"""
    
    class Meta:
        model = CommissionPlanTier
        fields = [
            'tier_id',
            'level',
            'rate_percent',
            'min_sales',
            'diff_cap_percent',
            'hold_days',
            'created_at',
        ]
        read_only_fields = ['tier_id', 'created_at']
    
    def validate_level(self, value):
        """验证层级范围"""
        if value < 1 or value > 10:
            raise serializers.ValidationError("层级必须在 1-10 之间")
        return value
    
    def validate_rate_percent(self, value):
        """验证费率范围"""
        if value < Decimal('0') or value > Decimal('100'):
            raise serializers.ValidationError("费率必须在 0-100 之间")
        return value
    
    def validate_min_sales(self, value):
        """验证最低销售额"""
        if value < Decimal('0'):
            raise serializers.ValidationError("最低销售额不能为负数")
        return value
    
    def validate(self, attrs):
        """验证 diff_cap_percent 使用场景"""
        # 从 context 获取 plan（如果有）
        plan = self.context.get('plan')
        diff_cap_percent = attrs.get('diff_cap_percent')
        
        # 仅在 mode='solar_diff' 时允许 diff_cap_percent
        if plan and diff_cap_percent is not None:
            if plan.mode != 'solar_diff':
                raise serializers.ValidationError({
                    "diff_cap_percent": f"仅 mode='solar_diff' 时可设置差额封顶，当前 mode='{plan.mode}'"
                })
        
        return attrs


class CommissionPlanSerializer(serializers.ModelSerializer):
    """佣金计划序列化器"""
    
    tiers = CommissionPlanTierSerializer(many=True, read_only=True)
    tiers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CommissionPlan
        fields = [
            'plan_id',
            'site_id',
            'name',
            'version',
            'mode',
            'diff_reward_enabled',
            'effective_from',
            'effective_to',
            'is_active',
            'tiers',
            'tiers_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['plan_id', 'site_id', 'created_at', 'updated_at']
    
    def get_tiers_count(self, obj):
        """获取层级数量"""
        return obj.tiers.count()
    
    def validate(self, attrs):
        """验证计划数据"""
        # 验证时间范围
        effective_from = attrs.get('effective_from')
        effective_to = attrs.get('effective_to')
        
        if effective_from and effective_to:
            if effective_from >= effective_to:
                raise serializers.ValidationError({
                    "effective_to": "结束时间必须晚于开始时间"
                })
        
        # 验证 mode 与 diff_cap_percent 的一致性
        mode = attrs.get('mode')
        diff_reward_enabled = attrs.get('diff_reward_enabled', False)
        
        # mode='level' 时，diff_reward_enabled 必须为 false
        if mode == 'level' and diff_reward_enabled:
            raise serializers.ValidationError({
                "diff_reward_enabled": "mode='level' 时不支持差额奖励，请设置为 false"
            })
        
        return attrs


class CommissionPlanCreateSerializer(serializers.ModelSerializer):
    """创建佣金计划序列化器（带 site_id 注入）"""
    
    class Meta:
        model = CommissionPlan
        fields = [
            'name',
            'version',
            'mode',
            'diff_reward_enabled',
            'effective_from',
            'effective_to',
        ]
    
    def create(self, validated_data):
        """创建计划（自动注入 site_id）"""
        # 从 context 获取站点
        request = self.context.get('request')
        if not hasattr(request, 'site'):
            raise serializers.ValidationError("缺少站点上下文")
        
        validated_data['site_id'] = request.site.site_id
        return super().create(validated_data)


class CommissionPlanTierBulkCreateSerializer(serializers.Serializer):
    """批量创建层级序列化器"""
    
    tiers = CommissionPlanTierSerializer(many=True)
    
    def validate_tiers(self, tiers_data):
        """验证层级数据"""
        if not tiers_data:
            raise serializers.ValidationError("至少需要一个层级")
        
        # 验证 level 唯一性
        levels = [tier['level'] for tier in tiers_data]
        if len(levels) != len(set(levels)):
            raise serializers.ValidationError("层级编号不能重复")
        
        # 验证 level 范围
        for tier in tiers_data:
            level = tier['level']
            if level < 1 or level > 10:
                raise serializers.ValidationError(f"层级 {level} 超出范围（1-10）")
        
        return tiers_data
    
    def create(self, validated_data):
        """批量创建层级"""
        plan = self.context.get('plan')
        if not plan:
            raise serializers.ValidationError("缺少计划上下文")
        
        tiers_data = validated_data['tiers']
        created_tiers = []
        
        for tier_data in tiers_data:
            tier = CommissionPlanTier.objects.create(
                plan=plan,
                **tier_data
            )
            created_tiers.append(tier)
        
        return created_tiers


class CommissionPlanActivateSerializer(serializers.Serializer):
    """激活计划序列化器"""
    
    is_active = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        """验证激活操作（基本校验）"""
        return attrs
    
    def update(self, instance, validated_data):
        """
        更新激活状态（原子操作）
        
        ⚠️ 保证同站点同名仅一个激活版本：
        1. 在事务中先停用其他版本
        2. 再激活当前版本
        """
        from django.db import transaction
        
        is_active = validated_data.get('is_active', True)
        
        if is_active:
            # 原子操作：停用其他版本，激活当前版本
            with transaction.atomic():
                # 停用同站点同名的其他激活版本
                CommissionPlan.objects.filter(
                    site_id=instance.site_id,
                    name=instance.name,
                    is_active=True
                ).exclude(
                    plan_id=instance.plan_id
                ).update(is_active=False)
                
                # 激活当前版本
                instance.is_active = True
                instance.save(update_fields=['is_active', 'updated_at'])
        else:
            # 停用当前版本
            instance.is_active = False
            instance.save(update_fields=['is_active', 'updated_at'])
        
        return instance


class CommissionPlanListSerializer(serializers.ModelSerializer):
    """佣金计划列表序列化器（精简）"""
    
    tiers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CommissionPlan
        fields = [
            'plan_id',
            'name',
            'version',
            'mode',
            'is_active',
            'effective_from',
            'effective_to',
            'tiers_count',
            'created_at',
        ]
    
    def get_tiers_count(self, obj):
        """获取层级数量"""
        return obj.tiers.count()

