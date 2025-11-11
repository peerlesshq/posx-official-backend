"""
Notifications URL Configuration

⭐ REST API 路由

端点：
1. GET /api/v1/notifications/ - 通知列表
2. GET /api/v1/notifications/{id}/ - 通知详情
3. PATCH /api/v1/notifications/mark-read/ - 标记已读（批量）
4. GET /api/v1/notifications/unread-count/ - 未读数统计
5. GET /api/v1/notifications/announcements/ - 公告列表
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
    path('announcements/', views.announcement_list, name='announcement-list'),
]

