# 🧙 POSX 环境配置向导

## 开始配置！

我会一步步引导您完成配置。每个配置项我都会说明：
- **是什么**
- **怎么填**
- **推荐值**

---

## 第1步：创建.env文件

### 操作：

```bash
# 在项目根目录创建.env文件
cd E:\300_Code\314_POSX_Official_Sale_App
notepad .env
```

然后复制粘贴下面的模板：

```bash
# POSX 环境变量配置
# 请根据下面的说明填写每一项

# Django核心
SECRET_KEY=
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# 数据库
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth0（可选）
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_ISSUER=

# SIWE
SIWE_DOMAIN=
SIWE_CHAIN_ID=
SIWE_URI=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
MOCK_STRIPE=true

# 订单配置
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 前端
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA

# Fireblocks（Phase D使用，暂时留空）
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
```

**保存文件（Ctrl+S）**

---

## 第2步：填写必需配置（P0）

### 🔑 SECRET_KEY

**是什么**: Django的加密密钥

**怎么填**: 生成一个随机字符串

**操作**:
```bash
# 运行这个命令生成密钥
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 复制输出结果，粘贴到.env的SECRET_KEY=后面
```

**示例**:
```bash
SECRET_KEY=django-insecure-k8@#mf2!x7n9$p4q&w5e6r7t8y9u0i1o2p3a4s5d6f
```

---

### 🗄️ DB_PASSWORD

**是什么**: PostgreSQL数据库密码

**怎么填**: 您的PostgreSQL密码

**操作**:
```bash
# 如果您使用默认设置（开发环境），可以填：
DB_PASSWORD=posx

# 生产环境应使用强密码
```

**示例**:
```bash
DB_PASSWORD=posx
```

---

### 🌐 SIWE_DOMAIN

**是什么**: Sign-In with Ethereum 的域名

**怎么填**: 本地开发填 `localhost`，生产环境填实际域名

**操作**:
```bash
# 本地开发
SIWE_DOMAIN=localhost

# 生产环境
SIWE_DOMAIN=posx.io
```

**示例**:
```bash
SIWE_DOMAIN=localhost
```

---

### ⛓️ SIWE_CHAIN_ID

**是什么**: 区块链网络ID

**怎么填**: 
- 本地开发：`11155111`（Sepolia测试网）
- 生产环境：`1`（以太坊主网）

**操作**:
```bash
# 本地开发（推荐）
SIWE_CHAIN_ID=11155111
```

**示例**:
```bash
SIWE_CHAIN_ID=11155111
```

---

### 🔗 SIWE_URI

**是什么**: 前端完整访问地址

**怎么填**: 前端URL（含协议）

**操作**:
```bash
# 本地开发（Next.js默认端口）
SIWE_URI=http://localhost:3000

# 生产环境
SIWE_URI=https://posx.io
```

**示例**:
```bash
SIWE_URI=http://localhost:3000
```

---

## 第3步：保存并验证

### 保存.env文件

确保所有必需配置已填写，示例：

```bash
SECRET_KEY=django-insecure-k8@#mf2!x7n9$p4q&w5e6r7t8y9u0i1o2p3a4s5d6f
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

# Auth0留空（如不使用）
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_ISSUER=

SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# Stripe留空（使用Mock）
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
MOCK_STRIPE=true

NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA

FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
```

### 运行配置检查脚本

```bash
cd backend
python check_env.py
```

**预期输出**:

```
============================================================
POSX 环境变量配置检查工具
============================================================

============================================================
1. 检查 .env 文件
============================================================

✅ .env 文件存在: E:\300_Code\314_POSX_Official_Sale_App\.env

============================================================
2. 检查 P0 配置（必须）
============================================================

✅ SECRET_KEY = django-ins...
✅ DEBUG = true
✅ DB_NAME = posx_local
✅ DB_USER = posx_app
✅ DB_PASSWORD = posx...
✅ DB_HOST = localhost
✅ REDIS_URL = redis://localhost:6379/0
✅ SIWE_DOMAIN = localhost
✅ SIWE_CHAIN_ID = 11155111
✅ SIWE_URI = http://localhost:3000

============================================================
3. 检查 P1 配置（重要）
============================================================

⚠️  Auth0 未配置（如不使用Auth0 JWT认证，可忽略）
⚠️  MOCK_STRIPE=true，Stripe将使用Mock模式
✅ 环境标识: dev

============================================================
4. 检查数据库连接
============================================================

✅ 数据库连接成功

============================================================
5. 检查 Redis 连接
============================================================

✅ Redis 连接成功

============================================================
6. 检查 Python 依赖
============================================================

✅ Django 已安装
✅ djangorestframework 已安装
✅ siwe 已安装
✅ eth-account 已安装
✅ stripe 已安装

============================================================
配置检查总结
============================================================

✅ P0配置完整
✅ Python依赖安装
✅ 数据库连接
✅ Redis连接

============================================================
🎉 所有检查通过！您可以开始使用POSX了。

下一步：
  1. python manage.py migrate
  2. python manage.py loaddata fixtures/seed_sites.json
  3. python manage.py runserver
============================================================
```

---

## ❓ 我当前应该怎么做？

请告诉我：

1. **您的数据库密码是什么？**
   - 如果不知道，默认可以用：`posx`
   
2. **您是否需要使用Auth0？**
   - 如果不需要，可以留空
   - 如果需要，我会引导您获取Auth0配置

3. **您是否需要测试真实Stripe支付？**
   - 如果不需要，使用 `MOCK_STRIPE=true`（推荐）
   - 如果需要，我会引导您获取Stripe测试密钥

**现在请回答这3个问题，我会根据您的回答提供精准的配置建议！** 🎯


