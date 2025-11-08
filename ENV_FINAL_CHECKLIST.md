# ⚠️ 重要提醒：.env 最终核对清单

## 📋 核对完成的配置项

### ✅ 已添加的关键配置

```bash
# 环境标识（与Redis前缀保持一致）
ENV=local

# 数据库URL（作为兜底，优先级高于单独配置）
DATABASE_URL=postgresql://posx_app:posx@localhost:5432/posx_local

# CSRF信任源（前后端分离必须）
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🔍 必须人工核对的配置

### 1. Auth0 Audience 一致性 ⚠️

**当前配置：**
```bash
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
```

**核对步骤：**
1. 打开 Auth0 控制台：https://manage.auth0.com/
2. 进入：**Applications → APIs → POSX API**
3. 查看 **Identifier** 字段
4. **确认是否包含尾部斜杠 `/`**

**如果不一致，修改 .env：**
```bash
# 情况1：控制台有斜杠
AUTH0_AUDIENCE=http://localhost:8000/api/v1/

# 情况2：控制台没有斜杠
AUTH0_AUDIENCE=http://localhost:8000/api/v1
```

**⚠️ 这个必须完全一致，否则 JWT 验证会失败！**

---

### 2. Stripe Webhook Secret 同步 ⚠️

**重要提醒：**
- `stripe listen` 每次重启时，检查输出的 `whsec_***`
- 如果与 `.env` 中的不同，**必须同步更新**

**检查命令：**
```powershell
# 查看当前监听的 secret
stripe listen --print-secret
```

**输出示例：**
```
whsec_4b0b79987be979c07fe98e3df7d7353bb2a7ae5cc0227d0f01083c174120dbf9
```

**对比 .env 中的值：**
```bash
STRIPE_WEBHOOK_SECRET=whsec_4b0b79987be979c07fe98e3df7d7353bb2a7ae5cc0227d0f01083c174120dbf9
```

**如果不一致：**
1. 更新 `.env` 文件中的 `STRIPE_WEBHOOK_SECRET`
2. **重启 Django 服务器**

---

### 3. 生产环境的 Stripe Webhook（可选）

**开发环境（当前）：**
- 使用 `stripe listen`
- 每次重启 `whsec_***` 可能变化

**生产环境（未来）：**
- 在 Stripe Dashboard 配置固定端点
- `whsec_***` 固定不变
- 更稳定

**配置步骤（生产时）：**
1. 登录 Stripe Dashboard
2. 进入：**Developers → Webhooks**
3. 点击 **Add endpoint**
4. 输入：`https://yourdomain.com/api/v1/webhooks/stripe/`
5. 选择事件：`payment_intent.succeeded`, `payment_intent.payment_failed`
6. 获取 **Signing secret**，更新到 `.env`

---

## 📝 .env 最终配置模板（含所有核对项）

```bash
# ============================================
# Django 核心配置
# ============================================
SECRET_KEY=django-insecure-Gnmt-VgUUAGxdkK8WEz5FED1E5xo8mUM3XjmHe_w7WyzY8GpJ7F0Tb41oC33G0C86x0
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
# 兜底配置（优先级高于上面的单独配置）
DATABASE_URL=postgresql://posx_app:posx@localhost:5432/posx_local

# ============================================
# Redis 配置（Docker）
# ============================================
REDIS_URL=redis://localhost:6379/0

# ============================================
# Auth0 配置
# ⚠️ 核对：AUTH0_AUDIENCE 必须与控制台完全一致！
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
# ⚠️ 核对：STRIPE_WEBHOOK_SECRET 必须与 stripe listen 输出一致！
# ============================================
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=whsec_4b0b79987be979c07fe98e3df7d7353bb2a7ae5cc0227d0f01083c174120dbf9
MOCK_STRIPE=false

# ============================================
# 订单配置
# ============================================
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
# ⚠️ 已更新：与Redis前缀保持一致
ENV=local

# ============================================
# Celery 配置
# ============================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false

# ============================================
# 前端配置
# ⚠️ 已添加：CSRF_TRUSTED_ORIGINS
# ============================================
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
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

---

## ✅ 核对完成后的下一步

1. **保存 .env 文件**
2. **按照 `STARTUP_AND_TEST_GUIDE.md` 启动所有服务**
3. **运行端到端测试**

---

## 📞 快速核对命令

```powershell
# 1. 查看 .env 配置
cat .env

# 2. 检查 Stripe webhook secret
stripe listen --print-secret

# 3. 验证配置
python backend/check_env_simple.py
```

---

## 🎯 总结

### 必须人工核对的3项：

1. ✅ **AUTH0_AUDIENCE** - 与控制台完全一致（包括尾部 `/`）
2. ✅ **STRIPE_WEBHOOK_SECRET** - 与 `stripe listen` 输出一致
3. ✅ **所有配置项** - 无拼写错误，无多余空格

### 已自动添加的3项：

1. ✅ **ENV=local** - 与Redis前缀一致
2. ✅ **DATABASE_URL** - 数据库连接兜底
3. ✅ **CSRF_TRUSTED_ORIGINS** - 前后端分离必须

---

核对完成后即可开始测试！🎉

