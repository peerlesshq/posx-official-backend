"""
Commission API Serializers and Views

⭐ Phase D P0: 
- 分页支持
- Decimal字符串化
- 统计聚合API
"""
from decimal import Decimal
from rest_framework import serializers, viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Q
from django_filters.rest_framework import DjangoFilterBackend

from apps.commissions.models import Commission


class CommissionSerializer(serializers.ModelSerializer):
    """
    佣金序列化器
    
    ⭐ Phase D P0: Decimal自动字符串化
    """
    commission_amount_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,  # ⭐ 展示2位小数
        coerce_to_string=True  # ⭐ 转换为字符串，避免精度问题
    )
    rate_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        coerce_to_string=True
    )
    
    order_amount = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Commission
        fields = [
            'commission_id',
            'order',
            'agent',
            'agent_name',
            'level',
            'rate_percent',
            'commission_amount_usd',
            'order_amount',
            'status',
            'hold_until',
            'paid_at',
            'created_at',
        ]
        read_only_fields = ['commission_id', 'created_at']
    
    def get_order_amount(self, obj):
        """获取订单金额"""
        return f"{obj.order.final_price_usd:.2f}"
    
    def get_agent_name(self, obj):
        """获取代理名称"""
        return obj.agent.email or f"Agent_{obj.agent.user_id}"


class CommissionPagination(PageNumberPagination):
    """
    佣金分页器
    
    ⭐ Phase D P0: 标准分页配置
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    佣金查询 ViewSet（只读）
    
    ⭐ Phase D P0: 
    - 分页支持
    - 过滤和排序
    - 统计API
    """
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CommissionPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'level']
    ordering_fields = ['created_at', 'commission_amount_usd', 'hold_until']
    ordering = ['-created_at']  # ⭐ 默认按创建时间倒序
    
    def get_queryset(self):
        """
        仅返回当前用户的佣金
        
        ⭐ RLS在Order表生效，Commission通过order.site_id间接隔离
        """
        return Commission.objects.filter(
            agent=self.request.user
        ).select_related('order', 'agent')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        佣金统计API
        
        ⭐ Phase D P0: Decimal字符串化（2位小数）
        
        GET /api/v1/commissions/stats/
        
        Response:
        {
            "total_earned": "1234.56",
            "hold": "123.45",
            "ready": "567.89",
            "paid": "543.22"
        }
        """
        queryset = self.get_queryset()
        
        stats = queryset.aggregate(
            total_earned=Sum('commission_amount_usd'),
            hold=Sum('commission_amount_usd', filter=Q(status=Commission.STATUS_HOLD)),
            ready=Sum('commission_amount_usd', filter=Q(status=Commission.STATUS_READY)),
            paid=Sum('commission_amount_usd', filter=Q(status=Commission.STATUS_PAID)),
        )
        
        # ⭐ Decimal 转字符串（2位小数）
        for key in stats:
            value = stats[key] or Decimal('0')
            stats[key] = f"{value:.2f}"
        
        return Response(stats)

