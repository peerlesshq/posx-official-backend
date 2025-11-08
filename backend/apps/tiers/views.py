"""
档位视图

⭐ 端点：
- GET /api/v1/tiers/ - 列表（分页 + 过滤）
- GET /api/v1/tiers/{id}/ - 详情

⭐ 权限：
- 所有端点：IsAuthenticated
- 站点隔离：自动通过request.site过滤
"""
import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal

from .models import Tier
from .serializers import TierSerializer, TierListSerializer

logger = logging.getLogger(__name__)


class TierViewSet(viewsets.ReadOnlyModelViewSet):
    """
    档位视图集（只读）
    
    功能：
    - GET /api/v1/tiers/ - 列表
    - GET /api/v1/tiers/{id}/ - 详情
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'tier_id'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        """
        获取查询集（站点隔离）
        
        ⭐ 安全：
        - 通过 request.site 显式过滤
        - RLS 策略提供二次保障
        """
        if not hasattr(self.request, 'site'):
            return Tier.objects.none()
        
        queryset = Tier.objects.filter(
            site=self.request.site
        ).select_related('site')
        
        # 过滤参数
        
        # 1. 激活状态
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 2. 仅可用（库存 > 0）
        available_only = self.request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(available_units__gt=0)
        
        # 3. 价格范围
        price_min = self.request.query_params.get('price_min')
        if price_min:
            try:
                price_min_decimal = Decimal(price_min)
                queryset = queryset.filter(list_price_usd__gte=price_min_decimal)
            except (ValueError, TypeError):
                pass
        
        price_max = self.request.query_params.get('price_max')
        if price_max:
            try:
                price_max_decimal = Decimal(price_max)
                queryset = queryset.filter(list_price_usd__lte=price_max_decimal)
            except (ValueError, TypeError):
                pass
        
        # 4. 排序
        ordering = self.request.query_params.get('ordering', 'display_order')
        allowed_orderings = ['display_order', '-display_order', 'list_price_usd', '-list_price_usd', 'created_at', '-created_at']
        
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('display_order')
        
        return queryset
    
    def get_serializer_class(self):
        """根据动作返回序列化器"""
        if self.action == 'list':
            return TierListSerializer
        return TierSerializer


