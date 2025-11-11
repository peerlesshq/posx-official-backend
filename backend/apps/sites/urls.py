"""
Sites API URLs（站点配置管理）

⭐ 权限：IsAdminUser（超级管理员）
⭐ 端点：
- GET /api/v1/admin/sites/ - 站点列表
- POST /api/v1/admin/sites/ - 创建站点
- GET /api/v1/admin/sites/{id}/ - 站点详情
- PUT /api/v1/admin/sites/{id}/ - 更新站点
- PATCH /api/v1/admin/sites/{id}/ - 部分更新
- DELETE /api/v1/admin/sites/{id}/ - 软删除
- POST /api/v1/admin/sites/{id}/activate/ - 激活站点
- GET /api/v1/admin/sites/{id}/stats/ - 站点统计
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteViewSet, ChainAssetConfigViewSet

app_name = 'sites'

router = DefaultRouter()
router.register(r'', SiteViewSet, basename='sites')
router.register(r'assets', ChainAssetConfigViewSet, basename='chain-assets')

urlpatterns = [
    path('', include(router.urls)),
]



