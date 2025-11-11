"""
Allocations API URLs

⭐ P1 补充：用户分配记录查询

端点：
1. GET /api/v1/allocations/ - 分配记录列表
2. GET /api/v1/allocations/{id}/ - 分配记录详情
3. GET /api/v1/allocations/balance/ - 代币余额统计
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.AllocationViewSet, basename='allocation')

app_name = 'allocations'

urlpatterns = [
    path('', include(router.urls)),
]



