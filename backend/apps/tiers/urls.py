"""
档位 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TierViewSet

app_name = 'tiers'

router = DefaultRouter()
router.register(r'', TierViewSet, basename='tiers')

urlpatterns = [
    path('', include(router.urls)),
]
