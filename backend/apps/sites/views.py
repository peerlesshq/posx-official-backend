"""
Site Views（站点配置视图）

⭐ 端点：
- GET /api/v1/admin/sites/ - 站点列表
- POST /api/v1/admin/sites/ - 创建站点
- GET /api/v1/admin/sites/{id}/ - 站点详情
- PUT /api/v1/admin/sites/{id}/ - 更新站点
- PATCH /api/v1/admin/sites/{id}/ - 部分更新
- DELETE /api/v1/admin/sites/{id}/ - 软删除（设置 is_active=False）

⭐ 权限：
- 所有端点：IsAdminUser（超级管理员）
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count

from .models import Site, ChainAssetConfig
from .serializers import SiteSerializer, SiteListSerializer, ChainAssetConfigSerializer

logger = logging.getLogger(__name__)


class SiteViewSet(viewsets.ModelViewSet):
    """
    站点配置视图集
    
    功能：
    - 创建/查询/更新站点
    - 软删除（设置 is_active=False）
    - 站点统计信息
    """
    
    queryset = Site.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'site_id'
    lookup_url_kwarg = 'id'
    
    def get_serializer_class(self):
        """根据操作返回不同序列化器"""
        if self.action == 'list':
            return SiteListSerializer
        return SiteSerializer
    
    def get_queryset(self):
        """获取查询集（支持过滤）"""
        queryset = super().get_queryset()
        
        # 过滤：激活状态
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 过滤：代码搜索
        code = self.request.query_params.get('code')
        if code:
            queryset = queryset.filter(code__icontains=code.upper())
        
        # 排序
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed_orderings = ['code', '-code', 'name', '-name', 'created_at', '-created_at']
        
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        """创建站点（记录日志）"""
        site = serializer.save()
        
        logger.info(
            f"Created site: {site.code}",
            extra={
                'site_id': str(site.site_id),
                'site_code': site.code,
                'site_name': site.name,
                'admin': self.request.user.email
            }
        )
    
    def perform_update(self, serializer):
        """更新站点（记录日志）"""
        site = serializer.save()
        
        logger.info(
            f"Updated site: {site.code}",
            extra={
                'site_id': str(site.site_id),
                'site_code': site.code,
                'admin': self.request.user.email
            }
        )
    
    def perform_destroy(self, instance):
        """软删除站点（设置 is_active=False）"""
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        
        logger.warning(
            f"Deactivated site: {instance.code}",
            extra={
                'site_id': str(instance.site_id),
                'site_code': instance.code,
                'admin': self.request.user.email
            }
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, id=None):
        """
        激活站点
        
        POST /api/v1/admin/sites/{id}/activate/
        """
        site = self.get_object()
        site.is_active = True
        site.save(update_fields=['is_active'])
        
        logger.info(
            f"Activated site: {site.code}",
            extra={
                'site_id': str(site.site_id),
                'site_code': site.code,
                'admin': request.user.email
            }
        )
        
        return Response({
            'message': f'站点 "{site.code}" 已激活',
            'site_id': str(site.site_id)
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, id=None):
        """
        站点统计信息
        
        GET /api/v1/admin/sites/{id}/stats/
        
        返回：
        - 订单数
        - 产品数
        - 代理数
        - 佣金总额等
        """
        site = self.get_object()
        
        from apps.orders.models import Order
        from apps.tiers.models import Tier
        from apps.agents.models import AgentProfile
        from apps.commissions.models import Commission
        from decimal import Decimal
        
        stats = {
            'site_id': str(site.site_id),
            'site_code': site.code,
            'site_name': site.name,
            'is_active': site.is_active,
            'orders': {
                'total': Order.objects.filter(site=site).count(),
                'paid': Order.objects.filter(site=site, status='paid').count(),
                'pending': Order.objects.filter(site=site, status='pending').count(),
            },
            'tiers': {
                'total': Tier.objects.filter(site=site).count(),
                'active': Tier.objects.filter(site=site, is_active=True).count(),
            },
            'agents': {
                'total': AgentProfile.objects.filter(site=site).count(),
                'active': AgentProfile.objects.filter(site=site, is_active=True).count(),
            },
            'commissions': {
                'total_count': Commission.objects.filter(order__site=site).count(),
                'total_amount': str(
                    Commission.objects.filter(order__site=site).aggregate(
                        total=models.Sum('commission_amount_usd')
                    )['total'] or Decimal('0')
                ),
            }
        }
        
        return Response(stats)


class ChainAssetConfigViewSet(viewsets.ModelViewSet):
    """
    链资产配置视图集
    
    功能：
    - 创建/查询/更新链资产配置
    - 按站点过滤
    """
    
    queryset = ChainAssetConfig.objects.all()
    serializer_class = ChainAssetConfigSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'config_id'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        """获取查询集（支持过滤）"""
        queryset = super().get_queryset().select_related('site')
        
        # 过滤：站点
        site_code = self.request.query_params.get('site_code')
        if site_code:
            queryset = queryset.filter(site__code=site_code.upper())
        
        # 过滤：链
        chain = self.request.query_params.get('chain')
        if chain:
            queryset = queryset.filter(chain=chain.upper())
        
        # 过滤：激活状态
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('site__code', 'chain', 'token_symbol')
    
    def perform_create(self, serializer):
        """创建资产配置（记录日志）"""
        config = serializer.save()
        
        logger.info(
            f"Created chain asset config: {config.chain} {config.token_symbol}",
            extra={
                'config_id': str(config.config_id),
                'site_code': config.site.code,
                'chain': config.chain,
                'token_symbol': config.token_symbol,
                'admin': self.request.user.email
            }
        )
    
    def perform_update(self, serializer):
        """更新资产配置（记录日志）"""
        config = serializer.save()
        
        logger.info(
            f"Updated chain asset config: {config.chain} {config.token_symbol}",
            extra={
                'config_id': str(config.config_id),
                'admin': self.request.user.email
            }
        )

