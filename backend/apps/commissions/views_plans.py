"""
Commission Plan 管理视图（Phase F）
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
import logging

from apps.commissions.models import CommissionPlan, CommissionPlanTier
from apps.commissions.serializers_plans import (
    CommissionPlanSerializer,
    CommissionPlanListSerializer
)

logger = logging.getLogger(__name__)


class CommissionPlanViewSet(viewsets.ModelViewSet):
    """
    佣金方案管理 ViewSet（Phase F）
    
    权限：
    - list/retrieve: 已登录用户（查看本站点方案）
    - create/update/delete: 超级管理员
    
    端点：
    - GET /api/v1/commission-plans/ - 列表
    - POST /api/v1/commission-plans/ - 创建
    - GET /api/v1/commission-plans/{id}/ - 详情
    - PUT /api/v1/commission-plans/{id}/ - 更新
    - DELETE /api/v1/commission-plans/{id}/ - 删除
    - POST /api/v1/commission-plans/{id}/set-default/ - 设为默认
    """
    
    queryset = CommissionPlan.objects.all()
    
    def get_permissions(self):
        """根据操作设置权限"""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        """根据操作返回不同序列化器"""
        if self.action == 'list':
            return CommissionPlanListSerializer
        return CommissionPlanSerializer
    
    def get_queryset(self):
        """过滤：仅返回当前站点的方案"""
        queryset = super().get_queryset()
        
        # 管理员可查看所有站点
        if self.request.user.is_superuser:
            site_code = self.request.query_params.get('site_code')
            if site_code:
                queryset = queryset.filter(site__code=site_code)
        else:
            # 普通用户仅看当前站点
            queryset = queryset.filter(site=self.request.site)
        
        return queryset.select_related('site').prefetch_related('tiers')
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        设置为默认方案
        
        逻辑：
        1. 将当前站点的所有方案 is_default=False
        2. 将选中方案 is_default=True
        """
        plan = self.get_object()
        
        with transaction.atomic():
            # 取消当前默认
            CommissionPlan.objects.filter(
                site=plan.site,
                is_default=True
            ).update(is_default=False)
            
            # 设置新默认
            plan.is_default = True
            plan.save(update_fields=['is_default', 'updated_at'])
        
        logger.info(
            f"Set default commission plan",
            extra={
                'plan_id': str(plan.plan_id),
                'site_code': plan.site.code,
                'plan_name': plan.name,
                'admin': request.user.email
            }
        )
        
        return Response({
            'message': f'已将"{plan.name}"设为默认方案',
            'plan_id': str(plan.plan_id)
        })
    
    def perform_create(self, serializer):
        """创建方案（记录日志）"""
        plan = serializer.save()
        
        logger.info(
            f"Created commission plan",
            extra={
                'plan_id': str(plan.plan_id),
                'site_code': plan.site.code,
                'plan_name': plan.name,
                'max_levels': plan.max_levels,
                'admin': self.request.user.email
            }
        )
    
    def perform_update(self, serializer):
        """更新方案（记录日志）"""
        plan = serializer.save()
        
        logger.info(
            f"Updated commission plan",
            extra={
                'plan_id': str(plan.plan_id),
                'plan_name': plan.name,
                'admin': self.request.user.email
            }
        )
    
    def perform_destroy(self, instance):
        """删除方案（软删除）"""
        # 不真正删除，仅设置 is_active=False
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        
        logger.warning(
            f"Deactivated commission plan",
            extra={
                'plan_id': str(instance.plan_id),
                'plan_name': instance.name,
                'admin': self.request.user.email
            }
        )

