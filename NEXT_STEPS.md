# 🎯 Stripe Webhook 配置说明

## ✅ 已完成

1. ✅ Stripe CLI 已登录
2. ✅ Webhook 监听已启动（后台运行）

---

## 📋 下一步操作

### 步骤1：获取 Webhook Secret

Webhook监听已在后台启动。请查看终端输出，找到类似这样的行：

```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxx
```

**🔑 请复制这个 `whsec_***` 密钥！**

---

### 步骤2：创建 .env 文件

**在项目根目录创建 `.env` 文件：**

```powershell
# 方法1：使用模板（如果存在）
Copy-Item .env.template .env

# 方法2：手动创建
notepad .env
```

**复制以下内容到 `.env` 文件（记得替换SECRET_KEY和STRIPE_WEBHOOK_SECRET）：**

```bash
# ============================================
# Django 核心配置
# ============================================
SECRET_KEY=django-insecure-dev-key-7x9k2m5n8p1q4r6t9w2y5u8i0o3a6s9d2f5g8h1j4k7m0
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# ============================================
# 数据库配置
# ============================================
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# ============================================
# Redis 配置（Docker）
# ============================================
REDIS_URL=redis://localhost:6379/0

# ============================================
# Auth0 配置
# ============================================
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/

# ============================================
# SIWE 配置（钱包认证）
# ============================================
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# ============================================
# Stripe 配置
# ============================================
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
MOCK_STRIPE=false

# ============================================
# 订单配置
# ============================================
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# ============================================
# Celery 配置
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
WALLETCONNECT_PROJECT_ID=cbc675a7819dd3d4bcc1c8c75bc16d86

# ============================================
# Fireblocks 配置（Phase D使用，暂时留空）
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

**⚠️ 重要替换：**
1. `SECRET_KEY` - 运行 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 生成
2. `STRIPE_WEBHOOK_SECRET` - 粘贴从webhook监听中复制的 `whsec_***` 密钥

---

### 步骤3：生成 SECRET_KEY

**在PowerShell中运行：**

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**复制输出的密钥，替换 `.env` 文件中的 `SECRET_KEY`**

---

### 步骤4：验证配置

**在PowerShell中运行：**

```powershell
cd backend
python check_env.py
```

**预期输出：**
```
✅ 所有检查通过！您可以开始使用POSX了。
```

---

## 🎯 快速命令参考

```powershell
# 生成SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 创建.env文件
notepad .env

# 验证配置
cd backend
python check_env.py

# 启动webhook监听（如果需要重新启动）
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/

# 测试webhook（需要Django运行）
stripe trigger payment_intent.succeeded
```

---

## 📞 需要帮助？

如果遇到问题，请查看：
- `COMPLETE_ENV_SETUP.md` - 完整配置指南
- `STRIPE_CONFIG_COMPLETE.md` - Stripe详细配置

