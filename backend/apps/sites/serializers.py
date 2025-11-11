"""
Site Serializers（站点配置序列化器）

⭐ 权限：IsAdminUser（超级管理员）
⭐ 用途：前端可视化管理站点
"""
from rest_framework import serializers
from .models import Site, ChainAssetConfig


class SiteSerializer(serializers.ModelSerializer):
    """站点序列化器（完整字段）"""
    
    class Meta:
        model = Site
        fields = [
            'site_id',
            'code',
            'name',
            'domain',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['site_id', 'created_at']
    
    def validate_code(self, value):
        """
        验证站点代码
        
        规则：
        - 大写字母
        - 长度 2-20
        - 唯一性
        """
        if not value:
            raise serializers.ValidationError("站点代码不能为空")
        
        # 转换为大写
        value = value.upper()
        
        # 验证长度
        if len(value) < 2 or len(value) > 20:
            raise serializers.ValidationError("站点代码长度必须在 2-20 之间")
        
        # 验证字符（仅允许字母、数字、下划线、连字符）
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("站点代码只能包含字母、数字、下划线、连字符")
        
        # 验证唯一性（更新时排除自身）
        existing = Site.objects.filter(code=value)
        if self.instance:
            existing = existing.exclude(site_id=self.instance.site_id)
        
        if existing.exists():
            raise serializers.ValidationError(f"站点代码 '{value}' 已存在")
        
        return value
    
    def validate_domain(self, value):
        """
        验证域名
        
        规则：
        - 非空
        - 唯一性
        """
        if not value:
            raise serializers.ValidationError("域名不能为空")
        
        # 验证唯一性（更新时排除自身）
        existing = Site.objects.filter(domain=value)
        if self.instance:
            existing = existing.exclude(site_id=self.instance.site_id)
        
        if existing.exists():
            raise serializers.ValidationError(f"域名 '{value}' 已存在")
        
        return value


class SiteListSerializer(serializers.ModelSerializer):
    """站点列表序列化器（精简字段）"""
    
    class Meta:
        model = Site
        fields = [
            'site_id',
            'code',
            'name',
            'domain',
            'is_active',
            'created_at',
        ]


class ChainAssetConfigSerializer(serializers.ModelSerializer):
    """链资产配置序列化器"""
    
    site_code = serializers.CharField(source='site.code', read_only=True)
    
    class Meta:
        model = ChainAssetConfig
        fields = [
            'config_id',
            'site',
            'site_code',
            'chain',
            'token_symbol',
            'token_decimals',
            'fireblocks_asset_id',
            'fireblocks_vault_id',
            'address_type',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['config_id', 'site_code', 'created_at']
    
    def validate_token_decimals(self, value):
        """验证代币小数位"""
        if value < 0 or value > 18:
            raise serializers.ValidationError("代币小数位必须在 0-18 之间")
        return value

