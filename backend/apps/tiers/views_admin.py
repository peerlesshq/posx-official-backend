"""
Tier Admin Views（产品配置管理视图）

⭐ 端点：
- POST /api/v1/admin/tiers/ - 创建产品
- PUT /api/v1/admin/tiers/{id}/ - 更新产品
- PATCH /api/v1/admin/tiers/{id}/ - 部分更新
- DELETE /api/v1/admin/tiers/{id}/ - 软删除
- POST /api/v1/admin/tiers/{id}/adjust-inventory/ - 调整库存

⭐ 权限：
- 所有端点：IsAdminUser（超级管理员）
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db import transaction
from django.db.models import F
from decimal import Decimal

from .models import Tier
from .serializers_admin import (
    TierCreateSerializer,
    TierUpdateSerializer,
    TierAdjustInventorySerializer,
    TierAdminDetailSerializer,
)

logger = logging.getLogger(__name__)


class TierAdminViewSet(viewsets.ModelViewSet):
    """
    产品配置管理视图集
    
    功能：
    - 创建/查询/更新产品
    - 软删除（设置 is_active=False）
    - 调整库存
    """
    
    queryset = Tier.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'tier_id'
    lookup_url_kwarg = 'id'
    
    def get_serializer_class(self):
        """根据操作返回不同序列化器"""
        if self.action == 'create':
            return TierCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TierUpdateSerializer
        elif self.action == 'adjust_inventory':
            return TierAdjustInventorySerializer
        return TierAdminDetailSerializer
    
    def get_queryset(self):
        """
        获取查询集（支持过滤）
        
        ⭐ 管理员可查看所有站点的产品
        """
        queryset = super().get_queryset().select_related('site')
        
        # 过滤：站点
        site_code = self.request.query_params.get('site_code')
        if site_code:
            queryset = queryset.filter(site__code=site_code.upper())
        else:
            # 默认按当前站点过滤（如果有）
            if hasattr(self.request, 'site'):
                queryset = queryset.filter(site=self.request.site)
        
        # 过滤：激活状态
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 过滤：库存状态
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'sold_out':
            queryset = queryset.filter(available_units=0)
        elif stock_status == 'low_stock':
            # 库存低于10%
            queryset = queryset.filter(
                available_units__gt=0,
                available_units__lte=F('total_units') * 0.1
            )
        elif stock_status == 'in_stock':
            queryset = queryset.filter(available_units__gt=0)
        
        # 排序
        ordering = self.request.query_params.get('ordering', 'display_order')
        allowed_orderings = [
            'display_order', '-display_order',
            'list_price_usd', '-list_price_usd',
            'created_at', '-created_at',
            'sold_units', '-sold_units'
        ]
        
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('display_order')
        
        return queryset
    
    def perform_create(self, serializer):
        """创建产品（记录日志）"""
        tier = serializer.save()
        
        logger.info(
            f"Created tier: {tier.name}",
            extra={
                'tier_id': str(tier.tier_id),
                'site_code': tier.site.code,
                'tier_name': tier.name,
                'price': str(tier.list_price_usd),
                'total_units': tier.total_units,
                'admin': self.request.user.email
            }
        )
    
    def perform_update(self, serializer):
        """更新产品（记录日志）"""
        tier = serializer.save()
        
        logger.info(
            f"Updated tier: {tier.name}",
            extra={
                'tier_id': str(tier.tier_id),
                'tier_name': tier.name,
                'admin': self.request.user.email
            }
        )
    
    def perform_destroy(self, instance):
        """软删除产品（设置 is_active=False）"""
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        
        logger.warning(
            f"Deactivated tier: {instance.name}",
            extra={
                'tier_id': str(instance.tier_id),
                'tier_name': instance.name,
                'admin': self.request.user.email
            }
        )
    
    @action(detail=True, methods=['post'])
    def adjust_inventory(self, request, id=None):
        """
        调整库存
        
        POST /api/v1/admin/tiers/{id}/adjust-inventory/
        Body:
        {
            "adjustment": 1000,  // 正数=增加，负数=减少
            "reason": "补货" // 可选
        }
        """
        tier = self.get_object()
        
        serializer = self.get_serializer(
            data=request.data,
            context={'tier': tier}
        )
        serializer.is_valid(raise_exception=True)
        
        adjustment = serializer.validated_data['adjustment']
        reason = serializer.validated_data.get('reason', '')
        
        # 原子性更新
        with transaction.atomic():
            # 使用 select_for_update 防止并发问题
            tier = Tier.objects.select_for_update().get(tier_id=tier.tier_id)
            
            old_total = tier.total_units
            old_available = tier.available_units
            
            # 更新库存
            tier.total_units += adjustment
            tier.available_units += adjustment
            tier.save(update_fields=['total_units', 'available_units', 'updated_at'])
        
        logger.info(
            f"Adjusted tier inventory: {tier.name}",
            extra={
                'tier_id': str(tier.tier_id),
                'tier_name': tier.name,
                'adjustment': adjustment,
                'old_total': old_total,
                'new_total': tier.total_units,
                'old_available': old_available,
                'new_available': tier.available_units,
                'reason': reason,
                'admin': request.user.email
            }
        )
        
        return Response({
            'message': f'库存调整成功',
            'tier_id': str(tier.tier_id),
            'adjustment': adjustment,
            'old_inventory': {
                'total': old_total,
                'available': old_available,
            },
            'new_inventory': {
                'total': tier.total_units,
                'available': tier.available_units,
            }
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, id=None):
        """
        激活产品
        
        POST /api/v1/admin/tiers/{id}/activate/
        """
        tier = self.get_object()
        tier.is_active = True
        tier.save(update_fields=['is_active', 'updated_at'])
        
        logger.info(
            f"Activated tier: {tier.name}",
            extra={
                'tier_id': str(tier.tier_id),
                'tier_name': tier.name,
                'admin': request.user.email
            }
        )
        
        return Response({
            'message': f'产品 "{tier.name}" 已激活',
            'tier_id': str(tier.tier_id)
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, id=None):
        """
        产品统计信息
        
        GET /api/v1/admin/tiers/{id}/stats/
        
        返回：
        - 销售统计
        - 收入统计
        - 库存状态等
        """
        tier = self.get_object()
        
        from apps.orders.models import Order, OrderItem
        
        # 统计订单数量
        order_items = OrderItem.objects.filter(tier=tier).select_related('order')
        
        total_orders = order_items.count()
        paid_orders = order_items.filter(order__status='paid').count()
        pending_orders = order_items.filter(order__status='pending').count()
        
        # 统计收入
        total_revenue = Decimal('0')
        paid_revenue = Decimal('0')
        
        for item in order_items:
            if item.order.status == 'paid':
                paid_revenue += item.order.final_price_usd
            total_revenue += item.order.final_price_usd
        
        # 库存状态
        stock_percentage = 0
        if tier.total_units > 0:
            stock_percentage = round((tier.available_units / tier.total_units) * 100, 2)
        
        stats = {
            'tier_id': str(tier.tier_id),
            'tier_name': tier.name,
            'orders': {
                'total': total_orders,
                'paid': paid_orders,
                'pending': pending_orders,
            },
            'revenue': {
                'total': str(total_revenue),
                'paid': str(paid_revenue),
            },
            'inventory': {
                'total': tier.total_units,
                'sold': tier.sold_units,
                'available': tier.available_units,
                'stock_percentage': stock_percentage,
            }
        }
        
        return Response(stats)

