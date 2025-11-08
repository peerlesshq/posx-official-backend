# Phase C 快速开始（5分钟）

## 🚀 3步启动

### 步骤1: 安装依赖（1分钟）

```bash
cd backend

# 安装依赖
pip install -r requirements/production.txt

# 或者开发环境
pip install -r requirements/local.txt
```

**关键依赖**:
- `siwe==2.1.1` - SIWE验证
- `eth-account==0.10.0` - 以太坊签名
- `stripe==7.8.0` - 支付集成

---

### 步骤2: 配置环境（2分钟）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，添加以下配置
```

**必需配置**:
```bash
# SIWE
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111  # Sepolia测试网
SIWE_URI=http://localhost:3000

# Stripe Mock（开发用）
MOCK_STRIPE=true

# 环境
ENV=dev
```

**可选配置**（使用默认值）:
```bash
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
```

---

### 步骤3: 运行迁移和启动（2分钟）

```bash
# 运行迁移
python manage.py migrate

# 加载种子数据
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json

# 启动Django
python manage.py runserver

# 另一个终端：启动Celery
celery -A config worker -l info

# 另一个终端：启动Beat
celery -A config beat -l info
```

---

## ✅ 验证启动成功

### 检查日志

```
✅ Auth0 配置已加载: Domain=posx-dev.***, Audience=https://api...
✅ SIWE 配置已加载: Domain=localhost, ChainID=11155111, URI=http://localhost:3000
⚠️ MOCK_STRIPE=true, Stripe集成将使用Mock模式
```

### 测试端点

```bash
# 健康检查
curl http://localhost:8000/health/
# {"status":"healthy"}

# 获取nonce（测试SIWE）
curl -X POST http://localhost:8000/api/v1/auth/nonce \
  -H "X-Site-Code: NA"
# {"nonce":"...","expires_in":300,"issued_at":"..."}

# 查询档位（需要认证）
curl http://localhost:8000/api/v1/tiers/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Site-Code: NA"
```

---

## 🧪 快速测试

### 运行单元测试

```bash
# 所有测试
python manage.py test

# 特定模块
python manage.py test apps.core.tests_money
python manage.py test apps.tiers.tests_inventory
python manage.py test apps.orders.tests_e2e
```

**预期结果**:
```
Ran 29 tests in 2.7s

OK
```

---

## 🎯 核心功能演示

### 1. 获取Nonce

```bash
curl -X POST http://localhost:8000/api/v1/auth/nonce \
  -H "X-Site-Code: NA" | jq '.'
```

### 2. 查询可用档位

```bash
curl "http://localhost:8000/api/v1/tiers/?is_active=true&available_only=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" | jq '.results[0]'
```

### 3. 创建订单（Mock模式）

```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -H "Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d '{
    "tier_id": "<tier_id>",
    "quantity": 1,
    "wallet_address": "0xab5801a7d398351b8be11c439e05c5b3259aec9b"
  }' | jq '.'
```

**预期响应**:
```json
{
  "order_id": "uuid",
  "status": "pending",
  "final_price_usd": "100.00",
  "expires_at": "2025-11-08T12:15:00Z",
  "stripe": {
    "payment_intent_id": "pi_mock_...",
    "client_secret": "pi_mock_..._secret_..."
  }
}
```

---

## 📚 下一步

- **完整验收**: 参考 `PHASE_C_ACCEPTANCE.md`
- **API文档**: 参考 `PHASE_C_IMPLEMENTATION.md`
- **问题排查**: 参考 `ENV_VARIABLES_PHASE_C.md`

---

**快速开始版本**: v1.0  
**更新日期**: 2025-11-08  
**预计时间**: 5分钟


