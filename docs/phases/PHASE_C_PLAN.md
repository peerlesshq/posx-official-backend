# POSX Phase C 实施计划

## 📋 概述

Phase C 实施 **SIWE 钱包认证 + 档位管理 + 订单流程**，支持用户通过钱包签名登录并购买代币档位。

**实施日期**: 2025-11-08  
**版本**: v1.0.0  
**依赖**: Phase B（认证基础 + 站点上下文 + RLS）

---

## 🎯 核心6件（优先级 P0）

### 1. 金额处理工具（2h）✅
- 文件: `backend/apps/core/utils/money.py`
- 功能: to_cents(), from_cents(), quantize_money()
- 防止浮点误差

### 2. Nonce服务（4h）✅
- 文件: `backend/apps/users/services/nonce.py`
- 功能: 生成nonce（Redis SET NX EX）、一次性消费
- Key规范: `posx:{site}:{env}:nonce:{nonce}`

### 3. SIWE验签服务（6h）✅
- 文件: `backend/apps/users/services/siwe.py`
- 功能: 验证domain/chain_id/uri/nonce/签名
- 暂不支持EIP-1271（合约钱包）

### 4. 库存乐观锁服务（6h）✅
- 文件: `backend/apps/tiers/services/inventory.py`
- 功能: 乐观锁扣减/回补库存
- 返回409（INVENTORY.CONFLICT）

### 5. 订单服务（14h）✅
- 文件: `backend/apps/orders/services/order_service.py`
- 功能: 幂等创建订单 + 锁库存 + 快照 + Stripe
- 幂等键: `(site_id, idempotency_key)` 唯一

### 6. 超时任务（4h）✅
- 文件: `backend/apps/orders/tasks.py`
- 功能: 15分钟未支付自动取消 + 回补库存
- 分页处理避免大事务

---

## 🔧 关键技术决策

### 幂等性设计
```python
# 数据库唯一约束
UNIQUE(site_id, idempotency_key)

# Redis Key规范
posx:{site}:{env}:idempotency:{key}
posx:NA:prod:idempotency:abc123
```

### 库存乐观锁
```sql
UPDATE tiers 
SET available_units = available_units - ?, 
    version = version + 1
WHERE tier_id = ? 
  AND version = ? 
  AND available_units >= ?;

-- affected_rows == 0 → 409 INVENTORY.CONFLICT
```

### SIWE最小安全集
```python
必须校验:
✅ domain = settings.SIWE_DOMAIN
✅ chain_id = settings.SIWE_CHAIN_ID  
✅ uri = settings.SIWE_URI
✅ nonce 一次性消费 + 5min TTL
✅ address EIP-55 + lower存储

Phase D再做:
❌ EIP-1271 (合约钱包)
```

### 订单快照集成
```python
# create_order() 事务内
with transaction.atomic():
    # 1. 锁库存
    # 2. 创建Order + OrderItem
    # 3. 创建OrderCommissionPolicySnapshot
    # 4. 创建Stripe PaymentIntent
    # 失败全部回滚
```

---

## 📂 新增文件清单

### 核心服务（36h）
```
backend/apps/
├── core/
│   └── utils/
│       └── money.py                 ✅ 金额处理
├── users/
│   ├── services/
│   │   ├── nonce.py                 ✅ Nonce服务
│   │   └── siwe.py                  ✅ SIWE验签
│   └── utils/
│       ├── wallet.py                ✅ 钱包工具
│       └── referral.py              ✅ 推荐码
├── tiers/
│   └── services/
│       └── inventory.py             ✅ 库存乐观锁
└── orders/
    ├── services/
    │   ├── stripe_service.py        ✅ Stripe集成
    │   └── order_service.py         ✅ 订单服务
    └── tasks.py                     ✅ 超时任务
```

### API层（16h）
```
backend/apps/
├── users/
│   ├── serializers_auth.py          ✅ 认证序列化器
│   ├── views_auth.py                 ✅ 认证API
│   └── urls_auth.py                  ✅ 路由
├── tiers/
│   ├── serializers.py                ✅ 档位序列化器（增强）
│   └── views.py                      ✅ 档位API
└── orders/
    ├── serializers.py                ✅ 订单序列化器
    └── views.py                      ✅ 订单API
```

---

## 🔐 环境变量（新增）

```bash
# SIWE配置
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=1
SIWE_URI=https://posx.io

# 订单配置
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000

# Stripe配置（已有，确认）
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Stripe Mock模式（开发用）
MOCK_STRIPE=true  # 本地开发时启用
```

---

## 🧪 验收标准

### 幂等性测试
```bash
# 相同Idempotency-Key重复请求
curl -X POST $BASE_URL/api/v1/orders/ \
  -H "Idempotency-Key: test-key-123" \
  -d '{"tier_id":"...","quantity":1}'

# 第二次请求应返回相同order_id
```

### 库存并发测试
```python
# 100并发购买最后10个名额
# 应该只有10个成功，其余返回409
```

### SIWE安全测试
```bash
# Nonce重放攻击 → 401
# 签名不匹配 → 401
# 域名不匹配 → 401
# Nonce过期 → 401
```

### 订单超时测试
```bash
# 创建订单后等待16分钟
# 应自动变为cancelled + 库存回补
```

---

## 📊 实施进度

| 任务 | 状态 | 工时 | 完成时间 |
|------|------|------|---------|
| 1. 金额工具 | ✅ | 2h | - |
| 2. Nonce服务 | ✅ | 4h | - |
| 3. SIWE验签 | ✅ | 6h | - |
| 4. 库存乐观锁 | ✅ | 6h | - |
| 5. 订单服务 | ✅ | 14h | - |
| 6. 超时任务 | ✅ | 4h | - |
| 7. 序列化器 | 🔄 | 4h | - |
| 8. API端点 | 🔄 | 6h | - |
| 9. 测试 | 🔄 | 6h | - |

**总计**: 52小时（约1.5周）

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install siwe eth-account
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 添加 SIWE_* 配置
```

### 3. 运行迁移
```bash
python manage.py migrate
```

### 4. 启动Celery（超时任务）
```bash
celery -A config worker -l info
celery -A config beat -l info
```

### 5. 测试端到端流程
```bash
python manage.py test apps.orders.tests_e2e
```

---

**实施状态**: 🔄 进行中  
**下一步**: 实施核心6件


