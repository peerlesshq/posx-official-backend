# 🎯 Stripe CLI 配置完成指南

## ✅ 已完成

1. ✅ Stripe CLI 已找到：`E:\300_Code\314_POSX_Official_Sale_App\stripe.exe`
2. ✅ 版本验证：`stripe version 1.32.0`
3. ✅ PATH环境变量已添加（用户级别）
4. ✅ 当前会话已可用 `stripe` 命令

---

## 📋 下一步操作（按顺序执行）

### 步骤1：登录 Stripe CLI

**在PowerShell中运行：**

```powershell
stripe login
```

**操作流程：**
1. 按 `Enter` 键打开浏览器
2. 在浏览器中登录您的 Stripe 账号
3. 确认配对码（CLI会显示）
4. 点击 "Allow access"

**预期输出：**
```
Done! The Stripe CLI is configured for [您的账号] with account id acct_***
```

---

### 步骤2：启动 Webhook 监听

**⚠️ 重要：保持这个终端窗口打开！**

**在PowerShell中运行：**

```powershell
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**预期输出：**
```
> Ready! You are using Stripe API Version [2024-XX-XX]. 
> Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxx (^C to quit)
```

**🔑 关键：复制 `whsec_***` 这个密钥！**

---

### 步骤3：配置 .env 文件

**打开 `.env` 文件**（如果不存在，创建它）：

```powershell
notepad .env
```

**添加或更新以下配置：**

```bash
# Stripe配置
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
MOCK_STRIPE=false
```

**⚠️ 将 `whsec_xxxxxxxxxxxxxxxxxxxx` 替换为步骤2中复制的实际密钥！**

---

### 步骤4：测试 Webhook

**保持步骤2的监听窗口运行**

**打开新的PowerShell窗口，运行Django：**

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend
python manage.py runserver
```

**再打开一个PowerShell窗口，触发测试事件：**

```powershell
stripe trigger payment_intent.succeeded
```

**预期结果：**
- Stripe CLI窗口显示：`[200] POST http://localhost:8000/api/v1/webhooks/stripe/`
- Django窗口显示：`[webhook] Event received: payment_intent.succeeded`

**✅ 如果看到这些，说明配置成功！**

---

## 🔧 完整 .env 配置模板

以下是包含所有配置的完整 `.env` 文件模板：

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

# ============================================
# Fireblocks 配置（Phase D）
# ============================================
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=ETH_TEST
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=
```

**⚠️ 记得替换 `STRIPE_WEBHOOK_SECRET` 为实际值！**

---

## 🎯 快速命令参考

```powershell
# 登录Stripe
stripe login

# 启动webhook监听
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/

# 触发测试事件
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed

# 查看事件日志
stripe events tail
```

---

## ✅ 配置检查清单

完成所有步骤后，确认：

- [ ] Stripe CLI已登录（`stripe login`）
- [ ] Webhook监听正在运行（`stripe listen`）
- [ ] `.env`文件已创建并配置
- [ ] `STRIPE_WEBHOOK_SECRET`已填入实际值
- [ ] Django服务器可以启动
- [ ] 测试事件可以触发并接收

---

## 🆘 常见问题

### Q: stripe命令找不到？
**A:** 重新打开PowerShell窗口，PATH需要重启才能生效。

### Q: 登录失败？
**A:** 检查网络连接，或使用API key登录：
```powershell
stripe login --api-key sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
```

### Q: Webhook未收到事件？
**A:** 
1. 确认Django运行在8000端口
2. 确认监听命令正在运行
3. 检查路由是否正确：`/api/v1/webhooks/stripe/`

---

## 📞 下一步

配置完Stripe后，我们继续配置其他部分（数据库、Redis、Auth0等）！

