"""
Notifications URL Configuration

⭐ REST API 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# TODO: 导入 ViewSet
# from apps.notifications.views import NotificationViewSet

router = DefaultRouter()
# router.register(r'notifications', NotificationViewSet, basename='notification')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
    # TODO: 添加自定义端点
    # path('announcements/', views.announcement_list, name='announcement-list'),
    # path('unread-count/', views.unread_count, name='unread-count'),
]

