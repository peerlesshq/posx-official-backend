# Phase C 验收清单（15分钟快速验证）

## 🎯 核心验收（7个场景）

### 前置准备

```bash
# 1. 安装依赖
pip install -r backend/requirements/production.txt

# 2. 运行迁移
cd backend
python manage.py migrate

# 3. 加载fixtures
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json

# 4. 配置环境变量
export SIWE_DOMAIN=posx.io
export SIWE_CHAIN_ID=1
export SIWE_URI=https://posx.io
export MOCK_STRIPE=true
export ENV=test

# 5. 启动服务
python manage.py runserver

# 6. 启动Celery（另一个终端）
celery -A config worker -l info
celery -A config beat -l info
```

---

## ✅ 场景1: Nonce生成与重放攻击（2分钟）

```bash
export BASE_URL=http://localhost:8000
export SITE=NA

# 获取nonce
NONCE_RESP=$(curl -s -X POST $BASE_URL/api/v1/auth/nonce \
  -H "X-Site-Code: $SITE")

echo $NONCE_RESP | jq '.'

# ✅ 预期响应
{
  "nonce": "...",  # 32字节随机字符串
  "expires_in": 300,
  "issued_at": "2025-11-08T..."
}

# 测试重放攻击（需要Python脚本或手动验证）
# 1. 第一次消费nonce → 成功
# 2. 第二次消费相同nonce → 失败（AUTH.NONCE_INVALID）
```

**验收标准**:
- ✅ nonce长度 > 20字符
- ✅ expires_in = 300
- ✅ 相同nonce无法重复使用

---

## ✅ 场景2: 金额精度验证（1分钟）

```python
# Python shell
python manage.py shell

from apps.core.utils.money import to_cents, from_cents, quantize_money
from decimal import Decimal

# 测试1: to_cents转换
assert to_cents(Decimal('100.50')) == 10050
assert to_cents(Decimal('0.01')) == 1
assert to_cents(Decimal('99.999999')) == 10000

# 测试2: from_cents转换
assert from_cents(10050) == Decimal('100.500000')
assert from_cents(1) == Decimal('0.010000')

# 测试3: 往返无损（2位小数内）
original = Decimal('123.45')
cents = to_cents(original)
result = from_cents(cents)
assert result == Decimal('123.450000')

print("✅ 金额精度测试通过")
```

**验收标准**:
- ✅ 无浮点误差
- ✅ Stripe金额正确
- ✅ 往返转换一致

---

## ✅ 场景3: 库存并发控制（3分钟）

```bash
# 运行并发库存测试
python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_concurrent_lock_inventory -v 2

# ✅ 预期输出
test_concurrent_lock_inventory ... ok

----------------------------------------------------------------------
Ran 1 test in 0.XXs

OK

# 解释：
# - 10个线程同时锁1个单位
# - 总库存10个
# - 应该恰好10个成功
# - version从0增到10
```

**验收标准**:
- ✅ 测试通过
- ✅ 无超卖
- ✅ version正确递增

---

## ✅ 场景4: 订单幂等性（3分钟）

```bash
# 创建订单（第一次）
ORDER1=$(curl -s -X POST $BASE_URL/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Idempotency-Key: test-idem-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "tier_id": "<tier_id>",
    "quantity": 1,
    "wallet_address": "0xab5801a7d398351b8be11c439e05c5b3259aec9b"
  }')

ORDER_ID1=$(echo $ORDER1 | jq -r '.order_id')
echo "Order ID (1st): $ORDER_ID1"

# 创建订单（第二次，相同幂等键）
ORDER2=$(curl -s -X POST $BASE_URL/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Idempotency-Key: test-idem-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "tier_id": "<tier_id>",
    "quantity": 1,
    "wallet_address": "0xab5801a7d398351b8be11c439e05c5b3259aec9b"
  }')

ORDER_ID2=$(echo $ORDER2 | jq -r '.order_id')
echo "Order ID (2nd): $ORDER_ID2"

# 验证
if [ "$ORDER_ID1" = "$ORDER_ID2" ]; then
  echo "✅ 幂等性验证通过"
else
  echo "❌ 幂等性验证失败"
fi
```

**验收标准**:
- ✅ ORDER_ID1 == ORDER_ID2
- ✅ 库存仅扣减一次

---

## ✅ 场景5: 库存不足返回409（2分钟）

```bash
# 查询档位剩余库存
TIER_INFO=$(curl -s "$BASE_URL/api/v1/tiers/<tier_id>/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE")

AVAILABLE=$(echo $TIER_INFO | jq -r '.available_units')
echo "Available: $AVAILABLE"

# 尝试购买超过库存的数量
CONFLICT_ORDER=$(curl -s -X POST $BASE_URL/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Content-Type: application/json" \
  -d "{
    \"tier_id\": \"<tier_id>\",
    \"quantity\": $((AVAILABLE + 1)),
    \"wallet_address\": \"0xabc...\"
  }")

HTTP_CODE=$(echo $CONFLICT_ORDER | jq -r '.code')
echo "Error Code: $HTTP_CODE"

# ✅ 预期
{
  "code": "INVENTORY.INSUFFICIENT",
  "message": "...",
  "request_id": "..."
}
```

**验收标准**:
- ✅ HTTP 409 Conflict
- ✅ code = "INVENTORY.INSUFFICIENT" 或 "INVENTORY.CONFLICT"
- ✅ 库存未扣减

---

## ✅ 场景6: 订单超时自动取消（2分钟）

```bash
# 手动运行超时任务
python manage.py shell

from apps.orders.tasks import expire_pending_orders
result = expire_pending_orders()

print(result)
# ✅ 预期
{
  'processed': 1,
  'succeeded': 1,
  'failed': 0
}

# 验证订单状态
from apps.orders.models import Order
expired_order = Order.objects.filter(status='cancelled').first()

if expired_order:
    print(f"✅ 订单 {expired_order.order_id} 已自动取消")
    print(f"   取消原因: {expired_order.cancelled_reason}")
    print(f"   取消时间: {expired_order.cancelled_at}")
```

**验收标准**:
- ✅ pending订单超时后变为cancelled
- ✅ cancelled_reason = 'TIMEOUT'
- ✅ 库存已回补

---

## ✅ 场景7: 订单佣金快照创建（2分钟）

```bash
# 创建订单
ORDER=$(curl -s -X POST $BASE_URL/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Content-Type: application/json" \
  -d '{
    "tier_id": "<tier_id>",
    "quantity": 1,
    "wallet_address": "0xabc..."
  }')

ORDER_ID=$(echo $ORDER | jq -r '.order_id')

# 验证快照
python manage.py shell

from apps.orders_snapshots.models import OrderCommissionPolicySnapshot

snapshot = OrderCommissionPolicySnapshot.objects.get(order_id='$ORDER_ID')

print(f"✅ 快照已创建")
print(f"   Plan: {snapshot.plan_name} v{snapshot.plan_version}")
print(f"   Mode: {snapshot.plan_mode}")
print(f"   Tiers: {len(snapshot.tiers_json)} levels")
```

**验收标准**:
- ✅ 快照记录存在
- ✅ plan_name, plan_version正确
- ✅ tiers_json包含所有层级配置

---

## 📊 验收结果汇总

| 场景         | HTTP码 | 关键字段              | 预期结果     |
| ------------ | ------ | --------------------- | ------------ |
| 1. Nonce生成 | 200    | `nonce`, `expires_in` | 300秒TTL     |
| 2. 金额精度  | -      | to_cents/from_cents   | 无精度丢失   |
| 3. 并发库存  | -      | success_count         | 恰好10个成功 |
| 4. 订单幂等  | 200    | `order_id`            | ID相同       |
| 5. 库存不足  | 409    | `code`                | INVENTORY.*  |
| 6. 超时取消  | -      | `status`              | cancelled    |
| 7. 佣金快照  | -      | snapshot              | 已创建       |

---

## 🔍 自动化测试

### 运行所有Phase C测试

```bash
cd backend

# 金额工具测试
python manage.py test apps.core.tests_money

# SIWE认证测试
python manage.py test apps.users.tests_siwe

# 库存并发测试
python manage.py test apps.tiers.tests_inventory

# 端到端测试
python manage.py test apps.orders.tests_e2e

# 所有测试
python manage.py test
```

**预期输出**:
```
Ran 29 tests in 2.5s

OK
```

---

## ⚠️ 故障排查

### 问题1: siwe库导入失败

```bash
# 检查依赖
pip list | grep siwe

# 如果缺失
pip install siwe==2.1.1 eth-account==0.10.0
```

### 问题2: 订单创建失败

```bash
# 查看日志
tail -f logs/django.log | grep "ORDER"

# 常见错误：
# - TIER.NOT_FOUND: 档位不存在
# - INVENTORY.INSUFFICIENT: 库存不足
# - INVENTORY.CONFLICT: 并发冲突
```

### 问题3: Celery任务未运行

```bash
# 检查Celery状态
celery -A config inspect active

# 检查Beat调度
celery -A config beat -l info

# 手动触发
python manage.py shell
from apps.orders.tasks import expire_pending_orders
expire_pending_orders()
```

### 问题4: 快照未创建

```bash
# 检查佣金计划
python manage.py shell

from apps.commission_plans.models import CommissionPlan
active_plans = CommissionPlan.objects.filter(is_active=True)
print(f"Active plans: {active_plans.count()}")

# 如果为0，加载fixtures
python manage.py loaddata fixtures/seed_commission_plans.json
```

---

## 📋 最小验收清单（必须100%通过）

- [ ] Nonce生成返回200 + nonce字段
- [ ] Nonce重放攻击被拒绝
- [ ] to_cents(Decimal('100.50')) == 10050
- [ ] 并发库存测试通过（无超卖）
- [ ] 相同Idempotency-Key返回相同order_id
- [ ] 库存不足返回409 + INVENTORY.*
- [ ] 订单超时15分钟后自动cancelled
- [ ] 每个订单都有OrderCommissionPolicySnapshot

---

## 🚀 快速验收脚本（一键运行）

```bash
#!/bin/bash
# phase_c_acceptance.sh

echo "🧪 Phase C 验收测试"
echo "==================="

# 1. 金额工具测试
echo ""
echo "1️⃣ 金额精度测试..."
python manage.py test apps.core.tests_money.MoneyUtilsTestCase.test_to_cents -v 0
if [ $? -eq 0 ]; then
  echo "✅ 金额精度测试通过"
else
  echo "❌ 金额精度测试失败"
fi

# 2. Nonce服务测试
echo ""
echo "2️⃣ Nonce服务测试..."
python manage.py test apps.users.tests_siwe.NonceServiceTestCase.test_generate_and_consume_nonce -v 0
if [ $? -eq 0 ]; then
  echo "✅ Nonce服务测试通过"
else
  echo "❌ Nonce服务测试失败"
fi

# 3. 并发库存测试
echo ""
echo "3️⃣ 并发库存测试..."
python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_concurrent_lock_inventory -v 0
if [ $? -eq 0 ]; then
  echo "✅ 并发库存测试通过"
else
  echo "❌ 并发库存测试失败"
fi

# 4. 订单快照测试
echo ""
echo "4️⃣ 订单快照测试..."
python manage.py test apps.orders.tests_e2e.OrderE2ETestCase.test_commission_snapshot_created -v 0
if [ $? -eq 0 ]; then
  echo "✅ 订单快照测试通过"
else
  echo "❌ 订单快照测试失败"
fi

# 5. 超时取消测试
echo ""
echo "5️⃣ 超时取消测试..."
python manage.py test apps.orders.tests_e2e.OrderE2ETestCase.test_order_timeout_cancellation -v 0
if [ $? -eq 0 ]; then
  echo "✅ 超时取消测试通过"
else
  echo "❌ 超时取消测试失败"
fi

echo ""
echo "==================="
echo "✅ Phase C 验收完成"
```

使用方法:
```bash
cd backend
chmod +x phase_c_acceptance.sh
./phase_c_acceptance.sh
```

---

## 📝 验收签字

| 验收项              | 状态 | 备注 |
| ------------------- | ---- | ---- |
| Nonce生成与重放保护 | ⬜    |      |
| 金额精度（Decimal） | ⬜    |      |
| 库存并发控制        | ⬜    |      |
| 订单幂等性          | ⬜    |      |
| 库存不足返回409     | ⬜    |      |
| 订单超时自动取消    | ⬜    |      |
| 佣金快照创建        | ⬜    |      |

**验收人**: _____________  
**验收日期**: _____________  
**验收结果**: [ ] 通过 / [ ] 不通过  
**备注**: _________________________

---

## 🎉 验收通过后

### 下一步

1. **Phase D准备**:
   - Stripe Webhook集成
   - 代币分配流程
   - 佣金计算引擎

2. **性能优化**（可选）:
   - 档位列表缓存
   - 库存计数器优化
   - 查询索引优化

3. **监控部署**:
   - Sentry错误追踪
   - 订单状态监控
   - 库存告警

---

**验收清单版本**: v1.0  
**更新日期**: 2025-11-08


