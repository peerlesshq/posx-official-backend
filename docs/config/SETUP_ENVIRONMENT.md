# 🔧 POSX 环境配置引导手册

## 📋 配置概览

本手册将引导您完成**开发环境**的所有环境变量配置。我会按优先级分为：
- **P0（必须）** - 不配置无法启动
- **P1（重要）** - 影响核心功能
- **P2（可选）** - 高级功能或Phase D

---

## 🚀 快速开始（最小配置 - 5分钟）

### 步骤1: 创建.env文件

```bash
# 进入项目根目录
cd E:\300_Code\314_POSX_Official_Sale_App

# 复制模板
cp .env.template .env

# 或者从头创建
touch .env
```

### 步骤2: 配置P0变量（必须）

在`.env`文件中添加以下内容：

```bash
# ============================================
# P0 必须配置（不配置无法启动）
# ============================================

# 1. Django Secret Key
SECRET_KEY=dev-secret-key-for-local-testing-change-in-production

# 2. Debug模式
DEBUG=true

# 3. 数据库配置
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# 4. Redis配置
REDIS_URL=redis://localhost:6379/0

# 5. SIWE配置（Phase C核心）
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# 6. Stripe Mock模式
MOCK_STRIPE=true

# 7. 环境标识
ENV=dev
```

### 步骤3: 验证配置

```bash
# 进入backend目录
cd backend

# 检查配置是否正确
python manage.py shell

# 在shell中执行
>>> from django.conf import settings
>>> print(f"SECRET_KEY: {settings.SECRET_KEY[:10]}...")
>>> print(f"DEBUG: {settings.DEBUG}")
>>> print(f"SIWE_DOMAIN: {settings.SIWE_DOMAIN}")
>>> print(f"MOCK_STRIPE: {settings.MOCK_STRIPE}")
>>> 
>>> # 应该看到配置值
>>> exit()
```

**✅ 如果没有报错，P0配置完成！**

---

## 📱 Phase B 配置（Auth0 JWT认证 - 可选）

### 是否需要配置？

**回答以下问题**：
- ❓ 您是否需要使用Auth0作为额外的认证方式（除了SIWE钱包认证之外）？
- ❓ 您是否已有Auth0账号？

**如果回答"是"，继续配置；如果回答"否"，跳过此部分**

---

### 如何获取Auth0配置

#### 步骤1: 登录Auth0

访问：https://manage.auth0.com/

#### 步骤2: 获取Domain

1. 左侧菜单 → **Settings**
2. 复制 **Domain** 字段
3. 示例：`your-tenant.us.auth0.com`

#### 步骤3: 创建/选择API

1. 左侧菜单 → **Applications** → **APIs**
2. 如果没有API，点击 **Create API**：
   - Name: `POSX API`
   - Identifier: `https://api.posx.io`（这就是Audience）
3. 复制 **Identifier**

#### 步骤4: 配置Issuer

格式：`https://{您的Domain}/`

示例：`https://your-tenant.us.auth0.com/`

#### 步骤5: 添加到.env

```bash
# ============================================
# P1 Auth0配置（可选 - 如果使用Auth0 JWT）
# ============================================

AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.posx.io
AUTH0_ISSUER=https://your-tenant.us.auth0.com/
```

**💡 提示**: 如果您不使用Auth0，可以留空或注释掉这些配置。SIWE钱包认证可以独立工作。

---

## 💳 Stripe 配置（支付集成）

### 是否需要配置真实Stripe？

**开发环境建议**: 使用Mock模式（已配置 `MOCK_STRIPE=true`），无需真实Stripe账号

**如果需要测试真实支付流程，继续配置**

---

### 如何获取Stripe密钥

#### 步骤1: 登录Stripe

访问：https://dashboard.stripe.com/

#### 步骤2: 获取测试密钥

1. 左侧菜单 → **Developers** → **API keys**
2. 确保切换到 **Test mode**（右上角开关）
3. 复制以下密钥：
   - **Secret key**（sk_test_...）
   - **Publishable key**（pk_test_...）

#### 步骤3: 添加到.env

```bash
# ============================================
# P1 Stripe配置
# ============================================

# 开发环境：使用测试密钥
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...

# Webhook Secret（Phase D使用，暂时留空）
STRIPE_WEBHOOK_SECRET=

# Mock模式（开发时可以先用Mock）
MOCK_STRIPE=true  # 改为false使用真实Stripe
```

**💡 提示**: 建议先使用 `MOCK_STRIPE=true` 开发，后续再切换到真实Stripe测试支付流程。

---

## 🎯 完整.env文件（开发环境推荐配置）

### 立即可用的配置

将以下内容复制到`.env`文件：

```bash
# ============================================
# POSX 开发环境配置
# ============================================

# ============================================
# Django 核心
# ============================================
SECRET_KEY=dev-insecure-secret-key-for-local-testing-only
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# ============================================
# 数据库
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
# Auth0（可选 - 如不使用可留空）
# ============================================
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_ISSUER=

# ============================================
# SIWE 钱包认证（Phase C）
# ============================================
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# ============================================
# Stripe 支付
# ============================================
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
MOCK_STRIPE=true

# ============================================
# 订单配置
# ============================================
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# ============================================
# Celery
# ============================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false

# ============================================
# 前端配置
# ============================================
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA

# ============================================
# Fireblocks（Phase D使用，暂时留空）
# ============================================
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=ETH_TEST
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=

# ============================================
# 其他配置
# ============================================
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7
```

---

## ✅ 配置验证步骤

### 步骤1: 保存.env文件

```bash
# 确认文件位置
ls -la .env

# 应该在项目根目录下
# E:\300_Code\314_POSX_Official_Sale_App\.env
```

### 步骤2: 启动Django检查

```bash
cd backend

# 启动服务
python manage.py runserver
```

**查看启动日志**，应该看到：

```
✅ Auth0 配置缺失: AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_ISSUER. JWT 认证将失败，请检查环境变量。
✅ SIWE 配置已加载: Domain=localhost, ChainID=11155111, URI=http://localhost:3000
⚠️ MOCK_STRIPE=true, Stripe集成将使用Mock模式

System check identified no issues (0 silenced).
Starting development server at http://127.0.0.1:8000/
```

**解释**:
- ⚠️ Auth0警告 - 正常（如果不使用Auth0）
- ✅ SIWE配置成功 - 好！
- ⚠️ Mock Stripe - 正常（开发模式）

### 步骤3: 测试健康检查

```bash
# 另一个终端
curl http://localhost:8000/health/

# 应该返回
{"status":"healthy"}
```

### 步骤4: 测试SIWE Nonce

```bash
curl -X POST http://localhost:8000/api/v1/auth/nonce \
  -H "X-Site-Code: NA" | jq '.'

# 应该返回
{
  "nonce": "xxxx...",
  "expires_in": 300,
  "issued_at": "2025-11-08T..."
}
```

**✅ 如果得到nonce，配置成功！**

---

## 🎯 配置决策树

### 我需要配置哪些？

```
开始
  ↓
是否本地开发？
  ├─ 是 → 使用上面的"开发环境推荐配置"
  │         ↓
  │       是否需要Auth0？
  │         ├─ 是 → 配置AUTH0_*
  │         └─ 否 → 留空（使用SIWE即可）
  │         ↓
  │       是否需要真实支付测试？
  │         ├─ 是 → 配置STRIPE_*，设置MOCK_STRIPE=false
  │         └─ 否 → 保持MOCK_STRIPE=true
  │         ↓
  │       完成！启动服务
  │
  └─ 否（生产环境）→ 继续阅读"生产环境配置"
```

---

## 🏭 生产环境配置（仅供参考）

```bash
# ============================================
# POSX 生产环境配置
# ============================================

SECRET_KEY=<使用命令生成>
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.production

DB_NAME=posx_prod
DB_USER=posx_app
DB_PASSWORD=<强密码>
DB_HOST=<RDS地址>
DB_PORT=5432

REDIS_URL=redis://<ElastiCache地址>:6379/0

# Auth0（如果使用）
AUTH0_DOMAIN=posx.auth0.com
AUTH0_AUDIENCE=https://api.posx.io
AUTH0_ISSUER=https://posx.auth0.com/

# SIWE（生产域名）
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=1  # 主网
SIWE_URI=https://posx.io

# Stripe（生产密钥）
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
MOCK_STRIPE=false  # 必须关闭

# 订单配置
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=100  # 可能更严格
ENV=prod

FRONTEND_URL=https://posx.io
CORS_ALLOWED_ORIGINS=https://posx.io,https://www.posx.io
```

---

## ❓ 常见问题

### Q1: 我没有Auth0账号怎么办？

**答**: 不影响！Phase C的SIWE钱包认证可以独立工作。Auth0是可选的额外认证方式。

**操作**: 将AUTH0_*留空即可

---

### Q2: 我没有Stripe账号怎么办？

**答**: 开发阶段使用Mock模式！

**操作**:
```bash
MOCK_STRIPE=true
STRIPE_SECRET_KEY=  # 留空
```

这样可以正常测试订单创建流程，只是支付是模拟的。

---

### Q3: SIWE_DOMAIN应该填什么？

**答**: 
- 本地开发：`localhost`
- 生产环境：`posx.io`（您的实际域名）

**重要**: 必须与前端访问域名一致！

---

### Q4: SIWE_CHAIN_ID应该选哪个？

**答**:
| 环境 | Chain ID | 网络 |
|------|----------|------|
| 本地开发 | 11155111 | Sepolia测试网 |
| 生产环境 | 1 | 以太坊主网 |
| Polygon | 137 | Polygon主网 |

**推荐**: 本地开发用Sepolia（测试网），生产环境用主网

---

### Q5: 如何生成安全的SECRET_KEY？

**答**:
```bash
# 方法1: Django命令
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 方法2: OpenSSL
openssl rand -base64 50

# 复制输出结果到.env的SECRET_KEY
```

---

## 🧪 配置测试清单

### 测试1: Django启动

```bash
cd backend
python manage.py runserver
```

**检查日志**:
- ✅ 无ModuleNotFoundError
- ✅ 能看到启动地址：`http://127.0.0.1:8000/`
- ✅ SIWE配置加载成功

---

### 测试2: 数据库连接

```bash
python manage.py check --database default
```

**预期输出**:
```
System check identified no issues (0 silenced).
```

---

### 测试3: Redis连接

```bash
python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
'value'
>>> exit()
```

---

### 测试4: SIWE Nonce

```bash
curl -X POST http://localhost:8000/api/v1/auth/nonce \
  -H "X-Site-Code: NA"
```

**预期响应**:
```json
{
  "nonce": "长随机字符串",
  "expires_in": 300,
  "issued_at": "2025-11-08T..."
}
```

---

## 📋 配置检查清单

### P0 必须配置

- [ ] SECRET_KEY 已设置（不是默认值）
- [ ] DB_* 配置正确（能连接数据库）
- [ ] REDIS_URL 配置正确（能连接Redis）
- [ ] SIWE_DOMAIN 已设置
- [ ] SIWE_CHAIN_ID 已设置
- [ ] SIWE_URI 已设置
- [ ] ENV 已设置（dev/test/prod）

### P1 重要配置

- [ ] MOCK_STRIPE=true（开发）或配置真实Stripe
- [ ] AUTH0_* 配置（如使用Auth0）
- [ ] FRONTEND_URL 配置正确
- [ ] CORS_ALLOWED_ORIGINS 包含前端地址

### P2 可选配置

- [ ] ORDER_EXPIRE_MINUTES 调整
- [ ] MAX_QUANTITY_PER_ORDER 调整
- [ ] NONCE_TTL_SECONDS 调整

---

## 🆘 遇到问题？

### 启动失败

```bash
# 检查配置文件位置
ls -la .env

# 检查配置是否被正确读取
python manage.py shell
>>> import os
>>> print(os.environ.get('SIWE_DOMAIN'))
```

### 数据库连接失败

```bash
# 检查PostgreSQL是否运行
psql -U posx_app -d posx_local -h localhost

# 如果失败，检查：
# 1. PostgreSQL服务是否启动
# 2. 用户名/密码是否正确
# 3. 数据库是否已创建
```

### Redis连接失败

```bash
# 检查Redis是否运行
redis-cli ping

# 应该返回：PONG
```

---

## ✅ 配置完成！

完成上述配置后，您应该能够：

1. ✅ 启动Django服务
2. ✅ 连接数据库
3. ✅ 连接Redis
4. ✅ 获取SIWE Nonce
5. ✅ 运行测试

**下一步**: 运行数据库迁移和加载种子数据

```bash
# 运行迁移
python manage.py migrate

# 加载站点数据
python manage.py loaddata fixtures/seed_sites.json

# 加载佣金计划
python manage.py loaddata fixtures/seed_commission_plans.json

# 创建测试档位（可选）
python manage.py shell
>>> from apps.sites.models import Site
>>> from apps.tiers.models import Tier
>>> from decimal import Decimal
>>> site = Site.objects.get(code='NA')
>>> Tier.objects.create(
...     site=site,
...     name='Early Bird',
...     description='Early bird special',
...     list_price_usd=Decimal('100.00'),
...     tokens_per_unit=Decimal('1000.00'),
...     total_units=100,
...     sold_units=0,
...     available_units=100,
...     display_order=1,
...     version=0,
...     is_active=True
... )
```

---

**需要帮助？** 告诉我您卡在哪一步，我会提供详细指导！

