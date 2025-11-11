# POSX Demo 环境部署 - 完成总结

## ✅ 已生成的文件

### 1. 核心配置文件

#### `docker-compose.demo.yml`（项目根目录）
- ✅ 所有服务配置 healthcheck
- ✅ 使用 `depends_on: service_healthy` 确保启动顺序
- ✅ `restart: unless-stopped` 自动重启
- ✅ Gunicorn 并发优化（workers=2, threads=2）
- ✅ 服务：db, redis, web, worker, beat, caddy

#### `Caddyfile`（项目根目录）
- ✅ 自动 HTTPS（Let's Encrypt）
- ✅ CORS 正则匹配多域名
- ✅ JSON 日志输出
- ✅ 反向代理到 web:8000
- ✅ 健康检查支持

### 2. 环境变量文件（需手动创建）

由于 `.env` 文件被 gitignore，你需要手动创建：

#### `.env.demo.example`（可提交到仓库）
- 📄 占位符配置
- 📄 不包含敏感信息
- 📄 参考：`docs/ENV_FILES_DEMO.md`

#### `.env.demo`（仅服务器，不提交）
- 🔒 包含真实 Auth0 凭据
- 🔒 自动生成的 SECRET_KEY 和 DB_PASSWORD
- 🔒 参考：`docs/ENV_FILES_DEMO.md`

**创建方法**：
```bash
# 在服务器上执行部署脚本，会自动生成
./scripts/deploy_demo.sh

# 或手动创建（参考 docs/ENV_FILES_DEMO.md）
```

### 3. 后端配置增强

#### `backend/config/settings/demo.py`
- ✅ 反向代理头配置（USE_X_FORWARDED_HOST, USE_X_FORWARDED_PORT）
- ✅ Auth0 严格校验（RS256 only, JWT_LEEWAY=60s）
- ✅ HSTS 保守配置（不含子域）
- ✅ CORS 后端白名单（Retool + AdminHQ）

### 4. 部署脚本

#### `scripts/deploy_demo.sh`
- ✅ 一键部署脚本
- ✅ 自动检测 Ubuntu 22.04
- ✅ 自动安装 Docker & Docker Compose
- ✅ 自动生成 .env.demo（SECRET_KEY, DB_PASSWORD）
- ✅ DNS 检查
- ✅ 容器启动与健康检查
- ✅ 数据库迁移
- ✅ 种子数据加载（--seed=minimal|none|full）
- ✅ 非交互超级用户创建
- ✅ 彩色输出与错误处理
- ✅ 安全提醒

### 5. 文档

#### `docs/DEPLOY_DEMO.md`（详细部署指南）
- ✅ 前置条件检查
- ✅ 快速部署与手动部署
- ✅ 验证检查步骤
- ✅ 常见问题排查（401/403, CORS, SSL, 容器启动）
- ✅ 日志查看命令
- ✅ Retool 对接指南
- ✅ 回滚与清理
- ✅ 备份策略

#### `docs/QUICK_START_DEMO.md`（5 分钟快速开始）
- ✅ 三种部署方式
- ✅ 一键 SSH 命令模板
- ✅ 默认凭据说明
- ✅ Retool 快速配置
- ✅ 常用管理命令
- ✅ 常见问题速查

#### `docs/ENV_FILES_DEMO.md`（环境变量详解）
- ✅ .env.demo.example 完整内容
- ✅ .env.demo 完整内容（含真实凭据）
- ✅ 手动创建步骤
- ✅ 验证与故障排查

---

## 📦 完整文件树

```
posx/
├── docker-compose.demo.yml          # ✅ 新建
├── Caddyfile                        # ✅ 新建
├── .env.demo.example                # 📄 需手动创建（参考 docs/ENV_FILES_DEMO.md）
├── .env.demo                        # 🔒 部署时自动生成或手动创建
├── DEPLOY_DEMO_SUMMARY.md           # ✅ 新建（本文件）
│
├── backend/
│   ├── config/
│   │   └── settings/
│   │       └── demo.py              # ✅ 已增强
│   ├── Dockerfile.prod              # ✅ 已存在
│   └── fixtures/                    # ✅ 已存在
│       ├── seed_sites.json
│       └── seed_commission_plans.json
│
├── scripts/
│   └── deploy_demo.sh               # ✅ 新建（一键部署脚本）
│
└── docs/
    ├── DEPLOY_DEMO.md               # ✅ 新建（详细指南）
    ├── QUICK_START_DEMO.md          # ✅ 新建（快速开始）
    └── ENV_FILES_DEMO.md            # ✅ 新建（环境变量详解）
```

---

## 🚀 立即开始部署

### 选项 1: 一键 SSH 命令（最快）⭐

在**本地**终端执行（会自动 SSH 到服务器并完成所有步骤）：

```bash
ssh ubuntu@18.191.15.227 << 'ENDSSH'
cd ~
[ ! -d "posx" ] && git clone https://github.com/your-org/posx.git
cd posx
git pull

# 创建 .env.demo（包含真实凭据）
cat > .env.demo << 'EOF'
ENV=demo
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.demo

ALLOWED_HOSTS=demo-api.posx.io,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io

DB_NAME=posx_demo
DB_USER=posx_app
DB_PASSWORD=$(python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(32)))")
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_CLIENT_ID=QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
AUTH0_CLIENT_SECRET=cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP

SIWE_DOMAIN=posx.io
SIWE_CHAIN_ID=8453
SIWE_URI=https://demo-api.posx.io

FRONTEND_URL=https://adminhq.posx.io
API_EXTERNAL_URL=https://demo-api.posx.io
ALLOWED_SITE_CODES=NA,ASIA

MOCK_STRIPE=true
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

WEB_CONCURRENCY=2
THREADS=2

NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7

FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=false

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOF

chmod +x scripts/deploy_demo.sh
./scripts/deploy_demo.sh --seed=minimal
ENDSSH
```

### 选项 2: 手动 SSH + 脚本（推荐新手）

```bash
# 1. SSH 到服务器
ssh ubuntu@18.191.15.227

# 2. 进入项目目录
cd posx  # 或先克隆: git clone <repo> && cd posx

# 3. 运行部署脚本（会提示你编辑 .env.demo）
chmod +x scripts/deploy_demo.sh
./scripts/deploy_demo.sh
```

### 选项 3: 完全手动部署

参考详细文档：[docs/DEPLOY_DEMO.md](docs/DEPLOY_DEMO.md)

---

## 🔍 部署后验证

### 1. 健康检查

```bash
# 在服务器上
curl http://localhost/ready/

# 在本地（DNS 生效后）
curl https://demo-api.posx.io/ready/

# 期望输出：
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

### 2. 容器状态

```bash
docker compose -f docker-compose.demo.yml ps

# 期望：所有服务都是 healthy 或 running
```

### 3. SSL 证书

```bash
# 检查证书（可能需要等待 5-10 分钟签发）
curl -I https://demo-api.posx.io

# 应看到：HTTP/2 200 或 301
```

---

## 🔑 默认凭据

### Django Admin
- **URL**: https://demo-api.posx.io/admin/
- **用户名**: `admin`
- **密码**: `Demo_Admin_2024!`

### Auth0
- **Domain**: dev-posx.us.auth0.com
- **Audience**: `https://demo-api.posx.io/api/v1/` ⭐（**必须带尾斜杠**）
- **Client ID**: QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK

### API
- **Base URL**: `https://demo-api.posx.io/api/v1/`
- **认证**: Bearer Token (Auth0 JWT)
- **Required Headers**: `X-Site-Code: NA`

---

## 📊 常用命令速查

```bash
# 查看容器状态
docker compose -f docker-compose.demo.yml ps

# 查看日志
docker compose -f docker-compose.demo.yml logs -f web

# 重启服务
docker compose -f docker-compose.demo.yml restart web

# 执行迁移
docker compose -f docker-compose.demo.yml exec web python manage.py migrate

# 进入 Django shell
docker compose -f docker-compose.demo.yml exec web python manage.py shell

# 备份数据库
docker compose -f docker-compose.demo.yml exec db pg_dump -U posx_app -d posx_demo > backup.sql

# 停止所有服务
docker compose -f docker-compose.demo.yml down
```

---

## ⚠️ 常见问题速查

### 问题 1: 401 Unauthorized

**原因**: Audience 不一致  
**解决**: 
1. 确保 Auth0 API Identifier、.env.demo、Retool 都使用 `https://demo-api.posx.io/api/v1/`（带 /）
2. 重新获取 token

### 问题 2: CORS 错误

**原因**: Origin 不在白名单  
**解决**: 
1. 检查 `Caddyfile` 正则表达式
2. 重启 caddy: `docker compose -f docker-compose.demo.yml restart caddy`

### 问题 3: SSL 证书未签发

**原因**: DNS 未生效或 Cloudflare 代理开启  
**解决**:
1. 确认 DNS 解析正确: `dig +short demo-api.posx.io`
2. 确认 Cloudflare 使用灰色云朵（关闭代理）
3. 等待 5-10 分钟

### 问题 4: 容器启动失败

**原因**: 配置错误或依赖未就绪  
**解决**:
1. 查看日志: `docker compose -f docker-compose.demo.yml logs [service]`
2. 检查 .env.demo 是否正确
3. 完全重建: `docker compose -f docker-compose.demo.yml down && docker compose -f docker-compose.demo.yml up -d --build`

**详细排查**: 参考 [docs/DEPLOY_DEMO.md#常见问题排查](docs/DEPLOY_DEMO.md#常见问题排查)

---

## 🔒 安全检查清单

部署完成后，请执行以下安全措施：

- [ ] 限制 SSH 访问到固定 IP: `sudo ufw allow from YOUR_IP to any port 22`
- [ ] 修改默认超级用户密码: `docker compose -f docker-compose.demo.yml exec web python manage.py changepassword admin`
- [ ] 设置自动备份（cron）
- [ ] 配置监控告警（CloudWatch 或 Sentry）
- [ ] 定期更新系统包: `sudo apt-get update && sudo apt-get upgrade`
- [ ] 检查日志异常: `docker compose -f docker-compose.demo.yml logs | grep ERROR`

---

## 📚 相关文档

### 核心文档
- **快速开始**: [docs/QUICK_START_DEMO.md](docs/QUICK_START_DEMO.md)
- **详细部署**: [docs/DEPLOY_DEMO.md](docs/DEPLOY_DEMO.md)
- **环境变量**: [docs/ENV_FILES_DEMO.md](docs/ENV_FILES_DEMO.md)

### 配置文档
- **Auth0 配置**: [docs/config/CONFIG_AUTH0.md](docs/config/CONFIG_AUTH0.md)
- **环境变量说明**: [docs/config/CONFIG_ENV_VARIABLES.md](docs/config/CONFIG_ENV_VARIABLES.md)

### Retool 集成
- **Retool 快速开始**: [docs/retool/RETOOL_QUICK_START.md](docs/retool/RETOOL_QUICK_START.md)
- **Retool 连接指南**: [docs/retool/RETOOL_CONNECTION_GUIDE.md](docs/retool/RETOOL_CONNECTION_GUIDE.md)

---

## 🎉 完成！

**恭喜！** 你已经成功完成 POSX Demo 环境的部署准备。

**下一步**:
1. 选择一种部署方式（推荐选项 1）
2. 执行部署命令
3. 验证健康检查
4. 在 Retool 中配置 API 连接
5. 开始测试和开发

**访问地址**:
- 🌐 API: https://demo-api.posx.io/api/v1/
- 🔧 Admin: https://demo-api.posx.io/admin/
- ✅ Health: https://demo-api.posx.io/ready/

**如遇问题**:
- 查看详细文档: [docs/DEPLOY_DEMO.md](docs/DEPLOY_DEMO.md)
- 查看日志: `docker compose -f docker-compose.demo.yml logs`
- 联系团队支持

---

**创建时间**: 2024-11-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

