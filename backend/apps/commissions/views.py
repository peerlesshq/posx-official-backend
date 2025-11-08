"""
佣金统计API

⭐ Phase D: 统计API完善
- 分页支持（DRF标准）
- Decimal字符串化（2位小数）
- 查询优化（select_related）
"""
from decimal import Decimal
from django.db.models import Sum, Q, Count
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.commissions.models import Commission


@api_view(['GET'])
def commission_stats_view(request):
    """
    获取当前用户的佣金统计
    
    ⭐ Phase D 修正：
    - Decimal字段转字符串（2位小数）
    - 避免JSON序列化错误
    
    Returns:
        {
            "total_earned": "1234.56",    # 总佣金
            "hold": "123.45",              # 锁定中
            "ready": "567.89",             # 可结算
            "paid": "543.22",              # 已支付
            "count": 42                    # 佣金记录数
        }
    """
    stats = Commission.objects.filter(
        agent=request.user
    ).aggregate(
        total_earned=Sum('commission_amount_usd'),
        hold=Sum('commission_amount_usd', filter=Q(status='hold')),
        ready=Sum('commission_amount_usd', filter=Q(status='ready')),
        paid=Sum('commission_amount_usd', filter=Q(status='paid')),
        count=Count('commission_id')
    )
    
    # ⭐ Decimal转字符串（2位小数）
    for key in ['total_earned', 'hold', 'ready', 'paid']:
        value = stats.get(key) or Decimal('0')
        stats[key] = f"{value:.2f}"  # 格式化为2位小数字符串
    
    return Response(stats)


@api_view(['GET'])
def commission_list_view(request):
    """
    获取当前用户的佣金列表
    
    ⭐ Phase D 修正：
    - 使用DRF分页
    - Decimal字段序列化处理
    - 查询优化
    
    Query Params:
        - page: 页码
        - page_size: 每页数量（默认20）
        - status: 过滤状态
        - ordering: 排序字段
    
    Returns:
        {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [佣金列表]
        }
    """
    # 查询（使用select_related优化）
    queryset = Commission.objects.filter(
        agent=request.user
    ).select_related('order', 'order__site').order_by('-created_at')
    
    # 状态过滤
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # ⭐ DRF标准分页
    paginator = PageNumberPagination()
    paginator.page_size = int(request.query_params.get('page_size', 20))
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    
    # 序列化（手动处理Decimal）⭐
    results = []
    for commission in paginated_queryset:
        results.append({
            'commission_id': str(commission.commission_id),
            'order_id': str(commission.order_id),
            'level': commission.level,
            'rate_percent': f"{commission.rate_percent:.2f}",  # ⭐ Decimal→str
            'commission_amount_usd': f"{commission.commission_amount_usd:.2f}",  # ⭐ 2位小数
            'status': commission.status,
            'hold_until': commission.hold_until.isoformat() if commission.hold_until else None,
            'paid_at': commission.paid_at.isoformat() if commission.paid_at else None,
            'created_at': commission.created_at.isoformat()
        })
    
    return paginator.get_paginated_response(results)

