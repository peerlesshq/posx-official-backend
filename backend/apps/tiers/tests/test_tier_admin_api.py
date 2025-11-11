"""
Tier Admin API Tests（产品配置管理测试）

测试范围：
1. 产品 CRUD 操作
2. 库存调整
3. 促销价验证
4. 权限验证
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from apps.tiers.models import Tier


@pytest.mark.django_db
class TestTierAdminAPI:
    """测试产品管理 API"""
    
    def test_create_tier(self, api_client, admin_user, site):
        """测试创建产品"""
        api_client.force_authenticate(user=admin_user)
        
        # 模拟 request.site
        api_client.defaults['HTTP_X_SITE_CODE'] = site.code
        
        response = api_client.post('/api/v1/admin/tiers/', {
            'name': 'Test Tier',
            'description': 'Test Description',
            'list_price_usd': '1000.00',
            'tokens_per_unit': '10000',
            'total_units': 1000,
            'display_order': 1,
            'is_active': True
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Test Tier'
        
        # 验证数据库
        tier = Tier.objects.get(tier_id=response.data['tier_id'])
        assert tier.sold_units == 0
        assert tier.available_units == 1000
    
    def test_create_tier_requires_admin(self, api_client, user):
        """测试创建产品需要管理员权限"""
        api_client.force_authenticate(user=user)
        
        response = api_client.post('/api/v1/admin/tiers/', {
            'name': 'Test Tier 2',
            'list_price_usd': '500.00',
            'tokens_per_unit': '5000',
            'total_units': 500
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_promotional_price_validation(self, api_client, admin_user, site):
        """测试促销价验证（必须低于原价）"""
        api_client.force_authenticate(user=admin_user)
        api_client.defaults['HTTP_X_SITE_CODE'] = site.code
        
        # 促销价等于原价（应该失败）
        response = api_client.post('/api/v1/admin/tiers/', {
            'name': 'Invalid Promo',
            'list_price_usd': '1000.00',
            'promotional_price_usd': '1000.00',  # 等于原价
            'tokens_per_unit': '10000',
            'total_units': 1000
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'promotional_price_usd' in response.data
    
    def test_promotional_requires_time_range(self, api_client, admin_user, site):
        """测试设置促销价必须指定时间范围"""
        api_client.force_authenticate(user=admin_user)
        api_client.defaults['HTTP_X_SITE_CODE'] = site.code
        
        response = api_client.post('/api/v1/admin/tiers/', {
            'name': 'Incomplete Promo',
            'list_price_usd': '1000.00',
            'promotional_price_usd': '800.00',  # 有促销价
            'tokens_per_unit': '10000',
            'total_units': 1000
            # 缺少 promotion_valid_from 和 promotion_valid_until
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_tier(self, api_client, admin_user, tier):
        """测试更新产品"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.patch(f'/api/v1/admin/tiers/{tier.tier_id}/', {
            'name': 'Updated Tier Name',
            'list_price_usd': '1200.00'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Tier Name'
        
        tier.refresh_from_db()
        assert tier.name == 'Updated Tier Name'
        assert tier.list_price_usd == Decimal('1200.00')
    
    def test_update_total_units_recalculates_available(self, api_client, admin_user, site):
        """测试更新总库存会重新计算可用库存"""
        # 创建产品：总库存100，已售10
        tier = Tier.objects.create(
            site=site,
            name='Test Tier',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=100,
            sold_units=10,
            available_units=90
        )
        
        api_client.force_authenticate(user=admin_user)
        
        # 增加总库存到200
        response = api_client.patch(f'/api/v1/admin/tiers/{tier.tier_id}/', {
            'total_units': 200
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        tier.refresh_from_db()
        assert tier.total_units == 200
        assert tier.sold_units == 10
        assert tier.available_units == 190  # 200 - 10
    
    def test_cannot_reduce_total_below_sold(self, api_client, admin_user, site):
        """测试不能将总库存减少到低于已售数量"""
        tier = Tier.objects.create(
            site=site,
            name='Test Tier',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=100,
            sold_units=50,
            available_units=50
        )
        
        api_client.force_authenticate(user=admin_user)
        
        # 尝试将总库存减少到40（低于已售50）
        response = api_client.patch(f'/api/v1/admin/tiers/{tier.tier_id}/', {
            'total_units': 40
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'total_units' in response.data
    
    def test_adjust_inventory_increase(self, api_client, admin_user, tier):
        """测试增加库存"""
        api_client.force_authenticate(user=admin_user)
        
        old_total = tier.total_units
        old_available = tier.available_units
        
        response = api_client.post(
            f'/api/v1/admin/tiers/{tier.tier_id}/adjust-inventory/',
            {
                'adjustment': 500,
                'reason': '补货'
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['adjustment'] == 500
        
        tier.refresh_from_db()
        assert tier.total_units == old_total + 500
        assert tier.available_units == old_available + 500
    
    def test_adjust_inventory_decrease(self, api_client, admin_user, site):
        """测试减少库存"""
        tier = Tier.objects.create(
            site=site,
            name='Test Tier',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=1000,
            sold_units=100,
            available_units=900
        )
        
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post(
            f'/api/v1/admin/tiers/{tier.tier_id}/adjust-inventory/',
            {
                'adjustment': -200,
                'reason': '报废'
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        tier.refresh_from_db()
        assert tier.total_units == 800
        assert tier.available_units == 700  # 800 - 100
    
    def test_cannot_adjust_below_sold(self, api_client, admin_user, site):
        """测试不能将库存调整到低于已售数量"""
        tier = Tier.objects.create(
            site=site,
            name='Test Tier',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=100,
            sold_units=50,
            available_units=50
        )
        
        api_client.force_authenticate(user=admin_user)
        
        # 尝试减少60（总库存会变成40，低于已售50）
        response = api_client.post(
            f'/api/v1/admin/tiers/{tier.tier_id}/adjust-inventory/',
            {
                'adjustment': -60
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_soft_delete_tier(self, api_client, admin_user, tier):
        """测试软删除产品"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.delete(f'/api/v1/admin/tiers/{tier.tier_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        tier.refresh_from_db()
        assert tier.is_active is False  # 软删除
    
    def test_activate_tier(self, api_client, admin_user, site):
        """测试激活产品"""
        tier = Tier.objects.create(
            site=site,
            name='Inactive Tier',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=100,
            sold_units=0,
            available_units=100,
            is_active=False
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/v1/admin/tiers/{tier.tier_id}/activate/')
        
        assert response.status_code == status.HTTP_200_OK
        
        tier.refresh_from_db()
        assert tier.is_active is True
    
    def test_tier_stats(self, api_client, admin_user, tier):
        """测试产品统计"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/v1/admin/tiers/{tier.tier_id}/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'orders' in response.data
        assert 'revenue' in response.data
        assert 'inventory' in response.data
    
    def test_filter_by_site(self, api_client, admin_user, site):
        """测试按站点过滤产品"""
        # 创建另一个站点
        site2 = Site.objects.create(
            code='SITE2',
            name='Site 2',
            domain='site2.com',
            is_active=True
        )
        
        # 创建两个站点的产品
        Tier.objects.create(
            site=site,
            name='Tier Site 1',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        Tier.objects.create(
            site=site2,
            name='Tier Site 2',
            list_price_usd=Decimal('1000'),
            tokens_per_unit=Decimal('10000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/v1/admin/tiers/?site_code={site.code}')
        
        assert response.status_code == status.HTTP_200_OK
        for tier in response.data['results']:
            assert tier['site_code'] == site.code

