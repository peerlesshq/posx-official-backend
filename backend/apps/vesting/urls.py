"""
Vesting API URLs（Retool 对接）
"""
from django.urls import path
from . import views

urlpatterns = [
    # VestingRelease 列表查询
    path('vesting-releases/', views.list_vesting_releases, name='vesting-releases-list'),
    
    # 守护任务 API（管理员）
    path(
        'admin/vesting/releases/stuck-stats/',
        views.get_stuck_releases_stats,
        name='stuck-releases-stats'
    ),
    path(
        'admin/vesting/releases/reconcile/',
        views.trigger_reconcile,
        name='trigger-reconcile'
    ),
]

