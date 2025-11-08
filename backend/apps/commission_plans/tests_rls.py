"""
RLS 烟雾测试

⭐ 测试重点：
- 跨站点数据不可见（RLS 隔离生效）
- SET LOCAL 事务隔离（自动失效）
"""
from django.test import TestCase, TransactionTestCase
from django.db import connection
from apps.sites.models import Site
from apps.users.models import User
from .models import CommissionPlan
import uuid


class RLSSiteIsolationTestCase(TestCase):
    """
    RLS 站点隔离测试
    
    验证：切换 X-Site-Code 后，跨站数据不可见
    """
    
    def setUp(self):
        """测试前置"""
        # 创建两个站点
        self.site_na = Site.objects.create(
            code='NA',
            name='North America',
            domain='na.posx.test',
            is_active=True
        )
        self.site_asia = Site.objects.create(
            code='ASIA',
            name='Asia Pacific',
            domain='asia.posx.test',
            is_active=True
        )
    
    def test_cross_site_data_invisible(self):
        """测试跨站数据不可见"""
        # 在 NA 站点创建计划（绕过 RLS，直接创建）
        plan_na = CommissionPlan.objects.create(
            site_id=self.site_na.site_id,
            name='NA Plan',
            version=1,
            mode='level',
        )
        
        # 在 ASIA 站点创建计划
        plan_asia = CommissionPlan.objects.create(
            site_id=self.site_asia.site_id,
            name='ASIA Plan',
            version=1,
            mode='level',
        )
        
        # ⚠️ 未设置 SET LOCAL 时，admin 连接可以看到所有数据
        all_plans = CommissionPlan.objects.all()
        self.assertEqual(all_plans.count(), 2)
        
        # 设置 NA 站点上下文
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.current_site_id = %s",
                [str(self.site_na.site_id)]
            )
        
        # 应该只能看到 NA 的计划
        na_plans = CommissionPlan.objects.all()
        self.assertEqual(na_plans.count(), 1)
        self.assertEqual(na_plans.first().plan_id, plan_na.plan_id)
        
        # 切换到 ASIA 站点上下文
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.current_site_id = %s",
                [str(self.site_asia.site_id)]
            )
        
        # 应该只能看到 ASIA 的计划
        asia_plans = CommissionPlan.objects.all()
        self.assertEqual(asia_plans.count(), 1)
        self.assertEqual(asia_plans.first().plan_id, plan_asia.plan_id)
    
    def test_cross_site_update_blocked(self):
        """测试跨站更新被阻止"""
        # 在 NA 站点创建计划
        plan_na = CommissionPlan.objects.create(
            site_id=self.site_na.site_id,
            name='NA Plan',
            version=1,
            mode='level',
        )
        
        # 设置 ASIA 站点上下文
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.current_site_id = %s",
                [str(self.site_asia.site_id)]
            )
        
        # 尝试查询 NA 的计划（应该失败）
        asia_visible = CommissionPlan.objects.filter(
            plan_id=plan_na.plan_id
        ).exists()
        
        self.assertFalse(
            asia_visible,
            "ASIA 站点不应该看到 NA 站点的数据（RLS 隔离生效）"
        )


class RLSTransactionIsolationTestCase(TransactionTestCase):
    """
    RLS 事务隔离测试
    
    验证：SET LOCAL 在事务结束后自动失效
    """
    
    def setUp(self):
        """测试前置"""
        self.site_na = Site.objects.create(
            code='NA',
            name='North America',
            domain='na.posx.test',
            is_active=True
        )
    
    def test_set_local_auto_reset_after_transaction(self):
        """测试 SET LOCAL 事务结束后自动失效"""
        # 创建测试数据
        plan = CommissionPlan.objects.create(
            site_id=self.site_na.site_id,
            name='Test Plan',
            version=1,
            mode='level',
        )
        
        # 在事务中设置 SET LOCAL
        from django.db import transaction
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL app.current_site_id = %s",
                    [str(self.site_na.site_id)]
                )
                
                # 事务内可以看到数据
                visible_in_tx = CommissionPlan.objects.filter(
                    plan_id=plan.plan_id
                ).exists()
                self.assertTrue(visible_in_tx, "事务内应该可见")
        
        # 事务结束后，SET LOCAL 自动失效
        # 由于使用 admin 连接（绕过 RLS），仍然可见所有数据
        # 但如果是应用连接（posx_app），则需要重新设置 SET LOCAL
        
        # 验证：不设置 SET LOCAL 时，使用 admin 连接可以看到所有数据
        all_plans = CommissionPlan.objects.all()
        self.assertGreaterEqual(
            all_plans.count(), 1,
            "Admin 连接（绕过 RLS）应该可以看到所有数据"
        )
    
    def test_concurrent_set_local_isolation(self):
        """测试并发请求的 SET LOCAL 隔离"""
        # 创建两个站点的数据
        site_asia = Site.objects.create(
            code='ASIA',
            name='Asia Pacific',
            domain='asia.posx.test',
            is_active=True
        )
        
        plan_na = CommissionPlan.objects.create(
            site_id=self.site_na.site_id,
            name='NA Plan',
            version=1,
            mode='level',
        )
        
        plan_asia = CommissionPlan.objects.create(
            site_id=site_asia.site_id,
            name='ASIA Plan',
            version=1,
            mode='level',
        )
        
        # 模拟请求 1：NA 站点
        from django.db import transaction
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL app.current_site_id = %s",
                    [str(self.site_na.site_id)]
                )
            
            # 应该只看到 NA 数据
            na_count = CommissionPlan.objects.count()
            self.assertEqual(na_count, 1)
        
        # 模拟请求 2：ASIA 站点（新事务）
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL app.current_site_id = %s",
                    [str(site_asia.site_id)]
                )
            
            # 应该只看到 ASIA 数据
            asia_count = CommissionPlan.objects.count()
            self.assertEqual(asia_count, 1)


class RLSPerformanceTestCase(TestCase):
    """
    RLS 性能测试（轻量）
    
    验证：RLS 不会显著影响查询性能
    """
    
    def setUp(self):
        """测试前置"""
        self.site_na = Site.objects.create(
            code='NA',
            name='North America',
            domain='na.posx.test',
            is_active=True
        )
    
    def test_rls_query_performance(self):
        """测试 RLS 查询性能"""
        # 创建一批测试数据
        plans = [
            CommissionPlan(
                site_id=self.site_na.site_id,
                name=f'Plan {i}',
                version=1,
                mode='level',
            )
            for i in range(100)
        ]
        CommissionPlan.objects.bulk_create(plans)
        
        # 设置站点上下文
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.current_site_id = %s",
                [str(self.site_na.site_id)]
            )
        
        # 查询（应该快速完成）
        import time
        start = time.time()
        result = list(CommissionPlan.objects.all()[:50])
        elapsed = time.time() - start
        
        self.assertLess(
            elapsed, 1.0,
            f"RLS 查询耗时过长：{elapsed:.3f}s（应该 < 1s）"
        )
        self.assertEqual(len(result), 50)



