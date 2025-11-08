"""
库存服务测试

⭐ 测试场景：
- 乐观锁并发控制
- 库存不足拒绝
- 库存回补
- version 冲突处理
"""
from django.test import TransactionTestCase
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

from apps.sites.models import Site
from apps.tiers.models import Tier
from apps.tiers.services.inventory import lock_inventory, release_inventory, check_inventory_available


class InventoryServiceTestCase(TransactionTestCase):
    """库存服务测试（需要真实数据库事务）"""
    
    def setUp(self):
        """测试前置"""
        self.site = Site.objects.create(
            code='NA',
            name='North America',
            domain='na.posx.test',
            is_active=True
        )
        
        self.tier = Tier.objects.create(
            site=self.site,
            name='Test Tier',
            list_price_usd=Decimal('100.00'),
            tokens_per_unit=Decimal('1000.00'),
            total_units=10,
            sold_units=0,
            available_units=10,
            version=0,
            is_active=True
        )
    
    def test_lock_inventory_success(self):
        """测试库存锁定成功"""
        success, error = lock_inventory(self.tier.tier_id, 5)
        
        self.assertTrue(success)
        self.assertEqual(error, '')
        
        # 刷新档位
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, 5)
        self.assertEqual(self.tier.version, 1)
    
    def test_lock_inventory_insufficient(self):
        """测试库存不足"""
        success, error = lock_inventory(self.tier.tier_id, 15)
        
        self.assertFalse(success)
        self.assertEqual(error, 'INVENTORY.INSUFFICIENT')
        
        # 档位未变
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, 10)
        self.assertEqual(self.tier.version, 0)
    
    def test_concurrent_lock_inventory(self):
        """测试并发锁库存（10个线程同时锁）"""
        # 每个线程尝试锁1个单位
        num_threads = 10
        
        def try_lock():
            try:
                return lock_inventory(self.tier.tier_id, 1)
            except Exception as e:
                return False, str(e)
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(try_lock) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # 统计成功和失败
        success_count = sum(1 for success, _ in results if success)
        conflict_count = sum(1 for success, error in results if not success and 'CONFLICT' in error)
        
        # 应该恰好10个成功（库存总量）
        self.assertEqual(success_count, 10)
        
        # 刷新档位
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, 0)
        self.assertEqual(self.tier.version, 10)
    
    def test_release_inventory(self):
        """测试库存回补"""
        # 先锁定
        lock_inventory(self.tier.tier_id, 5)
        
        # 再回补
        success, error = release_inventory(self.tier.tier_id, 3)
        
        self.assertTrue(success)
        self.assertEqual(error, '')
        
        # 刷新档位
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, 8)  # 10 - 5 + 3
        self.assertEqual(self.tier.version, 2)  # lock + release
    
    def test_check_inventory_available(self):
        """测试库存检查（不锁定）"""
        # 检查充足
        available = check_inventory_available(self.tier.tier_id, 5)
        self.assertTrue(available)
        
        # 检查不足
        available = check_inventory_available(self.tier.tier_id, 15)
        self.assertFalse(available)


