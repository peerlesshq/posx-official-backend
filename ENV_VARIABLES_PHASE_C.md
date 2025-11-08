# Phase C 环境变量配置文档

## 📋 概述

Phase C 新增了 **SIWE 钱包认证** 和 **订单管理** 相关的环境变量。

---

## 🔐 SIWE配置（必需）

### SIWE_DOMAIN
**说明**: Sign-In with Ethereum 的域名（不含协议）

**示例**:
```bash
# 生产环境
SIWE_DOMAIN=posx.io

# 开发环境
SIWE_DOMAIN=localhost
```

**注意**:
- ⚠️ 必须与前端域名完全匹配
- ⚠️ 防止钓鱼攻击
- ⚠️ SIWE消息会包含此域名

---

### SIWE_CHAIN_ID
**说明**: 区块链网络ID

**常用值**:
| 网络 | Chain ID | 说明 |
|------|----------|------|
| Ethereum Mainnet | 1 | 主网 |
| Sepolia Testnet | 11155111 | 测试网 |
| Polygon Mainnet | 137 | Polygon主网 |
| BSC Mainnet | 56 | 币安智能链 |

**示例**:
```bash
# 以太坊主网
SIWE_CHAIN_ID=1

# Sepolia测试网（开发用）
SIWE_CHAIN_ID=11155111
```

---

### SIWE_URI
**说明**: 应用完整URI（含协议）

**示例**:
```bash
# 生产环境
SIWE_URI=https://posx.io

# 开发环境
SIWE_URI=http://localhost:3000
```

**注意**:
- ⚠️ 必须包含协议（https:// 或 http://）
- ⚠️ 必须与前端访问地址一致

---

## 📦 订单配置（可选，有默认值）

### NONCE_TTL_SECONDS
**说明**: Nonce过期时间（秒）

**默认值**: 300（5分钟）

**示例**:
```bash
NONCE_TTL_SECONDS=300
```

**建议**:
- 生产环境：300-600秒
- 开发环境：可以更长（1800秒）

---

### ORDER_EXPIRE_MINUTES
**说明**: 订单过期时间（分钟）

**默认值**: 15（15分钟）

**示例**:
```bash
ORDER_EXPIRE_MINUTES=15
```

**建议**:
- Stripe推荐：15-30分钟
- 太短：用户体验差
- 太长：库存锁定时间长

---

### MAX_QUANTITY_PER_ORDER
**说明**: 每单最大购买数量

**默认值**: 1000

**示例**:
```bash
MAX_QUANTITY_PER_ORDER=1000
```

**用途**:
- 防止恶意大单
- 限制单笔交易风险
- 根据业务需求调整

---

### ENV
**说明**: 环境标识（用于Redis Key前缀）

**默认值**: dev

**示例**:
```bash
# 生产环境
ENV=prod

# 开发环境
ENV=dev

# 测试环境
ENV=test
```

**Redis Key示例**:
```
posx:NA:prod:nonce:abc123...
posx:NA:dev:nonce:xyz789...
```

---

### MOCK_STRIPE
**说明**: Stripe Mock模式（开发测试用）

**默认值**: false

**示例**:
```bash
# 开发环境（不依赖Stripe）
MOCK_STRIPE=true

# 生产环境（使用真实Stripe）
MOCK_STRIPE=false
```

**Mock模式行为**:
- ✅ 不调用Stripe API
- ✅ 返回假client_secret
- ✅ CI/CD友好
- ⚠️ 生产环境必须关闭

---

## 🔧 完整配置示例

### 开发环境 (.env.local)
```bash
# ============================================
# Django
# ============================================
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# ============================================
# Database
# ============================================
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# ============================================
# Redis
# ============================================
REDIS_URL=redis://localhost:6379/0

# ============================================
# Auth0 (Phase B)
# ============================================
AUTH0_DOMAIN=posx-dev.us.auth0.com
AUTH0_AUDIENCE=https://api.posx.dev
AUTH0_ISSUER=https://posx-dev.us.auth0.com/

# ============================================
# SIWE (Phase C)
# ============================================
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111  # Sepolia测试网
SIWE_URI=http://localhost:3000

# ============================================
# 订单配置 (Phase C)
# ============================================
NONCE_TTL_SECONDS=600  # 10分钟（开发用）
ORDER_EXPIRE_MINUTES=30  # 30分钟（开发用）
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# ============================================
# Stripe (Phase C)
# ============================================
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
MOCK_STRIPE=true  # 开发时启用Mock

# ============================================
# Celery
# ============================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 生产环境 (.env.prod)
```bash
# ============================================
# Django
# ============================================
SECRET_KEY=<生成的安全密钥>
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.production

# ============================================
# Database
# ============================================
DB_NAME=posx_prod
DB_USER=posx_app
DB_PASSWORD=<安全密码>
DB_HOST=postgres.internal
DB_PORT=5432

# ============================================
# Redis
# ============================================
REDIS_URL=redis://redis.internal:6379/0

# ============================================
# Auth0 (Phase B)
# ============================================
AUTH0_DOMAIN=posx.auth0.com
AUTH0_AUDIENCE=https://api.posx.io
AUTH0_ISSUER=https://posx.auth0.com/

# ============================================
# SIWE (Phase C)
# ============================================
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=1  # 以太坊主网
SIWE_URI=https://posx.io

# ============================================
# 订单配置 (Phase C)
# ============================================
NONCE_TTL_SECONDS=300  # 5分钟
ORDER_EXPIRE_MINUTES=15  # 15分钟
MAX_QUANTITY_PER_ORDER=100  # 生产环境可能更严格
ENV=prod

# ============================================
# Stripe (Phase C)
# ============================================
STRIPE_SECRET_KEY=sk_live_...  # 生产密钥
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
MOCK_STRIPE=false  # 生产环境必须关闭

# ============================================
# Celery
# ============================================
CELERY_BROKER_URL=redis://redis.internal:6379/0
CELERY_RESULT_BACKEND=redis://redis.internal:6379/0
```

---

## ⚙️ 配置验证

### 启动时自动检查

Django启动时会自动检查关键配置：

```
✅ Auth0 配置已加载: Domain=posx-dev.***, Audience=https://api...., JWKS_TTL=3600s
✅ SIWE 配置已加载: Domain=posx.io, ChainID=1, URI=https://posx.io
⚠️ MOCK_STRIPE=true, Stripe集成将使用Mock模式
```

### 手动验证

```bash
python manage.py shell

from django.conf import settings

# 检查SIWE配置
print(f"SIWE Domain: {settings.SIWE_DOMAIN}")
print(f"SIWE Chain ID: {settings.SIWE_CHAIN_ID}")
print(f"SIWE URI: {settings.SIWE_URI}")

# 检查订单配置
print(f"Order Expire Minutes: {settings.ORDER_EXPIRE_MINUTES}")
print(f"Max Quantity: {settings.MAX_QUANTITY_PER_ORDER}")

# 检查Stripe模式
print(f"Mock Stripe: {settings.MOCK_STRIPE}")
```

---

## 🐛 常见配置问题

### 问题1: SIWE验证失败

**错误**: `SIWE.DOMAIN_MISMATCH`

**原因**: 前端和后端域名不一致

**解决**:
```bash
# 检查配置
echo $SIWE_DOMAIN

# 前端SIWE消息应使用相同域名
const siweMessage = new SiweMessage({
  domain: 'posx.io',  # 必须匹配后端
  // ...
});
```

---

### 问题2: Nonce过期太快

**错误**: `AUTH.NONCE_INVALID`

**原因**: 用户签名速度慢，nonce已过期

**解决**:
```bash
# 增加TTL
NONCE_TTL_SECONDS=600  # 10分钟
```

---

### 问题3: Stripe Mock未生效

**错误**: Stripe API调用失败

**原因**: `MOCK_STRIPE`未设置为true

**解决**:
```bash
# .env
MOCK_STRIPE=true

# 重启服务
python manage.py runserver
```

---

## 📚 相关文档

- **Phase B**: `ENV_VARIABLES.md` - Auth0配置
- **Phase C**: `ENV_VARIABLES_PHASE_C.md` - 本文档
- **完整配置**: `.env.example` - 所有环境变量

---

**更新日期**: 2025-11-08  
**适用版本**: Phase C v1.0.0


