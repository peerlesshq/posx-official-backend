"""
Commission Calculation Tests（P0 功能测试）

测试范围：
1. 销售额门槛验证
2. 动态层级数支持
3. 字段命名兼容性
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from uuid import uuid4

from apps.orders.models import Order
from apps.commissions.models import Commission
from apps.commissions.tasks import calculate_commission_for_order
from apps.agents.models import AgentStats
from apps.orders_snapshots.models import OrderCommissionPolicySnapshot
from apps.users.models import User
from apps.sites.models import Site
from apps.tiers.models import Tier


@pytest.mark.django_db
class TestMinSalesThreshold:
    """测试销售额门槛验证"""
    
    def test_commission_skipped_when_below_threshold(self):
        """
        测试：代理销售额低于门槛时跳过佣金
        
        场景：
        - Agent A 累计销售 $300
        - 佣金方案：L1 无门槛，L2 需 $500
        - 买家 B 由 A 推荐，购买 $1000
        - 期望：L1 佣金创建，L2 佣金跳过
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='TEST',
            name='Test Site',
            domain='test.local',
            is_active=True
        )
        
        # 2. 创建代理链：Agent A <- Buyer B
        agent_a = User.objects.create(
            email='agent_a@test.com',
            referral_code='AGENT-A',
            is_active=True
        )
        buyer_b = User.objects.create(
            email='buyer_b@test.com',
            referral_code='BUYER-B',
            referrer=agent_a,
            is_active=True
        )
        
        # 3. 设置 Agent A 的累计销售额 $300（低于 L2 门槛 $500）
        AgentStats.objects.create(
            site_id=site.site_id,
            agent=agent_a.user_id,
            total_sales=Decimal('300.00'),
            direct_customers=1,
            total_customers=1,
            total_commissions=Decimal('0')
        )
        
        # 4. 创建产品
        tier = Tier.objects.create(
            site=site,
            name='Test Tier',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        # 5. 创建订单
        order = Order.objects.create(
            site=site,
            buyer=buyer_b,
            referrer=agent_a,
            wallet_address='0x1234567890abcdef',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 6. 创建佣金快照：L1 无门槛，L2 需 $500
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Test Plan',
            plan_version=1,
            plan_mode='level',
            diff_reward_enabled=False,
            tiers_json=[
                {
                    'level': 1,
                    'rate_percent': '12.00',
                    'min_sales': '0.00',  # L1 无门槛
                    'hold_days': 7
                },
                {
                    'level': 2,
                    'rate_percent': '4.00',
                    'min_sales': '500.00',  # L2 需 $500
                    'hold_days': 7
                }
            ]
        )
        
        # 7. 执行佣金计算
        calculate_commission_for_order(str(order.order_id))
        
        # 8. 断言：仅创建 L1 佣金
        commissions = Commission.objects.filter(order=order)
        assert commissions.count() == 1, "应该只创建1条佣金（L1）"
        
        l1_commission = commissions.filter(level=1).first()
        assert l1_commission is not None, "L1 佣金应该被创建"
        assert l1_commission.agent == agent_a
        assert l1_commission.rate_percent == Decimal('12.00')
        assert l1_commission.commission_amount_usd == Decimal('120.00')  # $1000 * 12%
        
        l2_commission = commissions.filter(level=2).first()
        assert l2_commission is None, "L2 佣金应该被跳过（销售额不足）"
    
    def test_commission_created_when_above_threshold(self):
        """
        测试：代理销售额达到门槛时创建佣金
        
        场景：
        - Agent A 累计销售 $600
        - 佣金方案：L1 无门槛，L2 需 $500
        - 买家 B 由 A 推荐，购买 $1000
        - 期望：L1 和 L2 佣金都创建
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='TEST2',
            name='Test Site 2',
            domain='test2.local',
            is_active=True
        )
        
        # 2. 创建代理链
        agent_a = User.objects.create(
            email='agent_a2@test.com',
            referral_code='AGENT-A2',
            is_active=True
        )
        buyer_b = User.objects.create(
            email='buyer_b2@test.com',
            referral_code='BUYER-B2',
            referrer=agent_a,
            is_active=True
        )
        
        # 3. 设置 Agent A 的累计销售额 $600（高于 L2 门槛 $500）
        AgentStats.objects.create(
            site_id=site.site_id,
            agent=agent_a.user_id,
            total_sales=Decimal('600.00'),
            direct_customers=1,
            total_customers=1,
            total_commissions=Decimal('0')
        )
        
        # 4. 创建产品
        tier = Tier.objects.create(
            site=site,
            name='Test Tier 2',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        # 5. 创建订单
        order = Order.objects.create(
            site=site,
            buyer=buyer_b,
            referrer=agent_a,
            wallet_address='0xabcdef1234567890',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 6. 创建佣金快照
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Test Plan 2',
            plan_version=1,
            plan_mode='level',
            diff_reward_enabled=False,
            tiers_json=[
                {
                    'level': 1,
                    'rate_percent': '12.00',
                    'min_sales': '0.00',
                    'hold_days': 7
                },
                {
                    'level': 2,
                    'rate_percent': '4.00',
                    'min_sales': '500.00',
                    'hold_days': 7
                }
            ]
        )
        
        # 7. 执行佣金计算
        calculate_commission_for_order(str(order.order_id))
        
        # 8. 断言：创建 L1 和 L2 佣金
        commissions = Commission.objects.filter(order=order)
        assert commissions.count() == 2, "应该创建2条佣金（L1 + L2）"
        
        l1_commission = commissions.filter(level=1).first()
        assert l1_commission is not None
        assert l1_commission.commission_amount_usd == Decimal('120.00')
        
        l2_commission = commissions.filter(level=2).first()
        assert l2_commission is not None
        assert l2_commission.commission_amount_usd == Decimal('40.00')  # $1000 * 4%


@pytest.mark.django_db
class TestDynamicLevels:
    """测试动态层级数支持"""
    
    def test_five_level_commission(self):
        """
        测试：5级佣金配置
        
        场景：
        - 配置5级佣金方案
        - 创建5层推荐链
        - 验证5条佣金记录都被创建
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='TEST3',
            name='Test Site 3',
            domain='test3.local',
            is_active=True
        )
        
        # 2. 创建5层推荐链：L5 <- L4 <- L3 <- L2 <- L1 <- Buyer
        agent_l5 = User.objects.create(
            email='agent_l5@test.com',
            referral_code='AGENT-L5',
            is_active=True
        )
        agent_l4 = User.objects.create(
            email='agent_l4@test.com',
            referral_code='AGENT-L4',
            referrer=agent_l5,
            is_active=True
        )
        agent_l3 = User.objects.create(
            email='agent_l3@test.com',
            referral_code='AGENT-L3',
            referrer=agent_l4,
            is_active=True
        )
        agent_l2 = User.objects.create(
            email='agent_l2@test.com',
            referral_code='AGENT-L2',
            referrer=agent_l3,
            is_active=True
        )
        agent_l1 = User.objects.create(
            email='agent_l1@test.com',
            referral_code='AGENT-L1',
            referrer=agent_l2,
            is_active=True
        )
        buyer = User.objects.create(
            email='buyer@test.com',
            referral_code='BUYER',
            referrer=agent_l1,
            is_active=True
        )
        
        # 3. 创建产品
        tier = Tier.objects.create(
            site=site,
            name='Test Tier 3',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        # 4. 创建订单
        order = Order.objects.create(
            site=site,
            buyer=buyer,
            referrer=agent_l1,
            wallet_address='0x5555555555555555',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 5. 创建5级佣金快照
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='5-Level Plan',
            plan_version=1,
            plan_mode='level',
            diff_reward_enabled=False,
            tiers_json=[
                {'level': 1, 'rate_percent': '12.00', 'min_sales': '0', 'hold_days': 7},
                {'level': 2, 'rate_percent': '5.00', 'min_sales': '0', 'hold_days': 7},
                {'level': 3, 'rate_percent': '3.00', 'min_sales': '0', 'hold_days': 7},
                {'level': 4, 'rate_percent': '2.00', 'min_sales': '0', 'hold_days': 7},
                {'level': 5, 'rate_percent': '1.00', 'min_sales': '0', 'hold_days': 7},
            ]
        )
        
        # 6. 执行佣金计算
        calculate_commission_for_order(str(order.order_id))
        
        # 7. 断言：创建5条佣金记录
        commissions = Commission.objects.filter(order=order).order_by('level')
        assert commissions.count() == 5, "应该创建5条佣金记录"
        
        # 验证每一级
        expected_amounts = [
            (1, agent_l1, Decimal('120.00')),  # 12%
            (2, agent_l2, Decimal('50.00')),   # 5%
            (3, agent_l3, Decimal('30.00')),   # 3%
            (4, agent_l4, Decimal('20.00')),   # 2%
            (5, agent_l5, Decimal('10.00')),   # 1%
        ]
        
        for idx, (level, agent, expected_amount) in enumerate(expected_amounts):
            comm = commissions[idx]
            assert comm.level == level, f"Level {idx+1} 应该是 {level}"
            assert comm.agent == agent, f"Level {level} 代理不匹配"
            assert comm.commission_amount_usd == expected_amount, f"Level {level} 金额不匹配"


@pytest.mark.django_db
class TestFieldNaming:
    """测试字段命名兼容性"""
    
    def test_min_order_amount_compatibility(self):
        """
        测试：兼容 min_order_amount 字段名
        
        场景：
        - 快照使用 min_order_amount 而非 min_sales
        - 验证门槛验证仍然生效
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='TEST4',
            name='Test Site 4',
            domain='test4.local',
            is_active=True
        )
        
        # 2. 创建代理链
        agent_a = User.objects.create(
            email='agent_a4@test.com',
            referral_code='AGENT-A4',
            is_active=True
        )
        buyer_b = User.objects.create(
            email='buyer_b4@test.com',
            referral_code='BUYER-B4',
            referrer=agent_a,
            is_active=True
        )
        
        # 3. 设置销售额低于门槛
        AgentStats.objects.create(
            site_id=site.site_id,
            agent=agent_a.user_id,
            total_sales=Decimal('200.00'),
            direct_customers=1,
            total_customers=1,
            total_commissions=Decimal('0')
        )
        
        # 4. 创建产品
        tier = Tier.objects.create(
            site=site,
            name='Test Tier 4',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        # 5. 创建订单
        order = Order.objects.create(
            site=site,
            buyer=buyer_b,
            referrer=agent_a,
            wallet_address='0x4444444444444444',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 6. 创建快照：使用 min_order_amount 而非 min_sales
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Test Plan 4',
            plan_version=1,
            plan_mode='level',
            diff_reward_enabled=False,
            tiers_json=[
                {
                    'level': 1,
                    'rate_percent': '12.00',
                    'min_order_amount': '0.00',  # 使用 min_order_amount
                    'hold_days': 7
                },
                {
                    'level': 2,
                    'rate_percent': '4.00',
                    'min_order_amount': '500.00',  # 使用 min_order_amount
                    'hold_days': 7
                }
            ]
        )
        
        # 7. 执行佣金计算
        calculate_commission_for_order(str(order.order_id))
        
        # 8. 断言：L2 因门槛被跳过（兼容性验证）
        commissions = Commission.objects.filter(order=order)
        assert commissions.count() == 1, "应该只创建1条佣金（L1）"
        assert commissions.first().level == 1


@pytest.mark.django_db
class TestEdgeCases:
    """测试边界情况"""
    
    def test_no_stats_defaults_to_zero_sales(self):
        """
        测试：代理无统计记录时，默认销售额为0
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='TEST5',
            name='Test Site 5',
            domain='test5.local',
            is_active=True
        )
        
        # 2. 创建代理链（不创建 AgentStats）
        agent_a = User.objects.create(
            email='agent_a5@test.com',
            referral_code='AGENT-A5',
            is_active=True
        )
        buyer_b = User.objects.create(
            email='buyer_b5@test.com',
            referral_code='BUYER-B5',
            referrer=agent_a,
            is_active=True
        )
        
        # 注意：不创建 AgentStats
        
        # 3. 创建产品
        tier = Tier.objects.create(
            site=site,
            name='Test Tier 5',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        # 4. 创建订单
        order = Order.objects.create(
            site=site,
            buyer=buyer_b,
            referrer=agent_a,
            wallet_address='0x5151515151515151',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 5. 创建快照：L2 需 $100
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Test Plan 5',
            plan_version=1,
            plan_mode='level',
            diff_reward_enabled=False,
            tiers_json=[
                {
                    'level': 1,
                    'rate_percent': '12.00',
                    'min_sales': '0.00',
                    'hold_days': 7
                },
                {
                    'level': 2,
                    'rate_percent': '4.00',
                    'min_sales': '100.00',  # 需 $100
                    'hold_days': 7
                }
            ]
        )
        
        # 6. 执行佣金计算
        calculate_commission_for_order(str(order.order_id))
        
        # 7. 断言：L2 被跳过（默认销售额=0）
        commissions = Commission.objects.filter(order=order)
        assert commissions.count() == 1, "应该只创建1条佣金（L1）"
        assert commissions.first().level == 1

