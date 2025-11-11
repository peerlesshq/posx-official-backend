# Railway 环境变量完整清单

本文档提供 Railway 部署所需的所有环境变量，按照 Railway 建议的变量顺序和最佳实践组织。

---

## 快速复制（适用于 Railway Variables 页面）

### 方式 1: 逐个添加（推荐）

在 Railway Backend Service → **Variables** → **+ New Variable**，逐个添加以下变量。

### 方式 2: Raw Editor（批量添加）

点击 **Raw Editor** 按钮，粘贴以下内容（需手动替换占位符）：

```env
# ============================================
# Django 核心配置
# ============================================
DJANGO_SETTINGS_MODULE=config.settings.railway
DEBUG=False
SECRET_KEY=<生成随机密钥>

# ============================================
# 域名配置（部署后填写）
# ============================================
ALLOWED_HOSTS=*.up.railway.app,localhost
CSRF_TRUSTED_ORIGINS=https://<Railway域名>.up.railway.app
CORS_ALLOWED_ORIGINS=https://posx.retool.com

# ============================================
# Auth0 认证
# ============================================
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_M2M_CLIENT_ID=QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
AUTH0_M2M_CLIENT_SECRET=cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP

# ============================================
# SIWE 配置
# ============================================
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=8453
SIWE_URI=https://demo-api.posx.io

# ============================================
# 前端配置
# ============================================
FRONTEND_URL=https://adminhq.posx.io
API_EXTERNAL_URL=https://<Railway域名>.up.railway.app
ALLOWED_SITE_CODES=NA,ASIA

# ============================================
# Stripe（Mock 模式）
# ============================================
MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# ============================================
# Fireblocks（Mock 模式）
# ============================================
FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=false
FIREBLOCKS_API_KEY=mock_key
FIREBLOCKS_PRIVATE_KEY=mock_private_key
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=ETH_TEST
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=

# ============================================
# Celery
# ============================================
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}

# ============================================
# Email（Console 模式）
# ============================================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@posx.io

# ============================================
# 业务配置
# ============================================
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7
```

---

## 详细说明（按类别）

### 1. Django 核心配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DJANGO_SETTINGS_MODULE` | ✅ | - | 使用 `config.settings.railway` |
| `DEBUG` | ✅ | `False` | 生产环境必须为 `False` |
| `SECRET_KEY` | ✅ | - | 随机密钥，生成方法见下方 |

**生成 SECRET_KEY**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### 2. 域名与安全配置

| 变量名 | 必填 | 示例值 | 说明 |
|--------|------|--------|------|
| `ALLOWED_HOSTS` | ✅ | `posx-backend-prod.up.railway.app` | Railway 分配的域名，支持通配符 `*.up.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | `https://posx-backend-prod.up.railway.app` | 必须带 `https://`，逗号分隔多个域名 |
| `CORS_ALLOWED_ORIGINS` | ⭕ | `https://posx.retool.com` | 允许跨域的前端域名，逗号分隔 |

⚠️ **注意**：首次部署时，Railway 还未分配域名，可先填 `*.up.railway.app`，部署后再更新为具体域名。

---

### 3. 数据库配置（Railway 自动注入）

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DATABASE_URL` | ✅ | Railway PostgreSQL Service 自动注入，无需手动配置 |

**格式示例**:
```
postgresql://postgres:password@host.railway.internal:5432/railway
```

---

### 4. Redis 配置（Railway 自动注入）

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `REDIS_URL` | ✅ | Railway Redis Service 自动注入 |
| `CELERY_BROKER_URL` | ✅ | 引用 `${{REDIS_URL}}` |
| `CELERY_RESULT_BACKEND` | ✅ | 引用 `${{REDIS_URL}}` |

**格式示例**:
```
redis://default:password@host.railway.internal:6379
```

---

### 5. Auth0 认证

| 变量名 | 必填 | 示例值 | 说明 |
|--------|------|--------|------|
| `AUTH0_DOMAIN` | ✅ | `dev-posx.us.auth0.com` | Auth0 Tenant 域名（不含 `https://`） |
| `AUTH0_AUDIENCE` | ✅ | `https://demo-api.posx.io/api/v1/` | API Identifier，必须与 Auth0 Dashboard 完全一致（含尾部斜杠） |
| `AUTH0_ISSUER` | ✅ | `https://dev-posx.us.auth0.com/` | Issuer URL，必须带尾部斜杠 |
| `AUTH0_M2M_CLIENT_ID` | ✅ | `QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK` | Machine-to-Machine Client ID |
| `AUTH0_M2M_CLIENT_SECRET` | ✅ | `cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP` | M2M Client Secret |

⚠️ **常见错误**：
- ❌ `AUTH0_AUDIENCE` 缺少尾部斜杠 → 导致 401 Unauthorized
- ❌ `AUTH0_ISSUER` 缺少 `https://` 或尾部斜杠 → JWT 验证失败

---

### 6. SIWE（Sign-In with Ethereum）

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `SIWE_DOMAIN` | ✅ | `posx.io` | 应用域名（不含协议） |
| `SIWE_CHAIN_ID` | ✅ | `8453` | 区块链 ID（1=Ethereum, 8453=Base） |
| `SIWE_URI` | ✅ | `https://demo-api.posx.io` | 应用完整 URL |

---

### 7. 前端配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `FRONTEND_URL` | ✅ | `https://adminhq.posx.io` | 前端应用 URL |
| `API_EXTERNAL_URL` | ⭕ | - | 后端 API 对外 URL（可选，留空则使用 Railway 域名） |
| `ALLOWED_SITE_CODES` | ✅ | `NA,ASIA` | 允许的站点代码，逗号分隔 |

---

### 8. Stripe 配置

#### Demo 环境（Mock 模式）

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `MOCK_STRIPE` | ✅ | `true` | 启用 Mock 模式，不调用真实 Stripe API |
| `STRIPE_SECRET_KEY` | ⭕ | `sk_test_placeholder` | Mock 模式下可用占位符 |
| `STRIPE_PUBLISHABLE_KEY` | ⭕ | `pk_test_placeholder` | Mock 模式下可用占位符 |
| `STRIPE_WEBHOOK_SECRET` | ⭕ | `whsec_placeholder` | Mock 模式下可用占位符 |

#### 真实 Stripe（测试环境）

| 变量名 | 必填 | 示例值 | 说明 |
|--------|------|--------|------|
| `MOCK_STRIPE` | ✅ | `false` | 禁用 Mock，使用真实 Stripe |
| `STRIPE_SECRET_KEY` | ✅ | `sk_test_51...` | Stripe 测试密钥（以 `sk_test_` 开头） |
| `STRIPE_PUBLISHABLE_KEY` | ✅ | `pk_test_51...` | Stripe 可发布密钥 |
| `STRIPE_WEBHOOK_SECRET` | ✅ | `whsec_...` | Webhook 签名密钥（创建 Webhook 后获取） |

⚠️ **注意**：生产环境使用 `sk_live_` 和 `pk_live_` 开头的密钥。

---

### 9. Fireblocks 配置

#### Demo 环境（Mock 模式）

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `FIREBLOCKS_MODE` | ✅ | `MOCK` | 使用 Mock 模式，不调用真实 Fireblocks |
| `ALLOW_PROD_TX` | ✅ | `false` | 禁止生产交易 |
| `FIREBLOCKS_API_KEY` | ⭕ | `mock_key` | Mock 模式占位符 |
| `FIREBLOCKS_PRIVATE_KEY` | ⭕ | `mock_private_key` | Mock 模式占位符 |
| `FIREBLOCKS_BASE_URL` | ⭕ | `https://sandbox-api.fireblocks.io` | Sandbox API |
| `FIREBLOCKS_VAULT_ACCOUNT_ID` | ⭕ | `0` | Vault 账户 ID |
| `FIREBLOCKS_ASSET_ID` | ⭕ | `ETH_TEST` | 资产 ID |
| `FIREBLOCKS_WEBHOOK_PUBLIC_KEY` | ⭕ | - | Webhook 公钥（可选） |

#### 真实 Fireblocks（生产环境）

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `FIREBLOCKS_MODE` | ✅ | 设置为 `LIVE` |
| `ALLOW_PROD_TX` | ✅ | 设置为 `true`（生产环境双确认） |
| `FIREBLOCKS_API_KEY` | ✅ | 真实 API Key |
| `FIREBLOCKS_PRIVATE_KEY` | ✅ | 私钥路径或内容 |
| `FIREBLOCKS_BASE_URL` | ✅ | `https://api.fireblocks.io` |
| `FIREBLOCKS_VAULT_ACCOUNT_ID` | ✅ | 真实 Vault ID |
| `FIREBLOCKS_ASSET_ID` | ✅ | 真实资产 ID（如 `ETH`, `USDC`） |

---

### 10. Email 配置

#### Demo 环境（Console 模式）

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `EMAIL_BACKEND` | ✅ | `django.core.mail.backends.console.EmailBackend` | 输出到日志，不发送真实邮件 |
| `DEFAULT_FROM_EMAIL` | ⭕ | `noreply@posx.io` | 发件人地址 |

#### 真实 Email（SendGrid/SMTP）

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `EMAIL_BACKEND` | ✅ | `django.core.mail.backends.smtp.EmailBackend` | 使用 SMTP 发送 |
| `EMAIL_HOST` | ✅ | `smtp.sendgrid.net` | SMTP 服务器 |
| `EMAIL_PORT` | ✅ | `587` | SMTP 端口 |
| `EMAIL_HOST_USER` | ✅ | - | SMTP 用户名 |
| `EMAIL_HOST_PASSWORD` | ✅ | - | SMTP 密码 |
| `DEFAULT_FROM_EMAIL` | ✅ | `noreply@posx.io` | 发件人地址 |

---

### 11. 业务配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NONCE_TTL_SECONDS` | ⭕ | `300` | Nonce 有效期（秒） |
| `ORDER_EXPIRE_MINUTES` | ⭕ | `15` | 订单过期时间（分钟） |
| `MAX_QUANTITY_PER_ORDER` | ⭕ | `1000` | 单笔订单最大数量 |
| `IDEMPOTENCY_KEY_RETENTION_HOURS` | ⭕ | `48` | 幂等键保留时间（小时） |
| `COMMISSION_HOLD_DAYS` | ⭕ | `7` | 佣金持有期（天） |

---

### 12. 监控配置（可选）

#### Sentry

| 变量名 | 必填 | 示例值 | 说明 |
|--------|------|--------|------|
| `SENTRY_DSN` | ⭕ | `https://...@sentry.io/...` | Sentry DSN，留空则禁用 |
| `SENTRY_ENVIRONMENT` | ⭕ | `railway-demo` | 环境标识 |
| `SENTRY_TRACES_SAMPLE_RATE` | ⭕ | `0.1` | 性能追踪采样率（10%） |

---

### 13. Railway 自动注入变量

以下变量由 Railway 自动管理，**无需手动配置**：

| 变量名 | 说明 |
|--------|------|
| `PORT` | 服务监听端口（默认自动分配） |
| `RAILWAY_ENVIRONMENT` | 环境名称（如 `production`） |
| `RAILWAY_PROJECT_ID` | 项目 ID |
| `RAILWAY_SERVICE_ID` | 服务 ID |
| `DATABASE_URL` | PostgreSQL 连接串（添加 PostgreSQL Service 后自动注入） |
| `REDIS_URL` | Redis 连接串（添加 Redis Service 后自动注入） |

---

## 变量优先级

Railway 环境变量加载顺序：

1. **Railway Variables**（最高优先级）
2. **Shared Variables**（跨 Service 共享）
3. **Service-specific Variables**
4. `.env` 文件（不推荐，Railway 不支持）

---

## 常见问题

### Q1: 如何引用其他变量？

使用 `${{VARIABLE_NAME}}` 语法：

```bash
CELERY_BROKER_URL=${{REDIS_URL}}
```

### Q2: 如何设置多个值（列表）？

使用逗号分隔：

```bash
ALLOWED_HOSTS=domain1.com,domain2.com,*.railway.app
```

代码中自动解析为列表：

```python
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
```

### Q3: 如何处理带空格的值？

Railway 自动处理，无需引号：

```bash
SECRET_KEY=abc 123 xyz  # ✅ 正确
```

### Q4: 如何查看变量是否生效？

在 Railway Shell 中检查：

```bash
echo $DATABASE_URL
echo $REDIS_URL
```

或在 Django Shell 中：

```python
from django.conf import settings
print(settings.DATABASE_URL)
```

### Q5: 变量更新后需要重启吗？

是的！修改环境变量后，必须：
1. 保存变量
2. 点击 **Redeploy** 或推送代码触发重新部署

---

## 部署后验证

### 1. 检查关键变量

在 Railway Shell 执行：

```bash
cd backend
python manage.py shell
```

```python
from django.conf import settings

# 核心配置
print(f"DEBUG: {settings.DEBUG}")  # 应为 False
print(f"ENV: {settings.ENV}")  # 应为 railway-demo

# 数据库
print(f"DB Host: {settings.DATABASES['default']['HOST']}")

# Redis
print(f"Redis: {settings.REDIS_URL}")

# Auth0
print(f"Auth0 Audience: {settings.AUTH0_AUDIENCE}")

# Stripe
print(f"Stripe Mock: {settings.MOCK_STRIPE}")
```

### 2. 测试健康检查

```bash
curl https://<Railway域名>.up.railway.app/ready/
```

期望输出：

```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "migrations": "ok",
    "rls": "ok"
  }
}
```

---

## 变量模板文件

### 创建本地参考文件（不提交到 Git）

在项目根目录创建 `.env.railway.example`：

```bash
# 复制以下内容，替换占位符后使用
DJANGO_SETTINGS_MODULE=config.settings.railway
DEBUG=False
SECRET_KEY=<生成>

# ... 其他变量 ...
```

添加到 `.gitignore`：

```
.env.railway
.env.railway.local
```

---

## 相关文档

- [Railway 部署指南](./RAILWAY_DEPLOYMENT_GUIDE.md)
- [环境变量说明](../config/CONFIG_ENV_VARIABLES.md)
- [Auth0 配置](../config/CONFIG_AUTH0.md)
- [Stripe 配置](../config/CONFIG_STRIPE.md)

---

**创建时间**: 2025-01-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

