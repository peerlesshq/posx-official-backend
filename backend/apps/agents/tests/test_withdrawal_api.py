"""
提现申请 API 测试（Phase F）
"""
import pytest
from decimal import Decimal
from rest_framework import status as http_status

from apps.agents.models import AgentProfile, WithdrawalRequest


@pytest.mark.django_db
class TestWithdrawalAPI:
    """测试提现申请 API"""
    
    def test_submit_withdrawal_success(self, api_client, user, site):
        """测试提交提现申请（余额充足）"""
        # 创建 Profile 并充值
        profile = AgentProfile.objects.create(
            user=user,
            site=site,
            balance_usd=Decimal('200.00')
        )
        
        # 登录
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        # 提交申请
        response = api_client.post('/api/v1/agents/withdrawal/', {
            'amount_usd': '100.00',
            'withdrawal_method': 'bank_transfer',
            'account_info': {
                'bank_name': 'Test Bank',
                'account_number': '123456789'
            }
        })
        
        # 验证
        assert response.status_code == http_status.HTTP_201_CREATED
        assert 'request_id' in response.data
        
        # 验证余额已扣减
        profile.refresh_from_db()
        assert profile.balance_usd == Decimal('100.00')
        
        # 验证申请已创建
        assert WithdrawalRequest.objects.filter(
            agent_profile=profile,
            status='submitted'
        ).count() == 1
    
    def test_submit_withdrawal_insufficient_balance(self, api_client, user, site):
        """测试提交提现申请（余额不足）"""
        # 创建 Profile（余额不足）
        profile = AgentProfile.objects.create(
            user=user,
            site=site,
            balance_usd=Decimal('30.00')
        )
        
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        # 提交申请
        response = api_client.post('/api/v1/agents/withdrawal/', {
            'amount_usd': '100.00',
            'withdrawal_method': 'bank_transfer',
            'account_info': {}
        })
        
        # 验证
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert 'INSUFFICIENT_BALANCE' in response.data.get('code', '')
        
        # 验证余额未扣减
        profile.refresh_from_db()
        assert profile.balance_usd == Decimal('30.00')
    
    def test_submit_withdrawal_below_min_amount(self, api_client, user, site):
        """测试提现金额低于最小限制"""
        profile = AgentProfile.objects.create(
            user=user,
            site=site,
            balance_usd=Decimal('100.00')
        )
        
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        # 提交申请（金额过小）
        response = api_client.post('/api/v1/agents/withdrawal/', {
            'amount_usd': '10.00',  # < WITHDRAWAL_MIN_AMOUNT (50.00)
            'withdrawal_method': 'bank_transfer',
            'account_info': {}
        })
        
        # 验证
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    
    def test_query_withdrawal_requests(self, api_client, user, site):
        """测试查询提现记录"""
        profile = AgentProfile.objects.create(user=user, site=site)
        
        # 创建提现记录
        WithdrawalRequest.objects.create(
            agent_profile=profile,
            amount_usd=Decimal('100.00'),
            withdrawal_method='bank_transfer',
            account_info={},
            status='submitted'
        )
        
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        # 查询
        response = api_client.get('/api/v1/agents/withdrawal-requests/')
        
        # 验证
        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['status'] == 'submitted'

