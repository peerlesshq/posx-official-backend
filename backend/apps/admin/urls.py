"""
Admin API URLs（Phase F）
管理员报表与监控端点
"""
from django.urls import path
from . import views

urlpatterns = [
    # 报表端点（需超级管理员权限）
    path('reports/overview/', views.overview_report, name='admin-overview-report'),
    path('reports/leaderboard/', views.agent_leaderboard, name='admin-agent-leaderboard'),
    path('reports/reconciliation/', views.commission_reconciliation, name='admin-commission-reconciliation'),
    path('reports/anomalies/', views.anomaly_report, name='admin-anomaly-report'),
]
