"""
代理 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet

app_name = 'agents'

router = DefaultRouter()
router.register(r'', AgentViewSet, basename='agents')

urlpatterns = [
    path('', include(router.urls)),
]



