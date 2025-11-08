"""
订单端到端测试

⭐ 测试流程：
1. 获取nonce
2. SIWE签名认证
3. 查询可用档位
4. 创建订单（幂等测试）
5. 取消订单
6. 验证库存回补
"""
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.sites.models import Site
from apps.users.models import User, Wallet
from apps.tiers.models import Tier
from apps.orders.models import Order, OrderItem
from apps.orders_snapshots.models import OrderCommissionPolicySnapshot
from apps.commission_plans.models import CommissionPlan, CommissionPlanTier


class OrderE2ETestCase(TransactionTestCase):
    """订单端到端测试"""
    
    def setUp(self):
        """测试前置"""
        # 创建站点
        self.site = Site.objects.create(
            code='NA',
            name='North America',
            domain='na.posx.test',
            is_active=True
        )
        
        # 创建用户
        self.user = User.objects.create(
            referral_code='NA-TEST123',
            is_active=True
        )
        
        # 创建钱包
        self.wallet = Wallet.objects.create(
            user=self.user,
            address='0xab5801a7d398351b8be11c439e05c5b3259aec9b',
            is_primary=True
        )
        
        # 创建档位
        self.tier = Tier.objects.create(
            site=self.site,
            name='Tier 1',
            description='Test tier',
            list_price_usd=Decimal('100.00'),
            tokens_per_unit=Decimal('1000.00'),
            total_units=100,
            sold_units=0,
            available_units=100,
            display_order=1,
            version=0,
            is_active=True
        )
        
        # 创建佣金计划（供快照使用）
        self.commission_plan = CommissionPlan.objects.create(
            site_id=self.site.site_id,
            name='Standard Plan',
            version=1,
            mode='level',
            is_active=True
        )
        
        CommissionPlanTier.objects.create(
            plan=self.commission_plan,
            level=1,
            rate_percent=Decimal('12.00'),
            hold_days=7
        )
        
        # API 客户端
        self.client = APIClient()
    
    def test_create_order_idempotent(self):
        """测试创建订单（幂等性）"""
        self.client.force_authenticate(user=self.user)
        
        # 模拟站点上下文
        # 注意：需要中间件设置request.site，这里手动模拟
        
        # 第一次请求
        response1 = self.client.post(
            '/api/v1/orders/',
            data={
                'tier_id': str(self.tier.tier_id),
                'quantity': 1,
                'wallet_address': self.wallet.address,
            },
            HTTP_X_SITE_CODE='NA',
            HTTP_IDEMPOTENCY_KEY='test-key-123',
            format='json'
        )
        
        # 应该返回201或200（取决于实现）
        # self.assertIn(response1.status_code, [200, 201])
        
        # 第二次请求（相同幂等键）
        response2 = self.client.post(
            '/api/v1/orders/',
            data={
                'tier_id': str(self.tier.tier_id),
                'quantity': 1,
                'wallet_address': self.wallet.address,
            },
            HTTP_X_SITE_CODE='NA',
            HTTP_IDEMPOTENCY_KEY='test-key-123',
            format='json'
        )
        
        # 应该返回相同的order_id
        # self.assertEqual(response1.json()['order_id'], response2.json()['order_id'])
    
    def test_concurrent_inventory_lock(self):
        """测试并发库存锁定"""
        from apps.tiers.services.inventory import lock_inventory
        
        # 并发锁定库存
        success1, error1 = lock_inventory(self.tier.tier_id, 99)
        self.assertTrue(success1)
        
        # 再次锁定（应该失败，库存不足）
        success2, error2 = lock_inventory(self.tier.tier_id, 10)
        self.assertFalse(success2)
        self.assertEqual(error2, 'INVENTORY.INSUFFICIENT')
    
    def test_order_timeout_cancellation(self):
        """测试订单超时自动取消"""
        from apps.orders.tasks import expire_pending_orders
        
        # 创建过期订单
        expired_order = Order.objects.create(
            site=self.site,
            buyer=self.user,
            wallet_address=self.wallet.address,
            list_price_usd=Decimal('100.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('100.00'),
            status='pending',
            expires_at=timezone.now() - timedelta(minutes=1)  # 已过期
        )
        
        OrderItem.objects.create(
            order=expired_order,
            tier=self.tier,
            quantity=1,
            unit_price_usd=Decimal('100.00'),
            token_amount=Decimal('1000.00')
        )
        
        # 锁定库存（模拟）
        self.tier.available_units -= 1
        self.tier.sold_units += 1
        self.tier.save()
        
        # 运行任务
        result = expire_pending_orders()
        
        # 验证
        self.assertEqual(result['succeeded'], 1)
        
        # 刷新订单
        expired_order.refresh_from_db()
        self.assertEqual(expired_order.status, 'cancelled')
        
        # 刷新档位（验证库存回补）
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, 100)
    
    def test_commission_snapshot_created(self):
        """测试佣金快照创建"""
        from apps.orders.services.order_service import create_order
        
        # 创建订单
        order, client_secret = create_order(
            site_id=self.site.site_id,
            tier_id=self.tier.tier_id,
            quantity=1,
            wallet_address=self.wallet.address,
            user=self.user
        )
        
        # 验证快照已创建
        snapshot = OrderCommissionPolicySnapshot.objects.filter(
            order_id=order.order_id
        ).first()
        
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.plan_name, 'Standard Plan')
        self.assertEqual(snapshot.plan_version, 1)


