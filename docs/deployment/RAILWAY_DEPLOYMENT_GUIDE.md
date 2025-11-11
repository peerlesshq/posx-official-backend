# Railway Demo 部署指南

## 概述

本指南详细说明如何将 POSX Backend 部署到 Railway 平台的 Demo 环境。

**关键特性**：
- ✅ 移除 AWS S3 依赖（使用 WhiteNoise 本地静态文件）
- ✅ 自动配置 PostgreSQL 和 Redis
- ✅ Mock 模式 Stripe 和 Fireblocks（可切换真实密钥）
- ✅ 严格 CSP 和安全头配置
- ✅ Celery Worker 和 Beat 支持

---

## 前置条件

### 1. 准备工作
- ✅ Railway 账号（GitHub 授权登录）
- ✅ GitHub 仓库已推送最新代码
- ✅ Auth0 已配置（获取 Domain、Client ID、Secret）
- ✅ Stripe 测试账号（可选，可使用 Mock 模式）

### 2. 必需的环境变量
以下变量必须在 Railway 中配置，详见[环境变量清单](#环境变量完整清单)。

---

## 快速部署（5 分钟）

### Step 1: 创建 Railway 项目

1. 访问 [railway.app](https://railway.app)
2. 点击 **New Project**
3. 选择 **Deploy from GitHub repo**
4. 授权并选择 `posx-official-backend` 仓库
5. Railway 自动创建 Service

### Step 2: 添加数据库服务

1. 在项目页面点击 **+ New**
2. 选择 **Database → PostgreSQL**
3. Railway 自动创建并注入 `DATABASE_URL`

### Step 3: 添加 Redis

1. 点击 **+ New**
2. 选择 **Database → Redis**
3. Railway 自动创建并注入 `REDIS_URL`

### Step 4: 配置环境变量

进入 Backend Service → **Variables** 标签，添加以下变量：

#### 核心配置（必填）
```bash
DJANGO_SETTINGS_MODULE=config.settings.railway
SECRET_KEY=<点击生成或使用命令生成>
DEBUG=False
```

#### 域名与安全（部署后填写）
```bash
ALLOWED_HOSTS=<Railway分配的域名>.up.railway.app,demo-api.posx.io
CSRF_TRUSTED_ORIGINS=https://<Railway域名>.up.railway.app
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io
```

#### Auth0
```bash
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_M2M_CLIENT_ID=<你的 Client ID>
AUTH0_M2M_CLIENT_SECRET=<你的 Client Secret>
```

#### SIWE
```bash
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=8453
SIWE_URI=https://demo-api.posx.io
```

#### 前端
```bash
FRONTEND_URL=https://adminhq.posx.io
API_EXTERNAL_URL=https://<Railway域名>.up.railway.app
ALLOWED_SITE_CODES=NA,ASIA
```

#### Stripe（Mock 模式）
```bash
MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
```

#### Fireblocks（Mock 模式）
```bash
FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=false
FIREBLOCKS_API_KEY=mock_key
FIREBLOCKS_PRIVATE_KEY=mock_private_key
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=ETH_TEST
```

#### Email（Console 模式）
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@posx.io
```

#### Celery
```bash
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
```

#### 业务配置
```bash
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7
```

### Step 5: 配置构建设置

进入 Backend Service → **Settings**：

#### Build Command（可选）
```bash
pip install -r backend/requirements/production.txt
```

#### Start Command
```bash
cd backend && python manage.py collectstatic --noinput && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2
```

> ⚠️ **注意**：首次部署后，迁移和 collectstatic 可能失败，需要在 Shell 中手动执行。

### Step 6: 添加 Celery Worker（可选）

1. 点击 **+ New → Empty Service**
2. 连接相同的 GitHub 仓库
3. **Service Name**: `celery-worker`
4. **Start Command**:
   ```bash
   cd backend && celery -A config worker -l info
   ```
5. 共享相同的环境变量（使用 Shared Variables 或手动复制）

### Step 7: 添加 Celery Beat（可选）

1. 点击 **+ New → Empty Service**
2. **Service Name**: `celery-beat`
3. **Start Command**:
   ```bash
   cd backend && celery -A config beat -l info
   ```

---

## 部署后配置

### 1. 获取域名

部署完成后，Railway 自动分配域名：

1. 进入 Backend Service → **Settings → Domains**
2. 点击 **Generate Domain**
3. 复制域名（形如 `posx-backend-production-abc123.up.railway.app`）

### 2. 更新环境变量

回到 **Variables**，更新以下变量：

```bash
ALLOWED_HOSTS=posx-backend-production-abc123.up.railway.app,localhost
CSRF_TRUSTED_ORIGINS=https://posx-backend-production-abc123.up.railway.app
API_EXTERNAL_URL=https://posx-backend-production-abc123.up.railway.app
```

保存后点击 **Redeploy**。

### 3. 执行初始化命令

进入 Backend Service → **Deployments → 最新部署 → Shell**：

#### 运行迁移
```bash
cd backend
python manage.py migrate
```

#### 收集静态文件
```bash
python manage.py collectstatic --noinput
```

#### 加载种子数据
```bash
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json
```

#### 创建超级用户
```bash
python manage.py createsuperuser --noinput --username admin --email admin@posx.io
# 设置密码（交互式）
```

或使用环境变量：
```bash
DJANGO_SUPERUSER_PASSWORD=YourStrongPassword123! python manage.py createsuperuser --noinput --username admin --email admin@posx.io
```

### 4. 验证部署

访问以下端点：

#### Health Check
```bash
curl https://<Railway域名>.up.railway.app/health/
# 期望输出: {"status": "healthy"}
```

#### Ready Check
```bash
curl https://<Railway域名>.up.railway.app/ready/
# 期望输出: {"status": "healthy", "checks": {"database": "ok", "redis": "ok", ...}}
```

#### Version
```bash
curl https://<Railway域名>.up.railway.app/version/
# 期望输出: {"version": "1.0.0", "env": "railway-demo"}
```

---

## 配置 Stripe Webhook

### 1. 在 Stripe Dashboard 创建 Webhook

1. 登录 [Stripe Dashboard](https://dashboard.stripe.com/test/webhooks)
2. 点击 **Add endpoint**
3. **Endpoint URL**: `https://<Railway域名>.up.railway.app/api/v1/webhooks/stripe/`
4. **API version**: `2025-08-27.basil`（或最新）
5. **Events to send**: 选择以下事件：
   - ✅ `payment_intent.succeeded`
   - ✅ `payment_intent.payment_failed`
   - ✅ `charge.succeeded`
   - ✅ `charge.failed`
   - ✅ `charge.refunded`
   - ✅ `charge.dispute.created`
   - ⭕ `checkout.session.completed`（如使用 Checkout）
   - ⭕ `payment_intent.canceled`

6. 点击 **Add endpoint**
7. 复制生成的 **Signing secret**（形如 `whsec_...`）

### 2. 更新 Railway 环境变量

```bash
MOCK_STRIPE=false
STRIPE_WEBHOOK_SECRET=whsec_你复制的密钥
STRIPE_SECRET_KEY=sk_test_你的测试密钥
STRIPE_PUBLISHABLE_KEY=pk_test_你的测试密钥
```

保存并 **Redeploy**。

### 3. 测试 Webhook

#### 方法 1: Stripe Dashboard
1. 回到 Stripe Webhooks 页面
2. 点击你的 endpoint → **Send test webhook**
3. 选择 `payment_intent.succeeded`
4. 点击 **Send test webhook**
5. 查看 Railway 日志（应显示 `[INFO] Received Stripe webhook: payment_intent.succeeded`）

#### 方法 2: Stripe CLI（本地）
```bash
stripe trigger payment_intent.succeeded --webhook-endpoint https://<Railway域名>.up.railway.app/api/v1/webhooks/stripe/
```

---

## 添加自定义域名（可选）

### 1. 在 Railway 添加域名

1. 进入 Backend Service → **Settings → Domains**
2. 点击 **Custom Domain**
3. 输入 `demo-api.posx.io`
4. Railway 会提供 CNAME 记录

### 2. 配置 DNS

在你的 DNS 提供商（如 Cloudflare）添加：

```
Type: CNAME
Name: demo-api
Target: <Railway提供的目标>
Proxy: 关闭（灰色云朵）
```

### 3. 更新环境变量

```bash
ALLOWED_HOSTS=demo-api.posx.io,posx-backend-production-abc123.up.railway.app
CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
API_EXTERNAL_URL=https://demo-api.posx.io
SIWE_URI=https://demo-api.posx.io
```

更新 Stripe Webhook URL 为 `https://demo-api.posx.io/api/v1/webhooks/stripe/`。

---

## 环境变量完整清单

<details>
<summary>点击展开完整清单（40+ 变量）</summary>

```bash
# ============================================
# Django 核心
# ============================================
DJANGO_SETTINGS_MODULE=config.settings.railway
SECRET_KEY=<生成随机密钥>
DEBUG=False
ENV=railway-demo

# ============================================
# 域名与安全
# ============================================
ALLOWED_HOSTS=<Railway域名>.up.railway.app
CSRF_TRUSTED_ORIGINS=https://<Railway域名>.up.railway.app
CORS_ALLOWED_ORIGINS=https://posx.retool.com

# ============================================
# 数据库（Railway 自动注入）
# ============================================
DATABASE_URL=<Railway自动生成>

# ============================================
# Redis（Railway 自动注入）
# ============================================
REDIS_URL=<Railway自动生成>
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}

# ============================================
# Auth0
# ============================================
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_M2M_CLIENT_ID=<Client ID>
AUTH0_M2M_CLIENT_SECRET=<Client Secret>

# ============================================
# SIWE
# ============================================
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=8453
SIWE_URI=https://demo-api.posx.io

# ============================================
# 前端
# ============================================
FRONTEND_URL=https://adminhq.posx.io
API_EXTERNAL_URL=https://<Railway域名>.up.railway.app
ALLOWED_SITE_CODES=NA,ASIA

# ============================================
# Stripe
# ============================================
MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# ============================================
# Fireblocks
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
# Email
# ============================================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@posx.io

# ============================================
# 业务配置
# ============================================
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7

# ============================================
# Sentry（可选）
# ============================================
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.1

# ============================================
# Railway 自动注入
# ============================================
PORT=<Railway自动设置>
RAILWAY_ENVIRONMENT=production
```

</details>

---

## 故障排查

### 问题 1: 部署失败 - "No module named 'dj_database_url'"

**原因**: 缺少依赖  
**解决**:

```bash
# 在 backend/requirements/production.txt 添加
dj-database-url==2.1.0
whitenoise==6.6.0
```

提交并推送，Railway 自动重新部署。

### 问题 2: 静态文件 404

**原因**: `collectstatic` 未执行或 WhiteNoise 未配置  
**解决**:

1. 检查 `config/settings/railway.py` 是否包含：
   ```python
   MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

2. 在 Railway Shell 执行：
   ```bash
   cd backend
   python manage.py collectstatic --noinput
   ```

### 问题 3: 数据库连接失败

**原因**: `DATABASE_URL` 未正确注入  
**解决**:

1. 检查 PostgreSQL Service 状态（应为 `Active`）
2. 查看环境变量：进入 Backend Service → Variables，确认 `DATABASE_URL` 存在
3. 如手动配置，确保格式正确：
   ```
   postgresql://user:password@host:5432/dbname
   ```

### 问题 4: Redis 连接超时

**原因**: Redis Service 未启动或 URL 错误  
**解决**:

1. 检查 Redis Service 状态
2. 确认 `REDIS_URL` 格式：`redis://host:6379/0`
3. 减少连接池大小（Railway 资源有限）：
   ```python
   # config/settings/railway.py
   'max_connections': 10,  # 降低到 10
   ```

### 问题 5: Stripe Webhook 返回 400

**原因**: 签名验证失败  
**解决**:

1. 确认 `STRIPE_WEBHOOK_SECRET` 与 Stripe Dashboard 一致
2. 检查 Railway 日志：
   ```
   [ERROR] Signature verification failed: ...
   ```
3. 重新创建 Webhook endpoint，获取新的 Signing Secret
4. 确保 Webhook URL 完全匹配（含 `https://` 和路径 `/api/v1/webhooks/stripe/`）

### 问题 6: Celery Worker 无法启动

**原因**: Redis 连接失败或配置错误  
**解决**:

1. 检查 Worker Service 的环境变量是否包含 `CELERY_BROKER_URL`
2. 查看 Worker 日志：
   ```bash
   # 在 Railway Celery Worker Service → Logs
   ```
3. 确认与 Backend 使用相同的 `REDIS_URL`

### 问题 7: RLS 策略未生效

**原因**: 迁移未执行或权限问题  
**解决**:

1. 检查迁移状态：
   ```bash
   cd backend
   python manage.py showmigrations
   ```

2. 手动执行 RLS 迁移：
   ```bash
   python manage.py migrate core 0004
   ```

3. 验证 RLS：
   ```bash
   curl https://<Railway域名>.up.railway.app/ready/
   # 检查 "rls": "ok"
   ```

### 问题 8: 401 Unauthorized（Auth0）

**原因**: Audience 不匹配或 JWT 过期  
**解决**:

1. 确认 `AUTH0_AUDIENCE` 与 Auth0 Dashboard → APIs → Identifier 完全一致（包括尾部斜杠）
2. 检查 JWT payload：
   ```bash
   # 在 https://jwt.io 解码 token
   # 确认 "aud" 字段与 AUTH0_AUDIENCE 一致
   ```
3. 增加 Clock Skew 容忍度（已在 `railway.py` 设置为 60 秒）

### 问题 9: CORS 错误

**原因**: Origin 不在白名单  
**解决**:

1. 添加前端域名到 `CORS_ALLOWED_ORIGINS`：
   ```bash
   CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://your-frontend.com
   ```

2. 检查请求头：
   ```bash
   curl -H "Origin: https://posx.retool.com" https://<Railway域名>.up.railway.app/api/v1/test/public/
   # 应返回 Access-Control-Allow-Origin 头
   ```

---

## 日常运维

### 查看日志
```bash
# 在 Railway Dashboard
Backend Service → Deployments → 最新部署 → Logs
```

### 重启服务
```bash
# 在 Railway Dashboard
Backend Service → Settings → Restart
```

### 手动部署
```bash
# 推送代码到 GitHub
git push origin main

# Railway 自动触发部署
```

### 执行管理命令
```bash
# 在 Railway Shell
cd backend
python manage.py <command>
```

### 备份数据库
```bash
# 在 PostgreSQL Service → Data → Backups
# 手动创建快照
```

---

## 性能优化

### 1. 调整 Gunicorn Workers

根据 Railway 机器配置调整：

```bash
# Start Command
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60
```

**推荐配置**：
- **Hobby Plan**: `--workers 2 --threads 2`
- **Pro Plan**: `--workers 4 --threads 4`

### 2. 启用持久化存储（可选）

Railway 默认是临时存储，需要持久化 Media 文件：

1. 创建 Volume：Backend Service → **Data → Add Volume**
2. Mount Path: `/app/backend/mediafiles`
3. 更新 `MEDIA_ROOT` 指向 Volume

### 3. 配置 Redis 最大内存

```bash
# 在 Redis Service → Variables
REDIS_MAXMEMORY=256mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

---

## 安全检查清单

部署完成后，执行以下检查：

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` 已更换为随机值（不使用开发环境密钥）
- [ ] HTTPS 强制跳转启用（`SECURE_SSL_REDIRECT=True`）
- [ ] CSRF 和 Session Cookie 设置为 Secure
- [ ] CSP 无 `'unsafe-inline'`
- [ ] Auth0 仅使用 RS256 算法
- [ ] Stripe Webhook 签名验证启用
- [ ] RLS 策略全部激活（`/ready/` 返回 `"rls": "ok"`）
- [ ] 数据库密码强度足够（Railway 自动生成）
- [ ] 生产环境禁用 Mock 模式（或仅在明确需要时启用）
- [ ] 管理员账号密码已修改（不使用默认密码）

---

## 从 Demo 切换到生产

### 1. 更新 Stripe 为生产密钥

```bash
MOCK_STRIPE=false
STRIPE_SECRET_KEY=sk_live_你的生产密钥
STRIPE_PUBLISHABLE_KEY=pk_live_你的生产密钥
STRIPE_WEBHOOK_SECRET=whsec_生产环境签名密钥
```

### 2. 更新 Fireblocks 为生产 API

```bash
FIREBLOCKS_MODE=LIVE
ALLOW_PROD_TX=true
FIREBLOCKS_BASE_URL=https://api.fireblocks.io
FIREBLOCKS_API_KEY=<生产API密钥>
FIREBLOCKS_PRIVATE_KEY=<生产私钥>
```

### 3. 配置真实 Email 服务

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=<SendGrid用户名>
EMAIL_HOST_PASSWORD=<SendGrid密码>
```

### 4. 启用 Sentry 监控

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 5. 更新 SIWE 为主网

```bash
SIWE_CHAIN_ID=1  # Ethereum 主网
# 或
SIWE_CHAIN_ID=8453  # Base 主网
```

---

## 相关文档

- [环境变量说明](../config/CONFIG_ENV_VARIABLES.md)
- [Auth0 配置](../config/CONFIG_AUTH0.md)
- [Stripe 配置](../config/CONFIG_STRIPE.md)
- [RLS 配置](../specs/POSX_System_Specification_RLS.md)
- [Production Checklist](../../PRODUCTION_CHECKLIST.md)

---

**部署完成后访问**：
- 🌐 API: `https://<Railway域名>.up.railway.app/api/v1/`
- 🔧 Admin: `https://<Railway域名>.up.railway.app/admin/`
- ✅ Health: `https://<Railway域名>.up.railway.app/ready/`

**如遇问题**：
- 查看 Railway 日志
- 检查环境变量拼写
- 确认所有服务状态为 `Active`
- 参考故障排查章节

---

**创建时间**: 2025-01-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

