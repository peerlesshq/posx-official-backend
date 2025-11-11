"""
Allocation Views

⭐ API 端点：
1. GET /api/v1/allocations/ - 分配记录列表（用户）
2. GET /api/v1/allocations/{id}/ - 分配记录详情
3. GET /api/v1/allocations/balance/ - 代币余额统计
"""
import logging
from decimal import Decimal
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Allocation
from .serializers import (
    AllocationSerializer,
    AllocationListSerializer,
    AllocationBalanceSerializer,
)

logger = logging.getLogger(__name__)


class AllocationPagination(PageNumberPagination):
    """分配记录分页配置"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AllocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    代币分配视图集
    
    ⚠️ 权限：IsAuthenticated
    ⚠️ 过滤：
    - RLS 自动过滤 site_id（通过 order.site_id）
    - 应用层过滤 buyer（只能查看自己的分配记录）
    
    查询参数：
    - ?status=active - 按状态过滤
    - ?wallet_address=0x... - 按钱包地址过滤
    """
    permission_classes = [IsAuthenticated]
    pagination_class = AllocationPagination
    
    def get_queryset(self):
        """
        获取查询集
        
        过滤规则：
        1. 只返回当前用户的分配记录（order.buyer = 当前用户）
        2. 通过 order 关联，RLS 自动过滤 site_id
        3. 按创建时间倒序
        """
        user = self.request.user
        
        queryset = Allocation.objects.filter(
            order__buyer=user
        ).select_related(
            'order'
        ).order_by('-created_at')
        
        # 查询参数过滤
        status_filter = self.request.query_params.get('status')
        wallet_address = self.request.query_params.get('wallet_address')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if wallet_address:
            # 统一为 lowercase
            queryset = queryset.filter(wallet_address=wallet_address.lower())
        
        return queryset
    
    def get_serializer_class(self):
        """根据 action 选择序列化器"""
        if self.action == 'list':
            return AllocationListSerializer
        return AllocationSerializer
    
    @action(detail=False, methods=['get'], url_path='balance')
    def balance(self, request):
        """
        代币余额统计
        
        返回当前用户的代币余额汇总：
        - total_tokens: 总代币数量
        - released_tokens: 已释放代币
        - pending_tokens: 待释放代币
        - active_allocations: 活跃分配记录数
        - completed_allocations: 已完成分配记录数
        - release_progress: 总体释放进度
        
        示例：
        {
            "total_tokens": "1000000.000000",
            "released_tokens": "100000.000000",
            "pending_tokens": "900000.000000",
            "active_allocations": 5,
            "completed_allocations": 2,
            "release_progress": "10.00"
        }
        """
        user = request.user
        
        # 查询用户所有分配记录
        allocations = Allocation.objects.filter(order__buyer=user)
        
        # 聚合统计
        stats = allocations.aggregate(
            total=Sum('token_amount'),
            released=Sum('released_tokens'),
            active_count=Count('allocation_id', filter=Q(status=Allocation.STATUS_ACTIVE)),
            completed_count=Count('allocation_id', filter=Q(status=Allocation.STATUS_COMPLETED)),
        )
        
        total_tokens = stats['total'] or Decimal('0')
        released_tokens = stats['released'] or Decimal('0')
        pending_tokens = total_tokens - released_tokens
        active_allocations = stats['active_count'] or 0
        completed_allocations = stats['completed_count'] or 0
        
        # 计算释放进度
        if total_tokens > 0:
            progress = (released_tokens / total_tokens) * 100
            release_progress = f"{progress:.2f}"
        else:
            release_progress = "0.00"
        
        data = {
            'total_tokens': total_tokens,
            'released_tokens': released_tokens,
            'pending_tokens': pending_tokens,
            'active_allocations': active_allocations,
            'completed_allocations': completed_allocations,
            'release_progress': release_progress,
        }
        
        serializer = AllocationBalanceSerializer(data)
        return Response(serializer.data)

