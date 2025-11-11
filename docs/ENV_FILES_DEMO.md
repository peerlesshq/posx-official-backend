# Demo 环境变量文件

## ⚠️ 安全说明

这些文件包含敏感信息，请妥善保管：
- **不要**提交到版本控制
- **不要**分享给未授权人员
- 仅在部署服务器上创建真实的 `.env.demo` 文件

---

## 文件 1: `.env.demo.example`（可提交到仓库）

创建文件：`项目根目录/.env.demo.example`

```env
# ============================================
# POSX Demo 环境配置示例
# ============================================
# 
# 使用方法：
# 1. 复制此文件为 .env.demo
# 2. 填写所有标记为 [必须填写] 的项
# 3. 执行部署脚本
# 
# ⚠️ 安全警告：
# - 不要将真实的 .env.demo 提交到版本控制
# - 真实凭据仅存在于服务器上
# 
# ============================================

# ============================================
# 环境标识
# ============================================
ENV=demo

# ============================================
# Django 核心配置
# ============================================

# [必须填写] 使用部署脚本自动生成，或手动生成：
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=GENERATE_WITH_DEPLOY_SCRIPT_OR_MANUALLY

# Demo 环境关闭 DEBUG
DEBUG=false

# Django Settings Module
DJANGO_SETTINGS_MODULE=config.settings.demo

# [必须填写] Demo 域名
ALLOWED_HOSTS=demo-api.posx.io,localhost,127.0.0.1

# ============================================
# CSRF 与 CORS 安全配置
# ============================================
# ⭐ 必须与前端域名完全一致

CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io

# ============================================
# 数据库配置
# ============================================

DB_NAME=posx_demo
DB_USER=posx_app
DB_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD
DB_HOST=db
DB_PORT=5432

# ============================================
# Redis 配置
# ============================================

REDIS_URL=redis://redis:6379/0

# ============================================
# Celery 配置
# ============================================

CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# ============================================
# Auth0 配置 ⭐
# ============================================
# ⚠️ 重要: 
# - AUTH0_AUDIENCE 的尾部斜杠必须与 Auth0 控制台完全一致
# - 仅使用 RS256 算法，拒绝 HS256
# - Clock skew 容忍度 60s

# [必须填写] Auth0 Demo Tenant
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_CLIENT_ID=YOUR_CLIENT_ID_HERE
AUTH0_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE

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
API_EXTERNAL_URL=https://demo-api.posx.io
ALLOWED_SITE_CODES=NA,ASIA

# ============================================
# Stripe 配置（Mock 模式）
# ============================================

MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# ============================================
# Gunicorn 配置（t3.micro 优化）
# ============================================

WEB_CONCURRENCY=2
THREADS=2

# ============================================
# 订单配置
# ============================================

NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7

# ============================================
# Fireblocks 配置（Mock 模式）
# ============================================

FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=false

# ============================================
# Email 配置（Console 模式）
# ============================================

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# ============================================
# 可选：Sentry 监控
# ============================================

# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
# SENTRY_ENVIRONMENT=demo
# SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## 文件 2: `.env.demo`（仅服务器，不提交）

创建文件：`项目根目录/.env.demo`

⚠️ **请手动替换以下值**：
- `SECRET_KEY`: 运行脚本时自动生成
- `DB_PASSWORD`: 运行脚本时自动生成
- `AUTH0_CLIENT_ID`: 你的真实值
- `AUTH0_CLIENT_SECRET`: 你的真实值

```env
# ============================================
# POSX Demo 环境配置（真实凭据）
# ============================================
# 
# ⚠️ 安全警告：
# - 此文件包含真实凭据，不要提交到版本控制
# - 仅存在于部署服务器上
# - 已在 .gitignore 中排除
# 
# ============================================

# ============================================
# 环境标识
# ============================================
ENV=demo

# ============================================
# Django 核心配置
# ============================================

# ⭐ 强随机密钥（运行 deploy_demo.sh 时自动生成）
SECRET_KEY=<WILL_BE_AUTO_GENERATED>

# Demo 环境关闭 DEBUG
DEBUG=false

# Django Settings Module
DJANGO_SETTINGS_MODULE=config.settings.demo

# Demo 域名
ALLOWED_HOSTS=demo-api.posx.io,localhost,127.0.0.1

# ============================================
# CSRF 与 CORS 安全配置
# ============================================

CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io

# ============================================
# 数据库配置
# ============================================

DB_NAME=posx_demo
DB_USER=posx_app
DB_PASSWORD=<WILL_BE_AUTO_GENERATED>
DB_HOST=db
DB_PORT=5432

# ============================================
# Redis 配置
# ============================================

REDIS_URL=redis://redis:6379/0

# ============================================
# Celery 配置
# ============================================

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ============================================
# Auth0 配置 ⭐
# ============================================
# ⚠️ 重要: AUTH0_AUDIENCE 的尾部斜杠必须与 Auth0 控制台完全一致

AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_CLIENT_ID=QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
AUTH0_CLIENT_SECRET=cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP

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
API_EXTERNAL_URL=https://demo-api.posx.io
ALLOWED_SITE_CODES=NA,ASIA

# ============================================
# Stripe 配置（Mock 模式）
# ============================================

MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# ============================================
# Gunicorn 配置（t3.micro 优化）
# ============================================

WEB_CONCURRENCY=2
THREADS=2

# ============================================
# 订单配置
# ============================================

NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7

# ============================================
# Fireblocks 配置（Mock 模式）
# ============================================

FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=false

# ============================================
# Email 配置（Console 模式）
# ============================================

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## 手动创建步骤

### 在本地（用于提交到仓库）

```bash
# 在项目根目录
cd posx

# 创建 .env.demo.example（复制上面的内容）
cat > .env.demo.example << 'EOF'
# [粘贴上面文件 1 的完整内容]
EOF

# 添加到 git
git add .env.demo.example
git commit -m "Add .env.demo.example for demo deployment"
git push
```

### 在服务器（部署时）

```bash
# SSH 到服务器
ssh ubuntu@18.191.15.227

cd posx

# 方式 1: 运行部署脚本（推荐，自动生成）
chmod +x scripts/deploy_demo.sh
./scripts/deploy_demo.sh

# 方式 2: 手动创建（如果脚本失败）
cat > .env.demo << 'EOF'
# [粘贴上面文件 2 的完整内容]
EOF

# 手动生成 SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 编辑 .env.demo，填写真实凭据
nano .env.demo
```

---

## 验证配置

```bash
# 检查文件存在
ls -la .env.demo*

# 检查文件权限（应该仅所有者可读写）
chmod 600 .env.demo

# 验证配置加载
docker compose -f docker-compose.demo.yml config | grep AUTH0_DOMAIN
```

---

## 故障排查

### 问题: .env.demo 不生效

```bash
# 检查文件名（必须是 .env.demo，不是 .env.demo.txt）
ls -la | grep .env

# 检查 Docker Compose 是否正确加载
docker compose -f docker-compose.demo.yml config

# 重启容器
docker compose -f docker-compose.demo.yml restart web
```

### 问题: 环境变量值被忽略

```bash
# 进入容器检查
docker compose -f docker-compose.demo.yml exec web env | grep AUTH0

# 检查是否有 .env 文件冲突
ls -la .env*
```

---

**相关文档**:
- [部署指南](./DEPLOY_DEMO.md)
- [Auth0 配置](./config/CONFIG_AUTH0.md)
- [环境变量说明](./config/CONFIG_ENV_VARIABLES.md)

