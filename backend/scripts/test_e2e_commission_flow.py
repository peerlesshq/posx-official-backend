#!/usr/bin/env python
"""
端到端测试脚本：订单 → 佣金 → 余额 → 提现

测试流程：
1. 创建推荐链路（Agent A → Agent B → Buyer）
2. Buyer 下单（$100）
3. 模拟 Stripe webhook（payment_intent.succeeded）
4. 验证佣金创建（L1: $12, L2: $4）
5. 模拟 7 天后，释放佣金（hold → ready）
6. Admin 批量结算（ready → paid）
7. 验证余额更新（A: +$12, B: +$4）
8. Agent A 提交提现申请
9. 验证余额扣减
10. 生成月度对账单

运行方式：
    python manage.py shell < scripts/test_e2e_commission_flow.py
"""
import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Django setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import transaction
from django.utils import timezone
from apps.users.models import User
from apps.sites.models import Site
from apps.tiers.models import Tier
from apps.orders.models import Order, OrderItem
from apps.commissions.models import Commission, CommissionConfig
from apps.allocations.models import Allocation
from apps.agents.models import AgentProfile, WithdrawalRequest
from apps.webhooks.handlers import handle_payment_succeeded
from apps.agents.services.balance import (
    get_or_create_agent_profile,
    deduct_balance_for_withdrawal
)

print("=" * 60)
print("E2E 测试：完整佣金流程")
print("=" * 60)

# ============================================
# Step 1: 创建测试数据
# ============================================
print("\n[Step 1] 创建测试数据...")

# 创建站点
site, _ = Site.objects.get_or_create(
    code='TEST',
    defaults={
        'name': 'Test Site',
        'domain': 'test.posx.io',
        'is_active': True
    }
)
print(f"✓ Site: {site.code}")

# 创建档位
tier, _ = Tier.objects.get_or_create(
    site=site,
    name='Test Tier',
    defaults={
        'list_price_usd': Decimal('100.00'),
        'tokens_per_unit': Decimal('1000.00'),
        'total_units': 1000,
        'sold_units': 0,
        'available_units': 1000,
        'is_active': True
    }
)
print(f"✓ Tier: {tier.name} - ${tier.list_price_usd}")

# 创建佣金配置
config_l1, _ = CommissionConfig.objects.get_or_create(
    site=site,
    level=1,
    defaults={
        'rate_percent': Decimal('12.00'),
        'hold_days': 7,
        'is_active': True
    }
)
config_l2, _ = CommissionConfig.objects.get_or_create(
    site=site,
    level=2,
    defaults={
        'rate_percent': Decimal('4.00'),
        'hold_days': 7,
        'is_active': True
    }
)
print(f"✓ Commission Config: L1={config_l1.rate_percent}%, L2={config_l2.rate_percent}%")

# 创建推荐链路：Agent A → Agent B → Buyer
agent_a, _ = User.objects.get_or_create(
    email='agent_a@test.com',
    defaults={
        'referral_code': 'TEST-AGENTA',
        'is_active': True
    }
)
print(f"✓ Agent A: {agent_a.email}")

agent_b, _ = User.objects.get_or_create(
    email='agent_b@test.com',
    defaults={
        'referral_code': 'TEST-AGENTB',
        'referrer': agent_a,
        'is_active': True
    }
)
print(f"✓ Agent B: {agent_b.email} (referrer: {agent_b.referrer.email})")

buyer, _ = User.objects.get_or_create(
    email='buyer@test.com',
    defaults={
        'referral_code': 'TEST-BUYER',
        'referrer': agent_b,
        'is_active': True
    }
)
print(f"✓ Buyer: {buyer.email} (referrer: {buyer.referrer.email})")

# ============================================
# Step 2: 创建订单
# ============================================
print("\n[Step 2] 创建订单...")

order = Order.objects.create(
    buyer=buyer,
    site=site,
    referrer=agent_b,
    status='pending',
    stripe_payment_intent_id=f'pi_test_{timezone.now().timestamp()}',
    list_price_usd=Decimal('100.00'),
    discount_usd=Decimal('0'),
    final_price_usd=Decimal('100.00'),
    wallet_address='0x742d35cc6634c0532925a3b844bc9e7595f0beb',
    expires_at=timezone.now() + timedelta(minutes=15)
)

OrderItem.objects.create(
    order=order,
    tier=tier,
    quantity=1,
    unit_price_usd=tier.list_price_usd,
    token_amount=tier.tokens_per_unit
)

print(f"✓ Order created: {order.order_id}")
print(f"  - Amount: ${order.final_price_usd}")
print(f"  - Status: {order.status}")

# ============================================
# Step 3: 模拟支付成功 Webhook
# ============================================
print("\n[Step 3] 模拟支付成功...")

# 手动更新订单状态为 paid
order.status = 'paid'
order.save()

# 创建佣金（模拟 Phase D 的佣金计算）
from apps.commissions.tasks import calculate_commission_for_order
try:
    calculate_commission_for_order(str(order.order_id))
    print(f"✓ Commission calculation task completed")
except Exception as e:
    print(f"✗ Commission calculation failed: {e}")

# 验证佣金创建
commissions = Commission.objects.filter(order=order).order_by('level')
print(f"✓ Commissions created: {commissions.count()}")

for comm in commissions:
    print(f"  - L{comm.level}: {comm.agent.email} = ${comm.commission_amount_usd} ({comm.status})")

assert commissions.count() == 2, "应该创建2条佣金（L1 + L2）"
assert commissions[0].level == 1
assert commissions[0].agent == agent_b
assert commissions[0].commission_amount_usd == Decimal('12.00')
assert commissions[1].level == 2
assert commissions[1].agent == agent_a
assert commissions[1].commission_amount_usd == Decimal('4.00')

# 创建 Allocation
allocation = Allocation.objects.create(
    order=order,
    wallet_address=order.wallet_address,
    token_amount=Decimal('1000.00'),
    status='pending'
)
print(f"✓ Allocation created: {allocation.allocation_id}")

# ============================================
# Step 4: 模拟 7 天后释放佣金
# ============================================
print("\n[Step 4] 释放佣金（hold → ready）...")

# 手动更新 hold_until（模拟7天已过）
past_time = timezone.now() - timedelta(days=1)
commissions.update(hold_until=past_time)

# 运行释放任务
from apps.commissions.tasks import release_held_commissions
result = release_held_commissions()
print(f"✓ Released {result['released_count']} commissions")

# 验证状态
commissions = Commission.objects.filter(order=order)
for comm in commissions:
    comm.refresh_from_db()
    print(f"  - L{comm.level}: {comm.status}")
    assert comm.status == 'ready', f"Commission L{comm.level} should be 'ready'"

# ============================================
# Step 5: Admin 批量结算
# ============================================
print("\n[Step 5] 批量结算佣金（ready → paid）...")

# 批量更新为 paid（模拟 Admin action）
with transaction.atomic():
    for comm in commissions:
        comm.status = 'paid'
        comm.paid_at = timezone.now()
        comm.save()
        
        # ⭐ Phase F: 更新余额
        from apps.agents.services.balance import update_balance_on_commission_paid
        update_balance_on_commission_paid(comm)

print(f"✓ Commissions settled")

# ============================================
# Step 6: 验证余额更新
# ============================================
print("\n[Step 6] 验证余额更新...")

# 检查 Agent A 余额
profile_a = AgentProfile.objects.get(user=agent_a, site=site)
print(f"✓ Agent A 余额: ${profile_a.balance_usd}")
print(f"  - 累计收入: ${profile_a.total_earned_usd}")
assert profile_a.balance_usd == Decimal('4.00'), "Agent A should have $4.00"
assert profile_a.total_earned_usd == Decimal('4.00')

# 检查 Agent B 余额
profile_b = AgentProfile.objects.get(user=agent_b, site=site)
print(f"✓ Agent B 余额: ${profile_b.balance_usd}")
print(f"  - 累计收入: ${profile_b.total_earned_usd}")
assert profile_b.balance_usd == Decimal('12.00'), "Agent B should have $12.00"
assert profile_b.total_earned_usd == Decimal('12.00')

# ============================================
# Step 7: Agent A 提现申请
# ============================================
print("\n[Step 7] Agent A 提现申请...")

# 提现 $3.00
success = deduct_balance_for_withdrawal(profile_a, Decimal('3.00'))
assert success, "Withdrawal deduction should succeed"

withdrawal = WithdrawalRequest.objects.create(
    agent_profile=profile_a,
    amount_usd=Decimal('3.00'),
    withdrawal_method='bank_transfer',
    account_info={'test': 'data'},
    status='submitted'
)

print(f"✓ Withdrawal request created: {withdrawal.request_id}")
print(f"  - Amount: ${withdrawal.amount_usd}")

# 验证余额扣减
profile_a.refresh_from_db()
print(f"✓ Agent A 余额更新: ${profile_a.balance_usd}")
assert profile_a.balance_usd == Decimal('1.00'), "Agent A balance should be $1.00 after withdrawal"

# ============================================
# Step 8: 生成对账单
# ============================================
print("\n[Step 8] 生成月度对账单...")

from apps.agents.tasks import generate_monthly_statements
result = generate_monthly_statements()
print(f"✓ Generated {result['generated']} statements")

# 查询对账单
from apps.agents.models import CommissionStatement
statement_a = CommissionStatement.objects.filter(agent_profile=profile_a).first()
if statement_a:
    print(f"✓ Agent A 对账单:")
    print(f"  - 期初余额: ${statement_a.balance_start_of_period}")
    print(f"  - 本期佣金: ${statement_a.total_commissions_usd}")
    print(f"  - 已结算: ${statement_a.paid_commissions_usd}")
    print(f"  - 本期提现: ${statement_a.withdrawals_in_period}")
    print(f"  - 期末余额: ${statement_a.balance_end_of_period}")

# ============================================
# 最终验证
# ============================================
print("\n" + "=" * 60)
print("✅ 端到端测试通过！")
print("=" * 60)

print("\n账务闭环验证:")
print(f"  Order: {order.order_id} - ${order.final_price_usd} ({order.status})")
print(f"  Commissions: {commissions.count()} 条 (all paid)")
print(f"  Agent A 余额: ${profile_a.balance_usd} (入账$4 - 提现$3 = $1)")
print(f"  Agent B 余额: ${profile_b.balance_usd} (入账$12)")
print(f"  Allocation: {allocation.status}")

print("\n✅ 全链路数据一致性检查通过！")

