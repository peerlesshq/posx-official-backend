# POSX Phase C 实施总结

## 📋 概述

Phase C 实施了 **SIWE 钱包认证 + 档位管理 + 订单流程**，完成了核心购买流程的所有必要组件。

**实施日期**: 2025-11-08  
**版本**: v1.0.0  
**状态**: ✅ 核心完成，待集成测试

---

## 🎯 实现功能

### 1. 核心6件（36小时）✅

#### 1.1 金额处理工具（2h）✅
**文件**: `backend/apps/core/utils/money.py`

**功能**:
- ✅ `quantize_money()` - 标准化金额精度（6位小数）
- ✅ `to_cents()` - 转换为Stripe金额（分）
- ✅ `from_cents()` - 从Stripe金额转回
- ✅ `validate_amount()` - 验证金额范围
- ✅ `format_money()` - 格式化显示

**关键代码**:
```python
def to_cents(amount: Decimal) -> int:
    """USD金额转Stripe分（100倍）"""
    return int(quantize_money(amount) * 100)

# 示例
to_cents(Decimal('100.50'))  # 10050
```

#### 1.2 Nonce服务（4h）✅
**文件**: `backend/apps/users/services/nonce.py`

**功能**:
- ✅ 生成密码学安全的nonce（`secrets.token_urlsafe(32)`）
- ✅ Redis存储（SET NX EX，5分钟TTL）
- ✅ 一次性消费（原子GETDEL）
- ✅ Key规范：`posx:{site}:{env}:nonce:{nonce}`

**安全特性**:
- 🔐 防止重放攻击
- 🔐 自动过期（TTL）
- 🔐 站点隔离
- 🔐 环境隔离

#### 1.3 SIWE验签服务（6h）✅
**文件**: `backend/apps/users/services/siwe.py`

**功能**:
- ✅ 验证SIWE消息（EIP-4361标准）
- ✅ 6项安全校验：
  1. domain 匹配
  2. chain_id 匹配
  3. uri 匹配
  4. nonce 一次性消费
  5. 未过期
  6. EIP-191 签名验证
- ✅ 暂不支持 EIP-1271（合约钱包留Phase D）

**配置**:
```bash
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=1
SIWE_URI=https://posx.io
```

#### 1.4 库存乐观锁服务（6h）✅
**文件**: `backend/apps/tiers/services/inventory.py`

**功能**:
- ✅ 乐观锁锁定库存（version字段）
- ✅ 检查affected_rows（兜底）
- ✅ 并发冲突返回 409
- ✅ 回补库存（取消/超时）

**关键SQL**:
```sql
UPDATE tiers 
SET available_units = available_units - ?, 
    version = version + 1,
    updated_at = NOW()
WHERE tier_id = ? 
  AND version = ?  -- ⭐ 乐观锁
  AND available_units >= ?;  -- ⭐ 双重检查

-- affected_rows == 0 → INVENTORY.CONFLICT
```

#### 1.5 订单服务（14h）✅
**文件**: `backend/apps/orders/services/order_service.py`

**功能**:
- ✅ 幂等性检查（`site_id` + `idempotency_key` 唯一）
- ✅ 数量校验（1 ≤ quantity ≤ MAX_QUANTITY_PER_ORDER）
- ✅ 锁定库存（乐观锁）
- ✅ 创建Order + OrderItem
- ✅ 创建OrderCommissionPolicySnapshot（Phase B模型）
- ✅ 创建Stripe PaymentIntent（或Mock）
- ✅ 事务一致性（失败全部回滚）

**幂等性设计**:
```python
# 数据库约束
UNIQUE(site_id, idempotency_key) WHERE idempotency_key IS NOT NULL

# Header传递
Idempotency-Key: order-abc123
```

**Mock Stripe模式**:
```python
# .env
MOCK_STRIPE=true  # 开发测试用

# 返回假client_secret
pi_mock_{order_id}_secret_{random}
```

#### 1.6 超时任务（4h）✅
**文件**: `backend/apps/orders/tasks.py`

**功能**:
- ✅ Celery定时任务（每5分钟）
- ✅ 查询 `pending` 且 `expires_at <= now` 的订单
- ✅ 分页处理（100/批，避免大事务）
- ✅ 状态改为 `cancelled`
- ✅ 回补库存

**Celery Beat配置**:
```python
# backend/config/celery.py
app.conf.beat_schedule = {
    'expire-pending-orders': {
        'task': 'apps.orders.tasks.expire_pending_orders',
        'schedule': crontab(minute='*/5'),  # 每5分钟
    },
}
```

---

### 2. 薄皮包装（16小时）✅

#### 2.1 认证API（4h）✅
**端点**:
- `POST /api/v1/auth/nonce` - 获取nonce（匿名）
- `POST /api/v1/auth/wallet` - 钱包认证/注册（匿名）
- `GET /api/v1/auth/me` - 用户信息（IsAuthenticated）
- `POST /api/v1/auth/wallet/bind` - 绑定额外钱包（IsAuthenticated）

#### 2.2 档位API（3h）✅
**端点**:
- `GET /api/v1/tiers/` - 列表（支持过滤）
- `GET /api/v1/tiers/{id}/` - 详情

**过滤参数**:
```bash
GET /api/v1/tiers/?is_active=true&available_only=true&price_min=100&price_max=1000&ordering=display_order
```

#### 2.3 订单API（5h）✅
**端点**:
- `POST /api/v1/orders/` - 创建订单（幂等）
- `GET /api/v1/orders/` - 列表（分页 + 过滤）
- `GET /api/v1/orders/{id}/` - 详情
- `POST /api/v1/orders/{id}/cancel/` - 取消订单

**过滤参数**:
```bash
GET /api/v1/orders/?status=pending&created_after=2025-11-01T00:00:00Z&page=1&size=20
```

#### 2.4 测试（4h）✅
**测试文件**:
- `apps/core/tests_money.py` - 金额工具测试
- `apps/users/tests_siwe.py` - SIWE认证测试
- `apps/tiers/tests_inventory.py` - 库存乐观锁测试
- `apps/orders/tests_e2e.py` - 端到端流程测试

---

## 📂 新增文件清单（45个文件）

### 核心服务层
```
backend/apps/
├── core/
│   ├── utils/
│   │   ├── __init__.py                    ✅
│   │   └── money.py                       ✅ 金额处理
│   ├── mixins.py                          ✅ 站点Mixin
│   └── tests_money.py                     ✅ 金额测试
├── users/
│   ├── services/
│   │   ├── __init__.py                    ✅
│   │   ├── nonce.py                       ✅ Nonce服务
│   │   └── siwe.py                        ✅ SIWE验签
│   ├── utils/
│   │   ├── __init__.py                    ✅
│   │   ├── wallet.py                      ✅ 钱包工具
│   │   └── referral.py                    ✅ 推荐码
│   ├── serializers_auth.py                ✅ 认证序列化器
│   ├── views_auth.py                      ✅ 认证API
│   ├── urls_auth.py                       ✅ 认证路由
│   └── tests_siwe.py                      ✅ SIWE测试
├── tiers/
│   ├── services/
│   │   ├── __init__.py                    ✅
│   │   └── inventory.py                   ✅ 库存乐观锁
│   ├── serializers.py                     ✅ 档位序列化器
│   ├── views.py                           ✅ 档位API
│   ├── urls.py                            ✅ 档位路由
│   └── tests_inventory.py                 ✅ 库存测试
└── orders/
    ├── services/
    │   ├── __init__.py                    ✅
    │   ├── stripe_service.py              ✅ Stripe集成
    │   └── order_service.py               ✅ 订单服务
    ├── serializers.py                     ✅ 订单序列化器
    ├── views.py                           ✅ 订单API
    ├── urls.py                            ✅ 订单路由
    ├── tasks.py                           ✅ 超时任务
    ├── tests_e2e.py                       ✅ 端到端测试
    └── migrations/
        ├── 0002_add_cancellation_fields.py     ✅ 取消字段
        └── 0003_add_idempotency_constraint.py  ✅ 幂等约束
```

### 配置和文档
```
backend/
├── config/
│   ├── settings/base.py                   ✅ 新增SIWE/订单配置
│   ├── celery.py                          ✅ Beat调度配置
│   └── urls.py                            ✅ 新增auth路由
├── requirements/
│   └── production.txt                     ✅ 新增siwe, eth-account
├── PHASE_C_PLAN.md                        ✅ Phase C计划
├── PHASE_C_IMPLEMENTATION.md              ✅ 本文档
└── PHASE_C_ACCEPTANCE.md                  ✅ 验收清单
```

**总计**: **45 个文件**（新增33个 + 修改12个）

---

## 🔧 关键技术决策

### 1. 幂等性设计

**问题**: 防止重复创建订单

**方案**:
```sql
-- 数据库唯一约束
ALTER TABLE orders ADD CONSTRAINT unique_site_idempotency_key 
UNIQUE (site_id, idempotency_key) 
WHERE idempotency_key IS NOT NULL;

-- Redis Key规范
posx:{site}:{env}:idempotency:{key}
```

**优点**:
- ✅ 多站点隔离
- ✅ 环境隔离
- ✅ 数据库层保障

---

### 2. 库存并发控制

**问题**: 防止超卖

**方案**:
```python
# 乐观锁 + affected_rows校验
affected = Tier.objects.filter(
    tier_id=tier_id,
    version=current_version,  # ⭐ 乐观锁
    available_units__gte=quantity  # ⭐ 双重检查
).update(
    available_units=F('available_units') - quantity,
    version=F('version') + 1
)

if affected == 0:
    return False, 'INVENTORY.CONFLICT'  # 409
```

**优点**:
- ✅ 无死锁
- ✅ 高并发性能
- ✅ 失败快速返回

---

### 3. SIWE最小安全集

**问题**: 钱包签名认证安全性

**方案**:
```python
必须校验:
✅ domain = settings.SIWE_DOMAIN
✅ chain_id = settings.SIWE_CHAIN_ID
✅ uri = settings.SIWE_URI
✅ nonce 一次性消费 + 5min TTL
✅ address EIP-55 + lower存储
✅ expiration_time 未过期

Phase D再做:
❌ EIP-1271 (合约钱包)
```

**优点**:
- ✅ 符合EIP-4361标准
- ✅ 防止重放攻击
- ✅ 域名绑定防钓鱼
- ✅ 80%用户场景覆盖

---

### 4. 订单快照集成

**问题**: 佣金规则变更影响历史订单

**方案**:
```python
# create_order() 事务内
with transaction.atomic():
    # 1. 锁库存
    # 2. 创建Order + OrderItem
    # 3. 创建OrderCommissionPolicySnapshot ⭐
    OrderSnapshotService.create_snapshot_for_order(
        order_id=order.order_id,
        site_id=site_id
    )
    # 4. 创建PaymentIntent
    # 失败全部回滚
```

**优点**:
- ✅ 规则不可变性
- ✅ 审计追踪
- ✅ 佣金计算准确

---

## 🔐 环境变量（新增）

### SIWE配置（必需）
```bash
# SIWE域名
SIWE_DOMAIN=posx.io

# 链ID（1=以太坊主网，11155111=Sepolia测试网）
SIWE_CHAIN_ID=1

# SIWE URI
SIWE_URI=https://posx.io
```

### 订单配置（可选，有默认值）
```bash
# Nonce TTL（秒）
NONCE_TTL_SECONDS=300  # 默认5分钟

# 订单过期时间（分钟）
ORDER_EXPIRE_MINUTES=15  # 默认15分钟

# 每单最大数量
MAX_QUANTITY_PER_ORDER=1000  # 默认1000

# 环境标识（用于Redis Key）
ENV=prod  # prod, dev, test

# Stripe Mock模式（开发测试）
MOCK_STRIPE=true  # 本地开发时启用
```

### Stripe配置（已有，确认）
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 🗄️ 数据库迁移

### 新增迁移

#### `orders/0002_add_cancellation_fields.py`
- ✅ 添加 `cancelled_reason` 字段
- ✅ 添加 `cancelled_at` 字段
- ✅ 添加索引 `(status, expires_at)`

#### `orders/0003_add_idempotency_constraint.py`
- ✅ 移除 `idempotency_key` 单列唯一约束
- ✅ 添加 `(site_id, idempotency_key)` 复合唯一约束
- ✅ 添加索引 `(site_id, idempotency_key)`

### 运行迁移

```bash
cd backend

# 运行新迁移
python manage.py migrate orders

# 验证约束
psql -U posx_app -d posx_local -c "
SELECT conname, contype FROM pg_constraint 
WHERE conrelid = 'orders'::regclass
AND conname LIKE '%idempotency%';
"

# 应该显示：unique_site_idempotency_key
```

---

## 🧪 测试覆盖

### 单元测试

| 测试文件                   | 测试场景                  | 用例数 |
| -------------------------- | ------------------------- | ------ |
| `core/tests_money.py`      | 金额工具、精度、边界值    | 8      |
| `users/tests_siwe.py`      | Nonce、SIWE、钱包、推荐码 | 10     |
| `tiers/tests_inventory.py` | 乐观锁、并发、回补        | 7      |
| `orders/tests_e2e.py`      | 端到端流程、快照          | 4      |

**总计**: **29个测试用例**

### 运行测试

```bash
cd backend

# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test apps.core.tests_money
python manage.py test apps.users.tests_siwe
python manage.py test apps.tiers.tests_inventory
python manage.py test apps.orders.tests_e2e

# 并发测试（重要！）
python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_concurrent_lock_inventory
```

---

## 📊 API端点总览

### 认证相关（Phase C新增）

| 方法 | 路径                       | 功能          | 权限            |
| ---- | -------------------------- | ------------- | --------------- |
| POST | `/api/v1/auth/nonce`       | 获取nonce     | AllowAny        |
| POST | `/api/v1/auth/wallet`      | 钱包认证/注册 | AllowAny        |
| GET  | `/api/v1/auth/me`          | 用户信息      | IsAuthenticated |
| POST | `/api/v1/auth/wallet/bind` | 绑定钱包      | IsAuthenticated |

### 档位相关

| 方法 | 路径                  | 功能     | 权限            |
| ---- | --------------------- | -------- | --------------- |
| GET  | `/api/v1/tiers/`      | 档位列表 | IsAuthenticated |
| GET  | `/api/v1/tiers/{id}/` | 档位详情 | IsAuthenticated |

### 订单相关

| 方法 | 路径                          | 功能     | 权限            |
| ---- | ----------------------------- | -------- | --------------- |
| POST | `/api/v1/orders/`             | 创建订单 | IsAuthenticated |
| GET  | `/api/v1/orders/`             | 订单列表 | IsAuthenticated |
| GET  | `/api/v1/orders/{id}/`        | 订单详情 | IsAuthenticated |
| POST | `/api/v1/orders/{id}/cancel/` | 取消订单 | IsAuthenticated |

---

## 🔬 端到端验证流程

### 完整购买流程

```bash
export SITE=NA
export BASE_URL=http://localhost:8000

# 步骤1: 获取nonce
NONCE_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/nonce \
  -H "X-Site-Code: $SITE")

NONCE=$(echo $NONCE_RESPONSE | jq -r '.nonce')
echo "Nonce: $NONCE"

# 步骤2: 生成SIWE消息并签名（前端操作）
# 使用 MetaMask 或 eth-account 库签名

# 步骤3: 钱包认证
AUTH_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/wallet \
  -H "X-Site-Code: $SITE" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"$SIWE_MESSAGE\",
    \"signature\": \"$SIGNATURE\",
    \"referral_code\": \"NA-ABC123\"
  }")

USER_ID=$(echo $AUTH_RESPONSE | jq -r '.user_id')
echo "User ID: $USER_ID"

# 步骤4: 查询可用档位
TIERS=$(curl -s "$BASE_URL/api/v1/tiers/?is_active=true&available_only=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE")

TIER_ID=$(echo $TIERS | jq -r '.results[0].tier_id')
echo "Tier ID: $TIER_ID"

# 步骤5: 创建订单（带幂等键）
ORDER_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Idempotency-Key: test-order-123" \
  -H "Content-Type: application/json" \
  -d "{
    \"tier_id\": \"$TIER_ID\",
    \"quantity\": 1,
    \"wallet_address\": \"0xabc...\"
  }")

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.order_id')
CLIENT_SECRET=$(echo $ORDER_RESPONSE | jq -r '.stripe.client_secret')
echo "Order ID: $ORDER_ID"
echo "Client Secret: $CLIENT_SECRET"

# 步骤6: 重复请求（验证幂等性）
ORDER_RESPONSE2=$(curl -s -X POST $BASE_URL/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Idempotency-Key: test-order-123" \
  -H "Content-Type: application/json" \
  -d "{
    \"tier_id\": \"$TIER_ID\",
    \"quantity\": 1,
    \"wallet_address\": \"0xabc...\"
  }")

ORDER_ID2=$(echo $ORDER_RESPONSE2 | jq -r '.order_id')

# 验证：应返回相同order_id
echo "Order ID (repeat): $ORDER_ID2"
# $ORDER_ID == $ORDER_ID2

# 步骤7: 取消订单
CANCEL_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/orders/$ORDER_ID/cancel/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -d '{"reason": "USER_CANCELLED"}')

echo "Cancel Response: $CANCEL_RESPONSE"
```

---

## 🔒 安全检查清单

### ✅ 已实施

- [x] **SIWE 6项校验**（domain/chain/uri/nonce/expiration/signature）
- [x] **Nonce 一次性消费**（防重放攻击）
- [x] **幂等性保证**（site_id + idempotency_key唯一）
- [x] **库存乐观锁**（version + affected_rows）
- [x] **订单快照**（佣金规则固化）
- [x] **金额精度**（Decimal(18,6) + to_cents()）
- [x] **站点隔离**（RLS + 显式过滤）
- [x] **输入验证**（DRF序列化器 + 自定义校验器）

### ⚠️ 已知限制

1. **EIP-1271（合约钱包）** - Phase D实现
2. **Stripe Webhook** - Phase D实现（当前仅创建PaymentIntent）
3. **退款流程** - Phase D实现
4. **代币分配** - Phase D实现（订单paid后）
5. **Email通知** - Phase D实现（可选）

---

## 📝 后续步骤（Phase D）

1. **Stripe Webhook集成**:
   - 监听 `payment_intent.succeeded`
   - 更新订单状态 `pending → paid`
   - 触发代币分配

2. **代币分配流程**:
   - 调用Fireblocks API
   - 创建Allocation记录
   - 触发佣金计算

3. **佣金计算引擎**:
   - 基于OrderCommissionPolicySnapshot
   - 基于AgentTree（Phase B）
   - 支持 `level` 和 `solar_diff` 模式

4. **合约钱包支持**:
   - EIP-1271验签
   - 链上查询 `isValidSignature()`

5. **监控与告警**:
   - Stripe Webhook失败告警
   - 库存异常告警
   - 订单超时告警

---

## ✅ 验收标准

### 必须通过

- [ ] **幂等性**: 相同Idempotency-Key重复请求返回相同order_id
- [ ] **库存并发**: 100并发购买10个名额，仅10个成功，其余409
- [ ] **SIWE安全**: Nonce重放返回401
- [ ] **订单快照**: 每个订单都有OrderCommissionPolicySnapshot
- [ ] **金额精度**: to_cents(Decimal('100.50')) == 10050
- [ ] **超时取消**: 15分钟后自动cancelled + 库存回补
- [ ] **站点隔离**: 跨站点访问返回404

### 推荐验证

- [ ] Nonce过期后无法使用
- [ ] 域名不匹配拒绝
- [ ] 数量超过MAX_QUANTITY_PER_ORDER拒绝
- [ ] 档位未激活拒绝
- [ ] client_secret格式正确

---

## 🐛 已知问题

### 1. Order模型字段不完整

**问题**: Order模型缺少以下字段：
- `cancelled_reason`
- `cancelled_at`

**状态**: ✅ 已通过迁移 `0002_add_cancellation_fields.py` 添加

### 2. idempotency_key约束调整

**问题**: 原约束为单列唯一，需要改为 `(site_id, idempotency_key)`

**状态**: ✅ 已通过迁移 `0003_add_idempotency_constraint.py` 修正

### 3. 幂等请求返回client_secret

**问题**: 幂等请求返回已有订单时，无法获取client_secret（模型未存储）

**临时方案**: 返回空字符串，前端可重新从Stripe获取

**长期方案**（Phase D）:
- 选项1: Order模型添加 `stripe_client_secret` 字段
- 选项2: 幂等请求时重新从Stripe API获取

---

## 📚 参考文档

- [EIP-4361: Sign-In with Ethereum](https://eips.ethereum.org/EIPS/eip-4361)
- [EIP-191: Signed Data Standard](https://eips.ethereum.org/EIPS/eip-191)
- [EIP-1271: Contract Signature Verification](https://eips.ethereum.org/EIPS/eip-1271)
- [Stripe PaymentIntents API](https://stripe.com/docs/api/payment_intents)
- [Celery Beat](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)

---

**实施完成日期**: 2025-11-08  
**实施人员**: AI Assistant  
**审核状态**: ✅ 核心完成，待集成测试


