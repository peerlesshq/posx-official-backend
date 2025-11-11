"""
档位 URL 路由

⭐ 端点：
公开端点（IsAuthenticated）：
- GET /api/v1/tiers/ - 产品列表
- GET /api/v1/tiers/{id}/ - 产品详情

管理端点（IsAdminUser）：
- POST /api/v1/admin/tiers/ - 创建产品
- PUT /api/v1/admin/tiers/{id}/ - 更新产品
- PATCH /api/v1/admin/tiers/{id}/ - 部分更新
- DELETE /api/v1/admin/tiers/{id}/ - 软删除
- POST /api/v1/admin/tiers/{id}/adjust-inventory/ - 调整库存
- POST /api/v1/admin/tiers/{id}/activate/ - 激活产品
- GET /api/v1/admin/tiers/{id}/stats/ - 产品统计
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TierViewSet
from .views_admin import TierAdminViewSet

app_name = 'tiers'

# 公开路由
public_router = DefaultRouter()
public_router.register(r'', TierViewSet, basename='tiers')

# 管理路由
admin_router = DefaultRouter()
admin_router.register(r'', TierAdminViewSet, basename='tiers-admin')

urlpatterns = [
    path('', include(public_router.urls)),
]

# 导出管理路由（在 config/urls.py 中使用）
admin_urlpatterns = [
    path('', include(admin_router.urls)),
]
