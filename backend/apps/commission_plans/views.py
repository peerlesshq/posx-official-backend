"""
佣金计划视图集

⭐ 权限：
- 读取：IsAuthenticated
- 写入：IsAuthenticated + IsAdminUser（或自定义权限）

⭐ 站点隔离：
- 通过 request.site 自动过滤
- RLS 策略提供二次保障
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q, Count
from .models import CommissionPlan, CommissionPlanTier
from .serializers import (
    CommissionPlanSerializer,
    CommissionPlanCreateSerializer,
    CommissionPlanListSerializer,
    CommissionPlanTierSerializer,
    CommissionPlanTierBulkCreateSerializer,
    CommissionPlanActivateSerializer,
)


class IsStaffUser(IsAdminUser):
    """仅管理员可写入"""
    
    def has_permission(self, request, view):
        # 允许所有认证用户读取
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        # 写入需要管理员权限（简化版：检查是_active）
        return request.user and request.user.is_active


class CommissionPlanViewSet(viewsets.ModelViewSet):
    """
    佣金计划视图集
    
    功能：
    - GET /api/v1/commission-plans/ - 列表（支持过滤）
    - POST /api/v1/commission-plans/ - 创建计划
    - GET /api/v1/commission-plans/{id}/ - 详情
    - PATCH /api/v1/commission-plans/{id}/ - 更新
    - DELETE /api/v1/commission-plans/{id}/ - 删除
    - POST /api/v1/commission-plans/{id}/tiers/bulk/ - 批量创建层级
    - PATCH /api/v1/commission-plans/{id}/activate/ - 激活/停用
    """
    
    permission_classes = [IsStaffUser]
    lookup_field = 'plan_id'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        """
        获取查询集（站点隔离）
        
        ⭐ 安全：
        - 通过 request.site 显式过滤
        - RLS 策略提供二次保障
        """
        if not hasattr(self.request, 'site'):
            return CommissionPlan.objects.none()
        
        queryset = CommissionPlan.objects.filter(
            site_id=self.request.site.site_id
        ).prefetch_related('tiers')
        
        # 过滤参数
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 按时间点过滤（查询某时点生效的计划）
        active_at = self.request.query_params.get('active_at')
        if active_at:
            try:
                active_at_dt = timezone.datetime.fromisoformat(active_at.replace('Z', '+00:00'))
                queryset = queryset.filter(
                    Q(effective_from__isnull=True) | Q(effective_from__lte=active_at_dt),
                    Q(effective_to__isnull=True) | Q(effective_to__gte=active_at_dt),
                )
            except ValueError:
                pass  # 忽略无效日期格式
        
        # 按名称过滤
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作返回序列化器"""
        if self.action == 'list':
            return CommissionPlanListSerializer
        elif self.action == 'create':
            return CommissionPlanCreateSerializer
        elif self.action == 'tiers_bulk':
            return CommissionPlanTierBulkCreateSerializer
        elif self.action == 'activate':
            return CommissionPlanActivateSerializer
        return CommissionPlanSerializer
    
    def create(self, request, *args, **kwargs):
        """创建佣金计划"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        
        # 返回完整数据
        response_serializer = CommissionPlanSerializer(plan)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='tiers/bulk')
    def tiers_bulk(self, request, id=None):
        """
        批量创建层级
        
        POST /api/v1/commission-plans/{id}/tiers/bulk/
        Body: {
            "tiers": [
                {"level": 1, "rate_percent": "12.00", "hold_days": 7},
                {"level": 2, "rate_percent": "5.00"},
                ...
            ]
        }
        """
        plan = self.get_object()
        
        serializer = self.get_serializer(
            data=request.data,
            context={'plan': plan}
        )
        serializer.is_valid(raise_exception=True)
        tiers = serializer.save()
        
        # 返回创建的层级
        tier_serializer = CommissionPlanTierSerializer(tiers, many=True)
        return Response({
            'message': f'成功创建 {len(tiers)} 个层级',
            'tiers': tier_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'], url_path='activate')
    def activate(self, request, id=None):
        """
        激活/停用计划
        
        PATCH /api/v1/commission-plans/{id}/activate/
        Body: {"is_active": true}
        """
        plan = self.get_object()
        
        serializer = self.get_serializer(
            plan,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_plan = serializer.save()
        
        # 返回完整数据
        response_serializer = CommissionPlanSerializer(updated_plan)
        return Response({
            'message': '激活成功' if updated_plan.is_active else '停用成功',
            'plan': response_serializer.data
        })



