"""
Commission API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.commissions.serializers import CommissionViewSet

router = DefaultRouter()
router.register(r'commissions', CommissionViewSet, basename='commission')

urlpatterns = [
    path('', include(router.urls)),
]
