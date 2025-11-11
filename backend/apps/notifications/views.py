"""
Notification Views

⭐ API 端点：
1. GET /api/v1/notifications/ - 通知列表（分页）
2. GET /api/v1/notifications/{id}/ - 通知详情
3. PATCH /api/v1/notifications/mark-read/ - 标记已读（批量）
4. GET /api/v1/notifications/unread-count/ - 未读数统计
5. GET /api/v1/notifications/announcements/ - 公告列表（站点广播）
"""
import logging
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Notification, NotificationReadReceipt
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    MarkReadSerializer,
    UnreadCountSerializer,
)

logger = logging.getLogger(__name__)


class NotificationPagination(PageNumberPagination):
    """通知分页配置"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    通知视图集
    
    ⚠️ 权限：IsAuthenticated
    ⚠️ 过滤：
    - RLS 自动过滤 site_id
    - 应用层过滤 recipient_id（个人通知）
    - 或 recipient_type='site_broadcast'（站点广播）
    
    查询参数：
    - ?unread=true - 仅未读
    - ?category=finance - 按分类过滤
    - ?severity=high - 按严重度过滤
    """
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination
    
    def get_queryset(self):
        """
        获取查询集
        
        过滤规则：
        1. 个人通知：recipient_id = 当前用户
        2. 站点广播：recipient_type = 'site_broadcast'
        3. 未过期：expires_at IS NULL OR expires_at > NOW()
        4. 可见：visible_at <= NOW()
        """
        user = self.request.user
        now = timezone.now()
        
        # 基础查询：个人通知 OR 站点广播
        queryset = Notification.objects.filter(
            Q(recipient_id=user.user_id) |
            Q(recipient_type=Notification.RECIPIENT_SITE_BROADCAST)
        ).filter(
            # 未过期
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).filter(
            # 可见
            visible_at__lte=now
        ).order_by('-visible_at', '-created_at')
        
        # 查询参数过滤
        unread = self.request.query_params.get('unread')
        category = self.request.query_params.get('category')
        severity = self.request.query_params.get('severity')
        
        if unread == 'true':
            # 未读过滤
            # 个人通知：read_at IS NULL
            # 站点广播：不存在 NotificationReadReceipt
            queryset = queryset.filter(
                Q(recipient_id=user.user_id, read_at__isnull=True) |
                Q(
                    recipient_type=Notification.RECIPIENT_SITE_BROADCAST,
                    read_receipts__user_id__ne=user.user_id
                )
            ).distinct()
        
        if category:
            queryset = queryset.filter(category=category)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset
    
    def get_serializer_class(self):
        """根据 action 选择序列化器"""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    def get_serializer_context(self):
        """添加 user_id 到序列化器上下文"""
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.user_id
        return context
    
    @action(detail=False, methods=['patch'], url_path='mark-read')
    def mark_read(self, request):
        """
        标记已读
        
        ⭐ 批量支持：
        - 提供 notification_ids: 标记指定通知
        - 设置 mark_all=true: 标记全部未读
        
        Body:
        {
            "notification_ids": ["uuid1", "uuid2"],  // 可选
            "mark_all": false  // 可选
        }
        
        返回:
        {
            "marked_count": 5,
            "personal_count": 3,
            "broadcast_count": 2
        }
        """
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        now = timezone.now()
        
        notification_ids = serializer.validated_data.get('notification_ids')
        mark_all = serializer.validated_data.get('mark_all', False)
        
        # 获取目标通知
        queryset = Notification.objects.filter(
            Q(recipient_id=user.user_id) |
            Q(recipient_type=Notification.RECIPIENT_SITE_BROADCAST)
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).filter(
            visible_at__lte=now
        )
        
        if not mark_all:
            # 指定通知
            queryset = queryset.filter(notification_id__in=notification_ids)
        
        # 分类处理
        personal_notifications = queryset.filter(recipient_id=user.user_id, read_at__isnull=True)
        broadcast_notifications = queryset.filter(recipient_type=Notification.RECIPIENT_SITE_BROADCAST)
        
        # 标记个人通知
        personal_count = personal_notifications.update(read_at=now)
        
        # 标记站点广播（创建 ReadReceipt）
        broadcast_count = 0
        for notification in broadcast_notifications:
            _, created = NotificationReadReceipt.objects.get_or_create(
                notification=notification,
                user_id=user.user_id
            )
            if created:
                broadcast_count += 1
        
        total_count = personal_count + broadcast_count
        
        logger.info(
            f"User {user.user_id} marked {total_count} notifications as read "
            f"(personal: {personal_count}, broadcast: {broadcast_count})"
        )
        
        return Response({
            'marked_count': total_count,
            'personal_count': personal_count,
            'broadcast_count': broadcast_count,
        })
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        未读数统计
        
        返回:
        {
            "total": 15,
            "by_category": {
                "finance": 5,
                "order": 10
            },
            "by_severity": {
                "info": 10,
                "high": 5
            }
        }
        """
        user = request.user
        now = timezone.now()
        
        # 获取未读通知
        # 个人通知：read_at IS NULL
        personal_unread = Notification.objects.filter(
            recipient_id=user.user_id,
            read_at__isnull=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).filter(
            visible_at__lte=now
        )
        
        # 站点广播：不存在 ReadReceipt
        broadcast_notifications = Notification.objects.filter(
            recipient_type=Notification.RECIPIENT_SITE_BROADCAST
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).filter(
            visible_at__lte=now
        ).exclude(
            read_receipts__user_id=user.user_id
        )
        
        # 合并查询
        unread_notifications = personal_unread | broadcast_notifications
        
        # 总数
        total = unread_notifications.count()
        
        # 按分类统计
        by_category = {}
        category_counts = unread_notifications.values('category').annotate(
            count=Count('notification_id')
        )
        for item in category_counts:
            by_category[item['category']] = item['count']
        
        # 按严重度统计
        by_severity = {}
        severity_counts = unread_notifications.values('severity').annotate(
            count=Count('notification_id')
        )
        for item in severity_counts:
            by_severity[item['severity']] = item['count']
        
        data = {
            'total': total,
            'by_category': by_category,
            'by_severity': by_severity,
        }
        
        serializer = UnreadCountSerializer(data)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def announcement_list(request):
    """
    公告列表（站点广播）
    
    ⭐ 只返回站点广播类型的通知
    
    查询参数：
    - ?page=1
    - ?page_size=20
    - ?unread=true
    
    返回:
    {
        "count": 50,
        "next": "...",
        "previous": null,
        "results": [...]
    }
    """
    user = request.user
    now = timezone.now()
    
    # 基础查询：站点广播
    queryset = Notification.objects.filter(
        recipient_type=Notification.RECIPIENT_SITE_BROADCAST
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    ).filter(
        visible_at__lte=now
    ).order_by('-visible_at', '-created_at')
    
    # 未读过滤
    unread = request.query_params.get('unread')
    if unread == 'true':
        queryset = queryset.exclude(
            read_receipts__user_id=user.user_id
        )
    
    # 分页
    paginator = NotificationPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = NotificationSerializer(
            page,
            many=True,
            context={'request': request, 'user_id': user.user_id}
        )
        return paginator.get_paginated_response(serializer.data)
    
    # 无分页（不应该发生）
    serializer = NotificationSerializer(
        queryset,
        many=True,
        context={'request': request, 'user_id': user.user_id}
    )
    return Response(serializer.data)

