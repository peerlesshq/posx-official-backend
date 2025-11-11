# Railway 快速开始（5 分钟）

本文档提供最快的 Railway 部署步骤，适合快速演示和测试。

---

## 🚀 前提条件

- ✅ GitHub 账号
- ✅ Railway 账号（使用 GitHub 登录）
- ✅ 代码已推送到 GitHub

---

## ⚡ 5 步快速部署

### Step 1: 创建 Railway 项目（30 秒）

1. 访问 [railway.app](https://railway.app)
2. 点击 **New Project**
3. 选择 **Deploy from GitHub repo**
4. 选择 `posx-official-backend` 仓库
5. Railway 自动创建 Backend Service

### Step 2: 添加数据库（30 秒）

1. 点击 **+ New**
2. 选择 **Database → PostgreSQL**
3. 再次点击 **+ New**
4. 选择 **Database → Redis**

Railway 自动注入 `DATABASE_URL` 和 `REDIS_URL`。

### Step 3: 配置核心环境变量（2 分钟）

进入 Backend Service → **Variables**，点击 **Raw Editor**，粘贴：

```env
DJANGO_SETTINGS_MODULE=config.settings.railway
DEBUG=False
SECRET_KEY=django-insecure-REPLACE-THIS-IN-PRODUCTION
ALLOWED_HOSTS=*.up.railway.app
CSRF_TRUSTED_ORIGINS=https://your-domain.up.railway.app
CORS_ALLOWED_ORIGINS=https://posx.retool.com
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_M2M_CLIENT_ID=QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
AUTH0_M2M_CLIENT_SECRET=cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=8453
SIWE_URI=https://demo-api.posx.io
FRONTEND_URL=https://adminhq.posx.io
ALLOWED_SITE_CODES=NA,ASIA
MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=false
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@posx.io
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7
```

保存。

### Step 4: 配置启动命令（1 分钟）

进入 Backend Service → **Settings → Deploy**：

**Start Command**:
```bash
cd backend && python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2
```

保存并等待自动重新部署。

### Step 5: 验证部署（1 分钟）

1. 等待部署完成（状态变为 **Success**）
2. 进入 **Settings → Networking → Generate Domain**
3. 复制域名（如 `posx-backend-prod.up.railway.app`）
4. 访问：

```bash
curl https://<你的域名>.up.railway.app/health/
```

**期望输出**:
```json
{"status": "healthy"}
```

✅ **部署完成！**

---

## 🔧 后续配置（可选）

### 更新域名变量

回到 **Variables**，更新：

```env
ALLOWED_HOSTS=<你的实际域名>.up.railway.app
CSRF_TRUSTED_ORIGINS=https://<你的实际域名>.up.railway.app
```

### 初始化数据

进入 Backend Service → **Deployments → Shell**：

```bash
cd backend
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json
python manage.py createsuperuser --noinput --username admin --email admin@posx.io
# 密码需要通过 Django shell 设置或使用环境变量
```

---

## 📋 完整部署指南

详细配置请参考：
- [Railway 部署指南](./RAILWAY_DEPLOYMENT_GUIDE.md)
- [环境变量详解](./RAILWAY_ENV_VARIABLES.md)
- [部署验证清单](./RAILWAY_DEPLOYMENT_CHECKLIST.md)

---

**创建时间**: 2025-01-11  
**版本**: v1.0.0

