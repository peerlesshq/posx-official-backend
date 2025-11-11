"""
Solar Diff 模式测试

测试范围：
1. 差额计算逻辑
2. 差额封顶功能
3. 等级不足跳过
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from apps.orders.models import Order
from apps.commissions.models import Commission
from apps.commissions.tasks import calculate_commission_for_order
from apps.agents.models import AgentProfile
from apps.orders_snapshots.models import OrderCommissionPolicySnapshot
from apps.users.models import User
from apps.sites.models import Site
from apps.tiers.models import Tier


@pytest.mark.django_db
class TestSolarDiffMode:
    """测试 Solar Diff 差额模式"""
    
    def test_basic_solar_diff_calculation(self):
        """
        测试：基础差额计算
        
        场景：
        - 买家（Bronze 10%）购买 $1000
        - 直推人（Gold 20%）
        - 间推人（Platinum 25%）
        
        期望：
        - L1 佣金：(20% - 10%) × $1000 = $100
        - L2 佣金：(25% - 20%) × $1000 = $50
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='SOLAR1',
            name='Solar Test 1',
            domain='solar1.local',
            is_active=True
        )
        
        # 2. 创建代理链：Platinum <- Gold <- Bronze(买家)
        agent_platinum = User.objects.create(
            email='platinum@test.com',
            referral_code='PLATINUM',
            is_active=True
        )
        agent_gold = User.objects.create(
            email='gold@test.com',
            referral_code='GOLD',
            referrer=agent_platinum,
            is_active=True
        )
        buyer_bronze = User.objects.create(
            email='bronze@test.com',
            referral_code='BRONZE',
            referrer=agent_gold,
            is_active=True
        )
        
        # 3. 设置代理等级
        AgentProfile.objects.create(
            user=buyer_bronze,
            site=site,
            agent_level=AgentProfile.LEVEL_BRONZE  # 10%
        )
        AgentProfile.objects.create(
            user=agent_gold,
            site=site,
            agent_level=AgentProfile.LEVEL_GOLD  # 20%
        )
        AgentProfile.objects.create(
            user=agent_platinum,
            site=site,
            agent_level=AgentProfile.LEVEL_PLATINUM  # 25%
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
            buyer=buyer_bronze,
            referrer=agent_gold,
            wallet_address='0xSOLAR1',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 6. 创建 Solar Diff 快照
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Solar Diff Plan',
            plan_version=1,
            plan_mode='solar_diff',  # ⭐ 使用 solar_diff 模式
            diff_reward_enabled=True,
            tiers_json=[
                {
                    'level': 1,
                    'rate_percent': '0',  # Solar Diff 模式不使用固定费率
                    'min_sales': '0',
                    'hold_days': 7
                },
                {
                    'level': 2,
                    'rate_percent': '0',
                    'min_sales': '0',
                    'hold_days': 7
                }
            ]
        )
        
        # 7. 执行佣金计算
        calculate_commission_for_order(str(order.order_id))
        
        # 8. 断言：创建2条佣金，金额为差额
        commissions = Commission.objects.filter(order=order).order_by('level')
        assert commissions.count() == 2, "应该创建2条佣金"
        
        # L1：Gold(20%) - Bronze(10%) = 10%
        l1_commission = commissions[0]
        assert l1_commission.level == 1
        assert l1_commission.agent == agent_gold
        assert l1_commission.rate_percent == Decimal('10.00')  # 差额费率
        assert l1_commission.commission_amount_usd == Decimal('100.00')  # $1000 × 10%
        
        # L2：Platinum(25%) - Gold(20%) = 5%
        l2_commission = commissions[1]
        assert l2_commission.level == 2
        assert l2_commission.agent == agent_platinum
        assert l2_commission.rate_percent == Decimal('5.00')  # 差额费率
        assert l2_commission.commission_amount_usd == Decimal('50.00')  # $1000 × 5%
    
    def test_solar_diff_with_same_level(self):
        """
        测试：上级等级与下级相同时跳过
        
        场景：
        - 买家（Silver 15%）
        - 直推人（Silver 15%）- 差额=0，应跳过
        - 间推人（Gold 20%）- 差额=(20%-15%)=5%
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='SOLAR2',
            name='Solar Test 2',
            domain='solar2.local',
            is_active=True
        )
        
        # 2. 创建代理链
        agent_gold = User.objects.create(
            email='gold2@test.com',
            referral_code='GOLD2',
            is_active=True
        )
        agent_silver = User.objects.create(
            email='silver2@test.com',
            referral_code='SILVER2',
            referrer=agent_gold,
            is_active=True
        )
        buyer_silver = User.objects.create(
            email='buyer_silver@test.com',
            referral_code='BUYER-SILVER',
            referrer=agent_silver,
            is_active=True
        )
        
        # 3. 设置代理等级（买家和直推人都是 Silver）
        AgentProfile.objects.create(
            user=buyer_silver,
            site=site,
            agent_level=AgentProfile.LEVEL_SILVER  # 15%
        )
        AgentProfile.objects.create(
            user=agent_silver,
            site=site,
            agent_level=AgentProfile.LEVEL_SILVER  # 15%（与买家相同）
        )
        AgentProfile.objects.create(
            user=agent_gold,
            site=site,
            agent_level=AgentProfile.LEVEL_GOLD  # 20%
        )
        
        # 4. 创建产品和订单
        tier = Tier.objects.create(
            site=site,
            name='Test Tier 2',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        order = Order.objects.create(
            site=site,
            buyer=buyer_silver,
            referrer=agent_silver,
            wallet_address='0xSOLAR2',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 5. 创建快照
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Solar Diff Plan 2',
            plan_version=1,
            plan_mode='solar_diff',
            diff_reward_enabled=True,
            tiers_json=[
                {'level': 1, 'rate_percent': '0', 'min_sales': '0', 'hold_days': 7},
                {'level': 2, 'rate_percent': '0', 'min_sales': '0', 'hold_days': 7}
            ]
        )
        
        # 6. 执行计算
        calculate_commission_for_order(str(order.order_id))
        
        # 7. 断言：仅创建 L2 佣金（L1 因差额=0被跳过）
        commissions = Commission.objects.filter(order=order)
        assert commissions.count() == 1, "应该只创建1条佣金（L2）"
        
        commission = commissions.first()
        assert commission.level == 2
        assert commission.agent == agent_gold
        assert commission.rate_percent == Decimal('5.00')  # 20% - 15%
        assert commission.commission_amount_usd == Decimal('50.00')
    
    def test_solar_diff_with_cap(self):
        """
        测试：差额封顶功能
        
        场景：
        - 买家（Bronze 10%）
        - 直推人（Platinum 25%）- 差额=15%，但封顶8%
        
        期望：
        - L1 佣金：min(15%, 8%) = 8% × $1000 = $80
        """
        # 1. 创建站点
        site = Site.objects.create(
            code='SOLAR3',
            name='Solar Test 3',
            domain='solar3.local',
            is_active=True
        )
        
        # 2. 创建代理链
        agent_platinum = User.objects.create(
            email='platinum3@test.com',
            referral_code='PLATINUM3',
            is_active=True
        )
        buyer_bronze = User.objects.create(
            email='bronze3@test.com',
            referral_code='BRONZE3',
            referrer=agent_platinum,
            is_active=True
        )
        
        # 3. 设置代理等级
        AgentProfile.objects.create(
            user=buyer_bronze,
            site=site,
            agent_level=AgentProfile.LEVEL_BRONZE  # 10%
        )
        AgentProfile.objects.create(
            user=agent_platinum,
            site=site,
            agent_level=AgentProfile.LEVEL_PLATINUM  # 25%
        )
        
        # 4. 创建产品和订单
        tier = Tier.objects.create(
            site=site,
            name='Test Tier 3',
            list_price_usd=Decimal('1000.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            sold_units=0,
            available_units=100
        )
        
        order = Order.objects.create(
            site=site,
            buyer=buyer_bronze,
            referrer=agent_platinum,
            wallet_address='0xSOLAR3',
            list_price_usd=Decimal('1000.00'),
            discount_usd=Decimal('0'),
            final_price_usd=Decimal('1000.00'),
            status=Order.STATUS_PAID
        )
        
        # 5. 创建快照：设置差额封顶 8%
        OrderCommissionPolicySnapshot.objects.create(
            order_id=order.order_id,
            plan_id=uuid4(),
            plan_name='Solar Diff Capped',
            plan_version=1,
            plan_mode='solar_diff',
            diff_reward_enabled=True,
            tiers_json=[
                {
                    'level': 1,
                    'rate_percent': '0',
                    'min_sales': '0',
                    'diff_cap_percent': '8.00',  # ⭐ 封顶 8%
                    'hold_days': 7
                }
            ]
        )
        
        # 6. 执行计算
        calculate_commission_for_order(str(order.order_id))
        
        # 7. 断言：差额被封顶到8%
        commission = Commission.objects.get(order=order)
        assert commission.rate_percent == Decimal('8.00'), "差额应该被封顶到8%"
        assert commission.commission_amount_usd == Decimal('80.00'), "佣金应该是 $1000 × 8% = $80"

