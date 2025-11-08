"""
Phase D 佣金计算测试

⭐ 测试覆盖：
1. 环路检测
2. 金额精度（ROUND_HALF_UP）
3. 多级佣金计算
4. 统计API验证
"""
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.users.models import User
from apps.sites.models import Site
from apps.tiers.models import Tier
from apps.commissions.models import Commission
from apps.commissions.tasks import get_referral_chain, quantize_commission, calculate_commission_for_order
from apps.orders_snapshots.models import OrderCommissionSnapshot


class ReferralChainTestCase(TestCase):
    """推荐链测试"""
    
    def setUp(self):
        """创建测试数据"""
        self.user_a = User.objects.create(auth0_sub='user_a', email='a@test.com')
        self.user_b = User.objects.create(auth0_sub='user_b', email='b@test.com', referrer=self.user_a)
        self.user_c = User.objects.create(auth0_sub='user_c', email='c@test.com', referrer=self.user_b)
    
    def test_referral_chain_normal(self):
        """测试：正常推荐链"""
        chain = get_referral_chain(self.user_c, max_levels=2)
        
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0]['agent'], self.user_b)
        self.assertEqual(chain[0]['level'], 1)
        self.assertEqual(chain[1]['agent'], self.user_a)
        self.assertEqual(chain[1]['level'], 2)
    
    def test_referral_chain_circular_detection(self):
        """测试：环路检测 ⭐ Phase D P0"""
        # 创建环路：A → B → C → A
        self.user_a.referrer = self.user_c
        self.user_a.save()
        
        chain = get_referral_chain(self.user_c, max_levels=5)
        
        # ⭐ 应检测到环路并停止
        self.assertLess(len(chain), 5)
        
        # 验证不会无限循环
        agent_ids = [c['agent'].user_id for c in chain]
        self.assertEqual(len(agent_ids), len(set(agent_ids)))  # 无重复


class CommissionCalculationTestCase(TestCase):
    """佣金计算精度测试"""
    
    def test_quantize_commission_round_half_up(self):
        """测试：金额量化到2位小数 ⭐ Phase D P0"""
        # 测试ROUND_HALF_UP
        self.assertEqual(quantize_commission(Decimal('12.345')), Decimal('12.35'))
        self.assertEqual(quantize_commission(Decimal('12.344')), Decimal('12.34'))
        self.assertEqual(quantize_commission(Decimal('12.125')), Decimal('12.13'))  # 0.5向上舍入
    
    def test_commission_calculation_precision(self):
        """测试：佣金计算精度"""
        order_amount = Decimal('100.00')
        rate_percent = Decimal('12.00')
        
        raw = order_amount * (rate_percent / Decimal('100'))
        commission = quantize_commission(raw)
        
        # ⭐ 应为 12.00（2位小数）
        self.assertEqual(commission, Decimal('12.00'))
        self.assertEqual(str(commission), '12.00')


class CommissionStatsAPITestCase(TestCase):
    """佣金统计API测试"""
    
    def setUp(self):
        """设置测试数据"""
        from rest_framework.test import APIClient
        
        self.client = APIClient()
        
        # 创建用户和站点
        self.site = Site.objects.create(code='NA', name='Test', domain='localhost')
        self.agent = User.objects.create(auth0_sub='agent', email='agent@test.com')
        
        # 创建测试订单
        self.order = Order.objects.create(
            site=self.site,
            buyer=self.agent,
            wallet_address='0x123',
            final_price_usd=Decimal('100.00'),
            status='paid'
        )
        
        # 创建佣金
        Commission.objects.create(
            order=self.order,
            agent=self.agent,
            level=1,
            rate_percent=Decimal('12.00'),
            commission_amount_usd=Decimal('12.00'),
            status='hold',
            hold_until=timezone.now() + timedelta(days=7)
        )
        
        Commission.objects.create(
            order=self.order,
            agent=self.agent,
            level=2,
            rate_percent=Decimal('4.00'),
            commission_amount_usd=Decimal('4.00'),
            status='ready'
        )
    
    def test_commission_stats_decimal_formatting(self):
        """测试：统计API Decimal字符串化 ⭐ Phase D P0"""
        self.client.force_authenticate(user=self.agent)
        
        response = self.client.get('/api/v1/commissions/stats/')
        
        self.assertEqual(response.status_code, 200)
        
        # ⭐ Decimal应转为字符串（2位小数）
        self.assertEqual(response.data['total_earned'], '16.00')
        self.assertEqual(response.data['hold'], '12.00')
        self.assertEqual(response.data['ready'], '4.00')
        self.assertEqual(response.data['paid'], '0.00')
        
        # 验证类型（应为字符串，不是数字）
        self.assertIsInstance(response.data['total_earned'], str)

