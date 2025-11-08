"""
佣金计划 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommissionPlanViewSet

app_name = 'commission_plans'

router = DefaultRouter()
router.register(r'', CommissionPlanViewSet, basename='commission-plans')

urlpatterns = [
    path('', include(router.urls)),
]



