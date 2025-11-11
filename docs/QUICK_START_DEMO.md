# POSX Demo 环境 - 快速开始指南

## 🚀 5 分钟完成部署

本指南将帮助你在 5 分钟内完成 POSX Demo 环境的部署。

---

## 📋 前置条件检查清单

- [ ] AWS EC2 实例 (Ubuntu 22.04, 18.191.15.227)
- [ ] 安全组已开放端口 22/80/443
- [ ] DNS 已配置 (demo-api.posx.io → 18.191.15.227, 灰色云朵)
- [ ] 准备好 Auth0 凭据 (Client ID, Client Secret)
- [ ] SSH 密钥已配置

---

## 🎯 三种部署方式

### 方式一：一键 SSH 部署（最快）⭐

在**本地**执行以下命令（将自动 SSH 到服务器并执行部署）：

```bash
# 替换为你的 SSH 密钥路径
ssh -i ~/.ssh/your-key.pem ubuntu@18.191.15.227 << 'ENDSSH'
# 克隆项目
cd ~
if [ ! -d "posx" ]; then
    git clone https://github.com/your-org/posx.git
fi

cd posx

# 拉取最新代码
git pull

# 手动创建 .env.demo（包含真实凭据）
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

# 执行部署脚本
chmod +x scripts/deploy_demo.sh
./scripts/deploy_demo.sh --seed=minimal

ENDSSH
```

### 方式二：手动 SSH + 运行脚本（推荐）

```bash
# 1. SSH 到服务器
ssh ubuntu@18.191.15.227

# 2. 克隆项目（如果尚未克隆）
git clone https://github.com/your-org/posx.git
cd posx

# 或更新现有代码
cd posx && git pull

# 3. 执行部署脚本（会自动生成 .env.demo 并提示填写）
chmod +x scripts/deploy_demo.sh
./scripts/deploy_demo.sh

# 脚本会暂停并提示你编辑 .env.demo
# 填写 AUTH0_CLIENT_ID 和 AUTH0_CLIENT_SECRET 后保存退出

# 4. 脚本自动完成剩余步骤
# - 安装 Docker
# - 启动容器
# - 执行迁移
# - 加载种子数据
# - 创建超级用户
# - 健康检查
```

### 方式三：完全手动部署（备用）

参考详细文档：[DEPLOY_DEMO.md](./DEPLOY_DEMO.md#手动部署)

---

## ⚡ 部署后验证

### 1. 快速健康检查

```bash
# 本地检查（在服务器上执行）
curl http://localhost/ready/

# 远程检查（在本地执行）
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

### 2. 检查容器状态

```bash
docker compose -f docker-compose.demo.yml ps

# 期望所有服务都是 "healthy" 或 "running"
```

### 3. 查看日志

```bash
# 查看 web 服务日志
docker compose -f docker-compose.demo.yml logs -f web

# 查看 caddy 日志（SSL 证书签发）
docker compose -f docker-compose.demo.yml logs caddy | grep certificate
```

---

## 🔑 默认凭据

部署完成后，使用以下凭据访问：

### Django Admin
- **URL**: https://demo-api.posx.io/admin/
- **用户名**: `admin`
- **密码**: `Demo_Admin_2024!`

### API 访问
- **Base URL**: https://demo-api.posx.io/api/v1/
- **认证**: Auth0 JWT (Bearer Token)
- **Required Headers**:
  ```
  Authorization: Bearer <your_jwt_token>
  X-Site-Code: NA
  ```

### Auth0
- **Domain**: dev-posx.us.auth0.com
- **Audience**: https://demo-api.posx.io/api/v1/ ⭐（带尾斜杠）
- **Client ID**: QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK

---

## 🎨 Retool 快速配置

### 1. 添加 Auth0 Resource

**Settings → Resources → Add Resource → Auth0**

```
Name: POSX Demo Auth0
Auth0 Domain: dev-posx.us.auth0.com
Client ID: QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
Client Secret: cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP
Audience: https://demo-api.posx.io/api/v1/
Scopes: openid profile email
```

### 2. 添加 REST API Resource

**Settings → Resources → Add Resource → REST API**

```
Name: POSX Demo API
Base URL: https://demo-api.posx.io/api/v1/
Authentication: POSX Demo Auth0 (上面创建的)
```

### 3. 添加默认 Headers

在 **Headers** 标签页：

```
X-Site-Code: NA
```

### 4. 测试查询

创建新查询：

```javascript
// Query1 - Get Tiers
{
  "method": "GET",
  "url": "tiers/",
  "headers": {
    "X-Site-Code": "NA"
  }
}
```

点击 **Run** 应返回 tiers 列表。

---

## 📊 常用管理命令

### 查看容器状态

```bash
docker compose -f docker-compose.demo.yml ps
```

### 重启服务

```bash
# 重启单个服务
docker compose -f docker-compose.demo.yml restart web

# 重启所有服务
docker compose -f docker-compose.demo.yml restart
```

### 查看日志

```bash
# 实时日志（所有服务）
docker compose -f docker-compose.demo.yml logs -f

# 单个服务日志
docker compose -f docker-compose.demo.yml logs -f web
docker compose -f docker-compose.demo.yml logs -f caddy
docker compose -f docker-compose.demo.yml logs -f worker
```

### 进入容器

```bash
# 进入 web 容器
docker compose -f docker-compose.demo.yml exec web bash

# 运行 Django 命令
docker compose -f docker-compose.demo.yml exec web python manage.py shell
```

### 数据库操作

```bash
# 连接数据库
docker compose -f docker-compose.demo.yml exec db psql -U posx_app -d posx_demo

# 备份数据库
docker compose -f docker-compose.demo.yml exec db pg_dump -U posx_app -d posx_demo > backup.sql

# 恢复数据库
docker compose -f docker-compose.demo.yml exec -T db psql -U posx_app -d posx_demo < backup.sql
```

---

## 🐛 常见问题速查

### 问题 1: 401 Unauthorized

**解决方案**:
1. 检查 Audience 是否带尾斜杠：`https://demo-api.posx.io/api/v1/`
2. 在 Retool 中重新登录获取新 token
3. 确认 token 中的 `aud` 字段与后端配置一致

### 问题 2: CORS 错误

**解决方案**:
1. 检查请求的 Origin 是否在白名单中
2. 重启 caddy: `docker compose -f docker-compose.demo.yml restart caddy`
3. 查看 caddy 日志确认 CORS 头

### 问题 3: SSL 证书未签发

**解决方案**:
1. 确认 DNS 解析正确：`dig +short demo-api.posx.io`
2. 确认 Cloudflare 使用灰色云朵（非代理模式）
3. 等待 5-10 分钟让 Let's Encrypt 验证域名
4. 查看 caddy 日志：`docker compose -f docker-compose.demo.yml logs caddy | grep certificate`

### 问题 4: 容器启动失败

**解决方案**:
1. 查看具体日志：`docker compose -f docker-compose.demo.yml logs [service]`
2. 检查 .env.demo 是否存在且正确
3. 完全重建：`docker compose -f docker-compose.demo.yml down && docker compose -f docker-compose.demo.yml up -d --build`

---

## 📚 更多资源

- **详细部署文档**: [DEPLOY_DEMO.md](./DEPLOY_DEMO.md)
- **环境变量说明**: [ENV_FILES_DEMO.md](./ENV_FILES_DEMO.md)
- **Auth0 配置**: [config/CONFIG_AUTH0.md](./config/CONFIG_AUTH0.md)
- **Retool 指南**: [retool/RETOOL_QUICK_START.md](./retool/RETOOL_QUICK_START.md)
- **故障排查**: [DEPLOY_DEMO.md#常见问题排查](./DEPLOY_DEMO.md#常见问题排查)

---

## 🔒 安全提醒

部署完成后，请立即执行以下安全措施：

```bash
# 1. 限制 SSH 访问（替换为你的 IP）
sudo ufw allow from YOUR_IP to any port 22
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 2. 修改默认超级用户密码
docker compose -f docker-compose.demo.yml exec web python manage.py changepassword admin

# 3. 设置自动备份（cron）
crontab -e
# 添加：0 2 * * * cd ~/posx && docker compose -f docker-compose.demo.yml exec -T db pg_dump -U posx_app -d posx_demo | gzip > ~/backups/posx-$(date +\%Y\%m\%d).sql.gz
```

---

## 🎉 完成！

恭喜！你的 POSX Demo 环境已成功部署。

**访问地址**:
- API: https://demo-api.posx.io/api/v1/
- Admin: https://demo-api.posx.io/admin/
- 健康检查: https://demo-api.posx.io/ready/

**下一步**:
1. 在 Retool 中配置 API 连接
2. 测试关键 API 端点
3. 配置监控和告警
4. 设置自动备份

---

**最后更新**: 2024-11-11  
**维护者**: POSX DevOps Team

