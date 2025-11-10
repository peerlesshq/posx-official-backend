"""
Agent Dashboard API 测试（Phase F）
"""
import pytest
from decimal import Decimal
from rest_framework import status as http_status

from apps.agents.models import AgentProfile
from apps.commissions.models import Commission
from apps.orders.models import Order


@pytest.mark.django_db
class TestAgentDashboard:
    """测试 Agent Dashboard API"""
    
    def test_dashboard_no_data(self, api_client, user, site):
        """测试新 Agent 的 Dashboard（无数据）"""
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        response = api_client.get('/api/v1/agents/dashboard/')
        
        assert response.status_code == http_status.HTTP_200_OK
        
        # 验证数据结构
        assert 'balance' in response.data
        assert 'performance' in response.data
        assert 'team' in response.data
        assert 'recent_commissions' in response.data
        assert 'recent_orders' in response.data
        
        # 验证初始值
        assert response.data['balance']['available'] == '0.00'
        assert response.data['performance']['total_sales'] == '0.00'
        assert response.data['team']['total_downlines'] == 0
    
    def test_balance_query(self, api_client, user, site):
        """测试余额查询"""
        # 创建 Profile 并设置余额
        profile = AgentProfile.objects.create(
            user=user,
            site=site,
            balance_usd=Decimal('1234.56'),
            total_earned_usd=Decimal('5000.00'),
            total_withdrawn_usd=Decimal('3765.44')
        )
        
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        response = api_client.get('/api/v1/agents/me/balance/')
        
        assert response.status_code == http_status.HTTP_200_OK
        assert response.data['balance_usd'] == '1234.56'
        assert response.data['total_earned_usd'] == '5000.00'
        assert response.data['total_withdrawn_usd'] == '3765.44'
    
    def test_dashboard_with_commissions(self, api_client, user, site, order_paid):
        """测试有佣金数据的 Dashboard"""
        # 创建佣金
        commission = Commission.objects.create(
            order=order_paid,
            agent=user,
            level=1,
            rate_percent=Decimal('12.00'),
            commission_amount_usd=Decimal('12.00'),
            status='hold'
        )
        
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        response = api_client.get('/api/v1/agents/dashboard/')
        
        assert response.status_code == http_status.HTTP_200_OK
        
        # 验证佣金数据
        assert response.data['balance']['pending_commissions']['hold'] == '12.00'
        assert len(response.data['recent_commissions']) == 1

