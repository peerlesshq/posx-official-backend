"""
核心 Mixins

⭐ 功能：
- SiteScopedViewSetMixin: 自动过滤 site_id
- SiteScopedSerializerMixin: 自动注入 site_id

使用示例：
>>> class MyViewSet(SiteScopedViewSetMixin, viewsets.ModelViewSet):
...     model = MyModel
...     serializer_class = MySerializer
"""
from rest_framework import serializers as drf_serializers


class SiteScopedViewSetMixin:
    """
    站点作用域 ViewSet Mixin
    
    自动功能：
    - 过滤当前站点的数据
    - 需要模型有 site 或 site_id 字段
    """
    
    def get_queryset(self):
        """重写get_queryset，自动过滤站点"""
        queryset = super().get_queryset()
        
        # 检查request.site
        if not hasattr(self.request, 'site'):
            return queryset.none()
        
        # 根据模型字段类型过滤
        model = queryset.model
        
        if hasattr(model, 'site'):
            # ForeignKey到Site
            return queryset.filter(site=self.request.site)
        elif hasattr(model, 'site_id'):
            # UUIDField
            return queryset.filter(site_id=self.request.site.site_id)
        else:
            # 无站点字段，返回全部（如全局表）
            return queryset


class SiteScopedSerializerMixin:
    """
    站点作用域 Serializer Mixin
    
    自动功能：
    - 创建时注入 site 或 site_id
    - 需要在 context 中传入 request
    """
    
    def create(self, validated_data):
        """重写create，自动注入站点"""
        request = self.context.get('request')
        
        if request and hasattr(request, 'site'):
            model = self.Meta.model
            
            # 检查模型字段
            if hasattr(model, 'site') and 'site' not in validated_data:
                # ForeignKey到Site
                validated_data['site'] = request.site
            elif hasattr(model, 'site_id') and 'site_id' not in validated_data:
                # UUIDField
                validated_data['site_id'] = request.site.site_id
        
        return super().create(validated_data)


class ReadOnlyFieldsMixin:
    """
    只读字段 Mixin
    
    自动将指定字段设为只读
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 自动设置常见只读字段
        readonly_fields = [
            'created_at',
            'updated_at',
            'id',
            'uuid',
        ]
        
        for field_name in readonly_fields:
            if field_name in self.fields:
                self.fields[field_name].read_only = True


