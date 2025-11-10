"""
Vesting API 视图（Retool 对接）
"""
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status

from apps.vesting.models import VestingRelease, VestingSchedule
from apps.vesting.serializers import VestingReleaseListSerializer, VestingScheduleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_vesting_releases(request):
    """
    GET /api/v1/vesting-releases
    
    Query params:
    - status: locked|unlocked|processing|released
    - page: int
    - page_size: int（默认50，最大100）
    - from: date（YYYY-MM-DD）
    - to: date（YYYY-MM-DD）
    
    ⭐ Retool 对接：包含 user_email, chain, token_decimals
    """
    site_code = request.headers.get('X-Site-Code')
    
    if not site_code:
        return Response(
            {'error': 'Missing X-Site-Code header'},
            status=http_status.HTTP_400_BAD_REQUEST
        )
    
    # 基础查询（带 RLS）
    queryset = VestingRelease.objects.filter(
        schedule__allocation__order__site__code=site_code
    )
    
    # 过滤
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    from_date = request.GET.get('from')
    if from_date:
        queryset = queryset.filter(release_date__gte=from_date)
    
    to_date = request.GET.get('to')
    if to_date:
        queryset = queryset.filter(release_date__lte=to_date)
    
    # ⭐ 优化查询（一次性加载所有关联）
    queryset = queryset.select_related(
        'schedule',
        'schedule__allocation',
        'schedule__allocation__order',
        'schedule__allocation__order__site',
        'schedule__allocation__order__buyer',  # ⭐ 为 user_email 预加载
    ).order_by('-created_at')
    
    # 分页
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 50))
    
    # 限制 page_size
    if page_size < 1:
        page_size = 50
    elif page_size > 100:
        page_size = 100
    
    start = (page - 1) * page_size
    end = start + page_size
    
    total = queryset.count()
    results = queryset[start:end]
    
    # ⭐ 使用新序列化器
    serializer = VestingReleaseListSerializer(results, many=True)
    
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'page_size': page_size,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_stuck_releases_stats(request):
    """
    GET /api/v1/admin/vesting/releases/stuck-stats
    
    返回卡在 processing 超过 15 分钟的 release 统计
    
    ⭐ Retool 守护任务对接
    """
    site_code = request.headers.get('X-Site-Code')
    
    stuck_threshold = timezone.now() - timedelta(minutes=15)
    
    # 查询卡住的 releases
    queryset = VestingRelease.objects.filter(
        status='processing',
        updated_at__lt=stuck_threshold
    )
    
    # 如果指定站点，过滤
    if site_code:
        queryset = queryset.filter(
            schedule__allocation__order__site__code=site_code
        )
    
    queryset = queryset.select_related('schedule__allocation__order')
    
    oldest = queryset.order_by('updated_at').first()
    
    return Response({
        'stuck_count': queryset.count(),
        'oldest_stuck_at': oldest.updated_at.isoformat() if oldest else None,
        'stuck_releases': [
            {
                'release_id': str(r.release_id),
                'period_no': r.period_no,
                'fireblocks_tx_id': r.fireblocks_tx_id,
                'stuck_minutes': int((timezone.now() - r.updated_at).total_seconds() / 60),
                'order_id': str(r.schedule.allocation.order.order_id),
            }
            for r in queryset[:10]  # 最多返回 10 条
        ]
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_reconcile(request):
    """
    POST /api/v1/admin/vesting/releases/reconcile
    
    立即触发对账任务（异步）
    
    ⭐ Retool 守护任务对接
    """
    from apps.vesting.tasks import reconcile_stuck_releases
    
    # 异步触发 Celery 任务
    task = reconcile_stuck_releases.delay()
    
    return Response({
        'status': 'triggered',
        'task_id': task.id,
        'message': '对账任务已触发，预计5分钟内完成'
    })

