"""
Commission API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.commissions.serializers import CommissionViewSet
from apps.commissions.views_plans import CommissionPlanViewSet

router = DefaultRouter()
router.register(r'', CommissionViewSet, basename='commission')
router.register(r'plans', CommissionPlanViewSet, basename='commission-plan')

urlpatterns = [
    path('', include(router.urls)),
]
