"""
Commission Plan API 测试（Phase F）
"""
import pytest
from decimal import Decimal
from rest_framework import status as http_status

from apps.commissions.models import CommissionPlan, CommissionPlanTier


@pytest.mark.django_db
class TestCommissionPlanAPI:
    """测试佣金方案 API"""
    
    def test_create_commission_plan(self, api_client, admin_user, site):
        """测试创建佣金方案"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post('/api/v1/commissions/plans/', {
            'site': str(site.site_id),
            'name': '标准方案',
            'description': '2级标准佣金方案',
            'max_levels': 2,
            'is_default': True,
            'tiers': [
                {
                    'level': 1,
                    'rate_percent': '12.00',
                    'hold_days': 7,
                    'min_order_amount': '0.00'
                },
                {
                    'level': 2,
                    'rate_percent': '4.00',
                    'hold_days': 7,
                    'min_order_amount': '0.00'
                }
            ]
        }, format='json')
        
        assert response.status_code == http_status.HTTP_201_CREATED
        
        # 验证方案创建
        plan = CommissionPlan.objects.get(plan_id=response.data['plan_id'])
        assert plan.name == '标准方案'
        assert plan.max_levels == 2
        assert plan.tiers.count() == 2
    
    def test_list_commission_plans(self, api_client, user, site):
        """测试查询佣金方案列表"""
        # 创建方案
        plan = CommissionPlan.objects.create(
            site=site,
            name='测试方案',
            max_levels=2,
            is_default=True
        )
        
        api_client.force_authenticate(user=user)
        api_client.site = site
        
        response = api_client.get('/api/v1/commissions/plans/')
        
        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == '测试方案'
    
    def test_set_default_plan(self, api_client, admin_user, site):
        """测试设置默认方案"""
        # 创建两个方案
        plan1 = CommissionPlan.objects.create(
            site=site,
            name='方案1',
            is_default=True
        )
        plan2 = CommissionPlan.objects.create(
            site=site,
            name='方案2',
            is_default=False
        )
        
        api_client.force_authenticate(user=admin_user)
        
        # 设置方案2为默认
        response = api_client.post(f'/api/v1/commissions/plans/{plan2.plan_id}/set-default/')
        
        assert response.status_code == http_status.HTTP_200_OK
        
        # 验证
        plan1.refresh_from_db()
        plan2.refresh_from_db()
        assert plan1.is_default == False
        assert plan2.is_default == True
    
    def test_plan_tier_validation(self, api_client, admin_user, site):
        """测试层级验证（必须连续）"""
        api_client.force_authenticate(user=admin_user)
        
        # 提交不连续的层级
        response = api_client.post('/api/v1/commissions/plans/', {
            'site': str(site.site_id),
            'name': '错误方案',
            'max_levels': 3,
            'tiers': [
                {'level': 1, 'rate_percent': '12.00', 'hold_days': 7},
                {'level': 3, 'rate_percent': '4.00', 'hold_days': 7},  # 跳过 L2
            ]
        }, format='json')
        
        # 验证失败
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

