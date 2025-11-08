"""
URL Configuration for POSX
包含健康检查端点的豁免
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views.health import health, ready, version
from apps.core.views.test_views import test_auth, test_public, test_config

urlpatterns = [
    # ============================================
    # 健康检查（CSRF 豁免）
    # ============================================
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('version/', version, name='version'),
    
    # ============================================
    # Admin
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # API v1（CSRF 豁免）
    # ============================================
    path('api/v1/', include([
        # Phase C: SIWE Wallet Authentication
        path('auth/', include('apps.users.urls_auth')),
        
        # Original endpoints
        path('users/', include('apps.users.urls')),
        path('sites/', include('apps.sites.urls')),
        path('tiers/', include('apps.tiers.urls')),
        path('orders/', include('apps.orders.urls')),
        path('allocations/', include('apps.allocations.urls')),
        path('commissions/', include('apps.commissions.urls')),
        path('webhooks/', include('apps.webhooks.urls')),
        
        # Phase B endpoints
        path('commission-plans/', include('apps.commission_plans.urls')),
        path('agents/', include('apps.agents.urls')),
    ])),
    
    # ============================================
    # Test endpoints for Auth0
    # ============================================
    path('api/v1/test/protected/', test_auth, name='test_auth'),
    path('api/v1/test/public/', test_public, name='test_public'),
    path('api/v1/test/config/', test_config, name='test_config'),
]
