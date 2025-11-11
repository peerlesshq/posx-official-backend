# 🚂 POSX Railway 部署总结

本文档总结了为 Railway Demo 环境部署 POSX Backend 所创建的所有配置和文档。

---

## 📦 创建的文件

### 1. 核心配置

#### `backend/config/settings/railway.py`
- Railway 专用 Django 设置
- 移除 AWS S3 依赖
- 使用 WhiteNoise 服务静态文件
- 自动解析 Railway 的 `DATABASE_URL` 和 `REDIS_URL`
- Mock 模式支付和区块链服务
- 严格 CSP 和安全头配置

**关键特性**:
- ✅ 无需 S3（使用本地 `staticfiles`）
- ✅ 自动 HTTPS 和安全头
- ✅ Mock Stripe 和 Fireblocks
- ✅ 简化日志配置（仅 console）

---

### 2. 部署文档

#### `docs/deployment/RAILWAY_DEPLOYMENT_GUIDE.md`（主文档）
完整的 Railway 部署指南，包含：
- 前置条件检查
- 快速部署（5 分钟）
- 详细配置步骤
- Stripe Webhook 配置
- 自定义域名设置
- 40+ 环境变量清单
- 故障排查（9 个常见问题）
- 性能优化建议
- 安全检查清单
- 从 Demo 切换到生产

#### `docs/deployment/RAILWAY_ENV_VARIABLES.md`
环境变量完整参考：
- 按类别组织（Django/Auth0/Stripe/Fireblocks/Email/业务配置）
- 每个变量的说明、默认值、示例
- 必填/可选标注
- 常见问题解答
- 变量模板文件

#### `docs/deployment/RAILWAY_SERVICE_CONFIGURATION.md`
Railway 多服务配置详解：
- 5 个 Service 的详细配置（Backend/PostgreSQL/Redis/Celery Worker/Beat）
- 架构图和依赖关系
- 启动命令和参数说明
- 资源优化策略
- 监控与日志
- 故障排查

#### `docs/deployment/RAILWAY_STRIPE_WEBHOOK.md`
Stripe Webhook 专项指南：
- 完整配置步骤
- 8 个监听事件详解
- 代码实现解析
- 测试方法（Dashboard + 真实支付）
- 安全最佳实践
- 5 个常见问题排查

#### `docs/deployment/RAILWAY_DEPLOYMENT_CHECKLIST.md`
部署验证清单：
- 部署前检查（代码/环境变量）
- Railway 服务创建检查
- 12 项部署后验证（Health/RLS/迁移/静态文件/Auth0/CORS/Webhook/Celery）
- 安全检查（4 项）
- 性能检查
- 日志验证
- 端到端功能测试
- 回滚计划

#### `docs/deployment/RAILWAY_QUICK_START.md`
5 分钟快速开始：
- 最简化的部署步骤
- 复制粘贴配置模板
- 快速验证命令

---

### 3. 依赖更新

#### `backend/requirements/production.txt`
新增依赖：
- `dj-database-url==2.1.0` - 解析 Railway 的 `DATABASE_URL`
- `whitenoise==6.6.0` - 服务静态文件（替代 S3）

---

## 🎯 部署流程概览

```
1. 创建 Railway 项目
   ├── 连接 GitHub 仓库
   └── 创建 Backend Service

2. 添加数据库服务
   ├── PostgreSQL (自动注入 DATABASE_URL)
   └── Redis (自动注入 REDIS_URL)

3. 配置环境变量
   ├── Django 核心 (DJANGO_SETTINGS_MODULE, SECRET_KEY)
   ├── 域名与安全 (ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS)
   ├── Auth0 (DOMAIN, AUDIENCE, CLIENT_ID, CLIENT_SECRET)
   ├── SIWE (DOMAIN, CHAIN_ID, URI)
   ├── Stripe (MOCK_STRIPE, 测试密钥)
   ├── Fireblocks (MOCK 模式)
   ├── Email (Console 后端)
   └── 业务配置

4. 配置启动命令
   └── collectstatic + migrate + gunicorn

5. 部署并验证
   ├── Health Check (/health/, /ready/)
   ├── RLS 验证
   ├── 迁移检查
   ├── 种子数据加载
   ├── 超级用户创建
   └── Auth0 JWT 测试

6. 配置 Stripe Webhook
   ├── 创建 Endpoint
   ├── 选择监听事件
   ├── 获取 Signing Secret
   ├── 更新环境变量
   └── 测试 Webhook

7. （可选）添加 Celery
   ├── Celery Worker Service
   └── Celery Beat Service

8. 验证完整功能
   ├── 端到端订单测试
   ├── Webhook 事件处理
   ├── 代币分配
   └── 佣金计算
```

---

## 🔑 关键环境变量（最小配置）

```bash
# 核心配置
DJANGO_SETTINGS_MODULE=config.settings.railway
SECRET_KEY=<生成随机密钥>
DEBUG=False

# 域名（部署后更新）
ALLOWED_HOSTS=<Railway域名>.up.railway.app
CSRF_TRUSTED_ORIGINS=https://<Railway域名>.up.railway.app

# Auth0
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_M2M_CLIENT_ID=QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
AUTH0_M2M_CLIENT_SECRET=cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP

# SIWE
SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=8453
SIWE_URI=https://demo-api.posx.io

# Mock 模式（Demo 环境）
MOCK_STRIPE=true
FIREBLOCKS_MODE=MOCK
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# 前端
FRONTEND_URL=https://adminhq.posx.io
ALLOWED_SITE_CODES=NA,ASIA

# Celery
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
```

---

## 📋 验证清单

### 部署后必做检查

1. ✅ Health Checks
   - `/health/` 返回 200
   - `/ready/` 所有检查为 `ok`

2. ✅ RLS 验证
   - 至少 8 张表启用 RLS
   - `/ready/` 显示 `"rls": "ok"`

3. ✅ 数据库迁移
   - 所有迁移已应用 `[X]`
   - 核心迁移 `0004_enable_rls_policies` 已执行

4. ✅ 静态文件
   - `collectstatic` 成功
   - `/static/admin/css/base.css` 可访问

5. ✅ Auth0 JWT
   - 受保护端点需要 Token
   - 公开端点无需 Token

6. ✅ CORS
   - 前端域名在白名单
   - 响应头包含 `Access-Control-Allow-Origin`

7. ✅ Stripe Webhook
   - Endpoint 可访问（返回 400）
   - 测试 Webhook 发送成功
   - 日志显示接收事件

---

## 🚀 快速开始命令

### 生成 SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 测试健康检查

```bash
curl https://<Railway域名>.up.railway.app/health/
curl https://<Railway域名>.up.railway.app/ready/
```

### 初始化数据

```bash
cd backend
python manage.py migrate
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json
```

### 创建超级用户

```bash
DJANGO_SUPERUSER_PASSWORD=Demo_Admin_2024! \
python manage.py createsuperuser \
  --noinput \
  --username admin \
  --email admin@posx.io
```

---

## 🔒 安全提醒

### Demo 环境

- ✅ 使用 Mock 模式（Stripe、Fireblocks）
- ✅ Console Email Backend（不发送真实邮件）
- ✅ 测试 Auth0 Tenant
- ✅ DEBUG = False

### 生产环境切换

切换到生产时，需更新：

```bash
# Stripe 生产密钥
MOCK_STRIPE=false
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Fireblocks 生产 API
FIREBLOCKS_MODE=LIVE
ALLOW_PROD_TX=true
FIREBLOCKS_BASE_URL=https://api.fireblocks.io

# 真实 Email 服务
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=<真实用户名>
EMAIL_HOST_PASSWORD=<真实密码>

# 生产 Auth0 Tenant
AUTH0_DOMAIN=<生产域名>
AUTH0_AUDIENCE=<生产API标识>

# SIWE 主网
SIWE_CHAIN_ID=1  # 或 8453 (Base)

# Sentry 监控
SENTRY_DSN=<真实DSN>
```

---

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| [RAILWAY_QUICK_START.md](docs/deployment/RAILWAY_QUICK_START.md) | 5 分钟快速部署 |
| [RAILWAY_DEPLOYMENT_GUIDE.md](docs/deployment/RAILWAY_DEPLOYMENT_GUIDE.md) | 完整部署指南 |
| [RAILWAY_ENV_VARIABLES.md](docs/deployment/RAILWAY_ENV_VARIABLES.md) | 环境变量详解 |
| [RAILWAY_SERVICE_CONFIGURATION.md](docs/deployment/RAILWAY_SERVICE_CONFIGURATION.md) | 服务配置详解 |
| [RAILWAY_STRIPE_WEBHOOK.md](docs/deployment/RAILWAY_STRIPE_WEBHOOK.md) | Stripe Webhook 配置 |
| [RAILWAY_DEPLOYMENT_CHECKLIST.md](docs/deployment/RAILWAY_DEPLOYMENT_CHECKLIST.md) | 部署验证清单 |

---

## 🛠️ 常用命令速查

### Railway Shell 命令

```bash
# 进入 Backend Shell
cd backend

# 查看迁移状态
python manage.py showmigrations

# 执行迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 加载种子数据
python manage.py loaddata fixtures/seed_sites.json

# Django Shell
python manage.py shell

# 查看 Celery Worker
celery -A config inspect ping

# 查看定时任务
celery -A config inspect scheduled
```

### cURL 测试命令

```bash
# Health Check
curl https://<Railway域名>/health/

# Ready Check
curl https://<Railway域名>/ready/

# 测试公开端点
curl https://<Railway域名>/api/v1/test/public/

# 测试受保护端点
curl https://<Railway域名>/api/v1/test/protected/ \
  -H "Authorization: Bearer <JWT>"

# 测试 Webhook
curl -X POST https://<Railway域名>/api/v1/webhooks/stripe/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## ✅ 部署完成

所有配置文件和文档已创建完成！

**下一步**:
1. 提交所有文件到 Git
2. 推送到 GitHub
3. 在 Railway 创建项目
4. 按照 [RAILWAY_QUICK_START.md](docs/deployment/RAILWAY_QUICK_START.md) 或 [RAILWAY_DEPLOYMENT_GUIDE.md](docs/deployment/RAILWAY_DEPLOYMENT_GUIDE.md) 执行部署
5. 使用 [RAILWAY_DEPLOYMENT_CHECKLIST.md](docs/deployment/RAILWAY_DEPLOYMENT_CHECKLIST.md) 验证部署

**如遇问题**:
- 查看对应的故障排查章节
- 检查 Railway 日志
- 验证环境变量拼写和值

---

**创建时间**: 2025-01-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

