"""
订单 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
from .views_promo import (
    PromoCodeAdminViewSet,
    validate_promo_code,
    promo_code_usage_list,
)
from .views_preview import order_preview

app_name = 'orders'

# 订单路由
router = DefaultRouter()
router.register(r'', OrderViewSet, basename='orders')

# Promo Code 管理路由（管理员）
promo_router = DefaultRouter()
promo_router.register(r'admin/promo-codes', PromoCodeAdminViewSet, basename='promo-codes-admin')

urlpatterns = [
    # 订单
    path('', include(router.urls)),
    path('preview/', order_preview, name='order-preview'),
    
    # Promo Code 管理（管理员）
    path('', include(promo_router.urls)),
    path('admin/promo-codes/<uuid:promo_id>/usages/', promo_code_usage_list, name='promo-code-usages'),
    
    # Promo Code 验证（用户）
    path('promo-codes/validate/', validate_promo_code, name='promo-code-validate'),
]
