"""
管理员报表 API 测试（Phase F）
"""
import pytest
from decimal import Decimal
from rest_framework import status as http_status

from apps.orders.models import Order
from apps.commissions.models import Commission


@pytest.mark.django_db
class TestAdminReports:
    """测试管理员报表 API"""
    
    def test_overview_report_requires_admin(self, api_client, user):
        """测试非管理员无法访问报表"""
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/admin-api/reports/overview/')
        
        # 非管理员应被拒绝
        assert response.status_code == http_status.HTTP_403_FORBIDDEN
    
    def test_overview_report_as_admin(self, api_client, admin_user, site):
        """测试管理员查询概览报表"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get('/api/admin-api/reports/overview/?site_code=NA')
        
        assert response.status_code == http_status.HTTP_200_OK
        
        # 验证数据结构
        assert 'period' in response.data
        assert 'total_sales' in response.data
        assert 'total_orders' in response.data
        assert 'total_commissions_paid' in response.data
        assert 'total_commissions_pending' in response.data
        assert 'active_agents' in response.data
        assert 'top_agents' in response.data
    
    def test_agent_leaderboard(self, api_client, admin_user):
        """测试 Agent 排行榜"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get('/api/admin-api/reports/leaderboard/?period=this_month&limit=20')
        
        assert response.status_code == http_status.HTTP_200_OK
        assert isinstance(response.data, list)
        
        # 验证排名
        if len(response.data) > 1:
            assert response.data[0]['rank'] == 1
            assert response.data[1]['rank'] == 2
    
    def test_commission_reconciliation(self, api_client, admin_user):
        """测试佣金对账报表"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get('/api/admin-api/reports/reconciliation/?period=2025-11')
        
        assert response.status_code == http_status.HTTP_200_OK
        
        # 验证数据结构
        assert 'period' in response.data
        assert 'total_generated' in response.data
        assert 'total_paid' in response.data
        assert 'total_pending' in response.data
        assert 'total_cancelled' in response.data
        assert 'by_status' in response.data
        assert 'by_level' in response.data
    
    def test_anomaly_report(self, api_client, admin_user):
        """测试异常监控报表"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get('/api/admin-api/reports/anomalies/')
        
        assert response.status_code == http_status.HTTP_200_OK
        
        # 验证数据结构
        assert 'stuck_commissions' in response.data
        assert 'failed_allocations' in response.data
        assert 'disputed_orders' in response.data
        assert 'inactive_agents' in response.data
        assert 'pending_withdrawals' in response.data

