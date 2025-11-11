"""
Site API Tests（站点配置管理测试）

测试范围：
1. 站点 CRUD 操作
2. 权限验证
3. 字段验证
4. 软删除功能
"""
import pytest
from rest_framework import status

from apps.sites.models import Site


@pytest.mark.django_db
class TestSiteAPI:
    """测试站点 API"""
    
    def test_create_site(self, api_client, admin_user):
        """测试创建站点"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post('/api/v1/admin/sites/', {
            'code': 'TEST',
            'name': 'Test Site',
            'domain': 'test.example.com',
            'is_active': True
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'TEST'
        assert response.data['name'] == 'Test Site'
        
        # 验证数据库
        site = Site.objects.get(site_id=response.data['site_id'])
        assert site.code == 'TEST'
        assert site.is_active is True
    
    def test_create_site_requires_admin(self, api_client, user):
        """测试创建站点需要管理员权限"""
        api_client.force_authenticate(user=user)
        
        response = api_client.post('/api/v1/admin/sites/', {
            'code': 'TEST2',
            'name': 'Test Site 2',
            'domain': 'test2.example.com'
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_code_uppercase_conversion(self, api_client, admin_user):
        """测试代码自动转大写"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post('/api/v1/admin/sites/', {
            'code': 'lowercase',
            'name': 'Test Site',
            'domain': 'lowercase.example.com'
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'LOWERCASE'
    
    def test_duplicate_code_rejected(self, api_client, admin_user, site):
        """测试重复代码被拒绝"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post('/api/v1/admin/sites/', {
            'code': site.code,
            'name': 'Duplicate Site',
            'domain': 'duplicate.example.com'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
    
    def test_list_sites(self, api_client, admin_user):
        """测试站点列表"""
        # 创建多个站点
        Site.objects.create(code='SITE1', name='Site 1', domain='site1.com', is_active=True)
        Site.objects.create(code='SITE2', name='Site 2', domain='site2.com', is_active=False)
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/admin/sites/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2
    
    def test_filter_sites_by_active(self, api_client, admin_user):
        """测试按激活状态过滤站点"""
        Site.objects.create(code='ACTIVE', name='Active Site', domain='active.com', is_active=True)
        Site.objects.create(code='INACTIVE', name='Inactive Site', domain='inactive.com', is_active=False)
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/admin/sites/?is_active=true')
        
        assert response.status_code == status.HTTP_200_OK
        for site in response.data['results']:
            assert site['is_active'] is True
    
    def test_update_site(self, api_client, admin_user, site):
        """测试更新站点"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.put(f'/api/v1/admin/sites/{site.site_id}/', {
            'code': site.code,
            'name': 'Updated Name',
            'domain': site.domain,
            'is_active': site.is_active
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'
        
        site.refresh_from_db()
        assert site.name == 'Updated Name'
    
    def test_soft_delete_site(self, api_client, admin_user, site):
        """测试软删除站点"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.delete(f'/api/v1/admin/sites/{site.site_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        site.refresh_from_db()
        assert site.is_active is False  # 软删除
    
    def test_activate_site(self, api_client, admin_user):
        """测试激活站点"""
        site = Site.objects.create(
            code='INACTIVE2',
            name='Inactive Site 2',
            domain='inactive2.com',
            is_active=False
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/v1/admin/sites/{site.site_id}/activate/')
        
        assert response.status_code == status.HTTP_200_OK
        
        site.refresh_from_db()
        assert site.is_active is True
    
    def test_site_stats(self, api_client, admin_user, site):
        """测试站点统计"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/v1/admin/sites/{site.site_id}/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'orders' in response.data
        assert 'tiers' in response.data
        assert 'agents' in response.data
        assert 'commissions' in response.data

