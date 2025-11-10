"""
Core API URLs（系统配置与资产管理）
"""
from django.urls import path
from apps.core.views import config, assets

urlpatterns = [
    # 系统配置查询
    path('admin/config/allow-prod-tx/', config.get_allow_prod_tx_status, name='allow-prod-tx-status'),
    
    # 资产配置 CRUD
    path('admin/chain-assets/', assets.list_chain_assets, name='chain-assets-list'),
    path('admin/chain-assets/create/', assets.create_or_update_chain_asset, name='chain-assets-create'),
]

