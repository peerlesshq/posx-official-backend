# POSX Demo 环境部署指南

## 📋 目录

- [前置条件](#前置条件)
- [快速部署](#快速部署)
- [手动部署](#手动部署)
- [验证检查](#验证检查)
- [常见问题排查](#常见问题排查)
- [日志查看](#日志查看)
- [Retool 对接](#retool-对接)
- [回滚与清理](#回滚与清理)
- [备份策略](#备份策略)

---

## 前置条件

### 1. AWS EC2 实例

- **系统**: Ubuntu 22.04 LTS
- **实例类型**: t3.micro 或更高（建议 t3.small）
- **存储**: 30 GiB gp3（建议，最低 20 GiB）
- **公网 IP**: 18.191.15.227（示例）

### 2. 安全组配置

**入站规则**:
- SSH (22): 限制到你的固定 IP（部署时可临时全开，部署后限制）
- HTTP (80): 0.0.0.0/0（Let's Encrypt 验证需要）
- HTTPS (443): 0.0.0.0/0

```bash
# AWS Console 或 CLI 配置
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp --port 22 --cidr YOUR_IP/32

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
```

### 3. DNS 配置

在 Cloudflare（或其他 DNS 提供商）配置：

```
类型: A
名称: demo-api
内容: 18.191.15.227
TTL: Auto
代理状态: 仅 DNS（灰色云朵）⭐
```

**⚠️ 重要**: 必须使用 **灰色云朵**（关闭 Cloudflare 代理），否则 Let's Encrypt 证书签发会失败。

**验证 DNS**:
```bash
dig +short demo-api.posx.io
# 应返回: 18.191.15.227

nslookup demo-api.posx.io
# 应显示正确的 IP
```

### 4. Auth0 配置

在 Auth0 Dashboard 中配置 Demo API：

1. **创建 API**（如果不存在）:
   - Name: `POSX API (Demo)`
   - Identifier: `https://demo-api.posx.io/api/v1/`（⭐ 带尾斜杠）
   - Signing Algorithm: `RS256`

2. **配置应用程序**:
   - Allowed Callback URLs: `https://adminhq.posx.io/callback`
   - Allowed Logout URLs: `https://adminhq.posx.io`
   - Allowed Web Origins: `https://adminhq.posx.io, https://posx.retool.com`

3. **记录凭据**:
   - Domain: `dev-posx.us.auth0.com`
   - Client ID: `QymLI...`
   - Client Secret: `cRiS6...`

---

## 快速部署

### 方式一：一键脚本（推荐）

```bash
# 1. SSH 到服务器
ssh ubuntu@18.191.15.227

# 2. 克隆项目（如果尚未克隆）
git clone https://github.com/your-org/posx.git
cd posx

# 3. 执行部署脚本
chmod +x scripts/deploy_demo.sh
./scripts/deploy_demo.sh

# 默认加载最小化种子数据（sites + commission_plans）
# 其他选项：
# ./scripts/deploy_demo.sh --seed=none   # 不加载数据
# ./scripts/deploy_demo.sh --seed=full   # 加载全量测试数据
```

### 方式二：本地触发远程部署

```bash
# 在本地执行（需要配置 SSH 密钥）
ssh -i ~/.ssh/your-key.pem ubuntu@18.191.15.227 'bash -s' < scripts/deploy_demo.sh
```

---

## 手动部署

如果自动脚本失败，可手动执行以下步骤：

### 1. 安装 Docker

```bash
# 更新软件包
sudo apt-get update
sudo apt-get upgrade -y

# 安装依赖
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 将当前用户加入 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

### 2. 准备配置文件

```bash
cd posx

# 复制环境变量示例
cp .env.demo.example .env.demo

# 生成 SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 编辑 .env.demo
nano .env.demo
```

**必须填写的项**:
- `SECRET_KEY`: 上面生成的值
- `DB_PASSWORD`: 强密码（建议 32+ 字符）
- `AUTH0_CLIENT_ID`: 从 Auth0 获取
- `AUTH0_CLIENT_SECRET`: 从 Auth0 获取

### 3. 启动容器

```bash
# 启动所有服务
docker compose -f docker-compose.demo.yml up -d --build

# 查看容器状态
docker compose -f docker-compose.demo.yml ps

# 查看日志
docker compose -f docker-compose.demo.yml logs -f
```

### 4. 初始化数据库

```bash
# 执行迁移
docker compose -f docker-compose.demo.yml exec web python manage.py migrate

# 加载种子数据
docker compose -f docker-compose.demo.yml exec web python manage.py loaddata \
    fixtures/seed_sites.json \
    fixtures/seed_commission_plans.json

# 创建超级用户
docker compose -f docker-compose.demo.yml exec web python manage.py createsuperuser
```

---

## 验证检查

### 1. 健康检查

```bash
# 本地检查
curl http://localhost/ready/

# 远程检查（DNS 生效后）
curl https://demo-api.posx.io/ready/

# 期望输出:
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "migrations": "ok",
    "rls": "ok"
  },
  "timestamp": "2024-..."
}
```

### 2. SSL 证书检查

```bash
# 检查证书
openssl s_client -connect demo-api.posx.io:443 -servername demo-api.posx.io < /dev/null

# 检查到期时间
echo | openssl s_client -servername demo-api.posx.io -connect demo-api.posx.io:443 2>/dev/null | openssl x509 -noout -dates
```

### 3. Auth0 JWT 测试

```bash
# 获取 Auth0 Token（需要先在前端登录）
TOKEN="your_jwt_token"

# 测试受保护端点
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Site-Code: NA" \
     https://demo-api.posx.io/api/v1/tiers/

# 期望: 返回 tiers 列表（200）
```

### 4. CORS 测试

```bash
# 预检请求测试
curl -X OPTIONS https://demo-api.posx.io/api/v1/tiers/ \
     -H "Origin: https://posx.retool.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization" \
     -v

# 期望看到:
# Access-Control-Allow-Origin: https://posx.retool.com
# Access-Control-Allow-Methods: GET, POST, ...
```

---

## 常见问题排查

### 问题 1: 401 Unauthorized - "Invalid token"

**可能原因**:
1. Audience 尾斜杠不一致
2. Token 使用了错误的 Audience
3. Issuer 配置错误

**排查步骤**:

```bash
# 1. 检查 .env.demo 配置
grep AUTH0_AUDIENCE .env.demo
# 必须是: https://demo-api.posx.io/api/v1/ （带 /）

grep AUTH0_ISSUER .env.demo
# 必须是: https://dev-posx.us.auth0.com/ （带 /）

# 2. 解码 JWT Token（在线工具 jwt.io 或命令行）
echo $TOKEN | cut -d. -f2 | base64 -d | jq .

# 检查 token 中的 aud 字段是否为: https://demo-api.posx.io/api/v1/
```

**解决方案**:
- 确保 Auth0 API Identifier、.env.demo 中的 `AUTH0_AUDIENCE`、以及前端/Retool 获取 token 时使用的 audience **完全一致**（包括尾斜杠）
- 在 Retool 中重新获取 token（使用正确的 audience）

### 问题 2: CORS 错误

**症状**:
```
Access to XMLHttpRequest at 'https://demo-api.posx.io/api/v1/...' from origin 'https://posx.retool.com' has been blocked by CORS policy
```

**排查步骤**:

```bash
# 1. 检查 Caddy 日志
docker compose -f docker-compose.demo.yml logs caddy | grep CORS

# 2. 检查 Django CORS 配置
docker compose -f docker-compose.demo.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.CORS_ALLOWED_ORIGINS)
['https://posx.retool.com', 'https://adminhq.posx.io']
```

**解决方案**:
- 确保请求的 `Origin` 头在白名单中
- 检查 `Caddyfile` 中的正则表达式是否正确
- 重启 caddy 容器: `docker compose -f docker-compose.demo.yml restart caddy`

### 问题 3: SSL 证书签发失败

**症状**:
```
curl: (60) SSL certificate problem: unable to get local issuer certificate
```

**排查步骤**:

```bash
# 1. 检查 DNS
dig +short demo-api.posx.io
# 必须返回正确的 IP

# 2. 检查端口 80 是否开放（Let's Encrypt 验证需要）
curl http://demo-api.posx.io/.well-known/acme-challenge/test

# 3. 检查 Cloudflare 设置
# 必须是灰色云朵（关闭代理）

# 4. 查看 Caddy 日志
docker compose -f docker-compose.demo.yml logs caddy | grep certificate
```

**解决方案**:
- 确保 DNS 使用灰色云朵（不通过 Cloudflare 代理）
- 等待 DNS 传播完成（可能需要几分钟）
- 重启 caddy: `docker compose -f docker-compose.demo.yml restart caddy`
- 手动触发证书签发: `docker compose -f docker-compose.demo.yml exec caddy caddy reload --config /etc/caddy/Caddyfile`

### 问题 4: 容器无法启动

**症状**:
```
docker compose ps
# 显示某个服务 Exit 1 或 unhealthy
```

**排查步骤**:

```bash
# 1. 查看具体服务日志
docker compose -f docker-compose.demo.yml logs web
docker compose -f docker-compose.demo.yml logs db

# 2. 检查健康检查
docker inspect posx_demo_web | jq '.[0].State.Health'

# 3. 检查依赖服务
docker compose -f docker-compose.demo.yml ps db redis
```

**常见原因**:
- 数据库密码不匹配
- 依赖服务未就绪
- 迁移失败

**解决方案**:
```bash
# 重启单个服务
docker compose -f docker-compose.demo.yml restart web

# 完全重建
docker compose -f docker-compose.demo.yml down
docker compose -f docker-compose.demo.yml up -d --build
```

### 问题 5: 数据库连接失败

**症状**:
```
django.db.utils.OperationalError: could not connect to server
```

**排查步骤**:

```bash
# 1. 检查 DB 容器状态
docker compose -f docker-compose.demo.yml ps db

# 2. 测试数据库连接
docker compose -f docker-compose.demo.yml exec db psql -U posx_app -d posx_demo -c "SELECT 1;"

# 3. 检查环境变量
docker compose -f docker-compose.demo.yml exec web env | grep DB_
```

**解决方案**:
- 确保 `DB_PASSWORD` 在 .env.demo 中正确设置
- 等待 db 服务健康检查通过
- 检查网络连接: `docker network ls`

---

## 日志查看

### 实时日志

```bash
# 所有服务
docker compose -f docker-compose.demo.yml logs -f

# 单个服务
docker compose -f docker-compose.demo.yml logs -f web
docker compose -f docker-compose.demo.yml logs -f caddy
docker compose -f docker-compose.demo.yml logs -f worker

# 最近 100 行
docker compose -f docker-compose.demo.yml logs --tail=100 web
```

### 应用日志

```bash
# Django 应用日志（JSON 格式）
docker compose -f docker-compose.demo.yml exec web cat /var/log/posx/django.log | jq .

# Gunicorn 访问日志（已输出到 stdout）
docker compose -f docker-compose.demo.yml logs web | grep "GET\|POST"
```

### Caddy 日志

```bash
# Caddy 访问日志（JSON 格式）
docker compose -f docker-compose.demo.yml logs caddy | jq .

# 过滤特定路径
docker compose -f docker-compose.demo.yml logs caddy | jq 'select(.request.uri | contains("/api/v1/"))'
```

---

## Retool 对接

### 1. 配置 Auth0 Resource

在 Retool 中添加 Auth0 认证资源：

- **Auth0 Domain**: `dev-posx.us.auth0.com`
- **Client ID**: `QymLI...`（从 Auth0 获取）
- **Client Secret**: `cRiS6...`（从 Auth0 获取）
- **Audience**: `https://demo-api.posx.io/api/v1/` ⭐（带尾斜杠）
- **Scope**: `openid profile email`

### 2. 配置 REST API Resource

- **Base URL**: `https://demo-api.posx.io/api/v1/`
- **Authentication**: 选择上面配置的 Auth0 资源
- **Headers**:
  ```
  X-Site-Code: NA
  ```

### 3. 测试连接

创建测试查询：

```javascript
// GET /api/v1/tiers/
{
  "method": "GET",
  "url": "{{ baseUrl }}tiers/",
  "headers": {
    "Authorization": "Bearer {{ auth0Token }}",
    "X-Site-Code": "NA"
  }
}
```

### 4. 常见问题

**401 错误**:
- 检查 Audience 是否带尾斜杠
- 重新登录获取新 token
- 检查 token 是否过期（默认 24 小时）

**CORS 错误**:
- 确保 `posx.retool.com` 在 CORS 白名单中
- 检查 Retool 使用的确切域名（可能是 `*.retool.com`）

---

## 回滚与清理

### 停止服务（保留数据）

```bash
docker compose -f docker-compose.demo.yml down
```

### 完全清理（删除所有数据）⚠️

```bash
# 停止并删除容器和卷
docker compose -f docker-compose.demo.yml down -v

# 删除镜像
docker compose -f docker-compose.demo.yml down --rmi all

# 清理未使用的资源
docker system prune -a
```

### 回滚到特定版本

```bash
# 拉取特定版本
git fetch
git checkout v1.0.0

# 重新构建
docker compose -f docker-compose.demo.yml up -d --build
```

---

## 备份策略

### 数据库备份

```bash
# 手动备份
docker compose -f docker-compose.demo.yml exec db pg_dump \
    -U posx_app \
    -d posx_demo \
    -F c \
    > backup-$(date +%Y%m%d-%H%M%S).dump

# 恢复备份
docker compose -f docker-compose.demo.yml exec -T db pg_restore \
    -U posx_app \
    -d posx_demo \
    -c \
    < backup-20240101-120000.dump
```

### 自动备份脚本

创建 cron 任务：

```bash
# 编辑 crontab
crontab -e

# 添加每日备份（凌晨 2 点）
0 2 * * * cd /home/ubuntu/posx && docker compose -f docker-compose.demo.yml exec -T db pg_dump -U posx_app -d posx_demo | gzip > /home/ubuntu/backups/posx-demo-$(date +\%Y\%m\%d).sql.gz

# 保留最近 7 天的备份
0 3 * * * find /home/ubuntu/backups -name "posx-demo-*.sql.gz" -mtime +7 -delete
```

### EBS 快照

```bash
# AWS CLI 创建快照
aws ec2 create-snapshot \
    --volume-id vol-xxxxx \
    --description "POSX Demo backup $(date +%Y-%m-%d)"

# 设置自动快照策略（Data Lifecycle Manager）
aws dlm create-lifecycle-policy \
    --execution-role-arn arn:aws:iam::xxx:role/DLM \
    --description "Daily POSX Demo snapshots" \
    --state ENABLED \
    --policy-details file://snapshot-policy.json
```

---

## 安全最佳实践

### 1. 限制 SSH 访问

```bash
# 只允许特定 IP 访问 SSH
sudo ufw allow from YOUR_IP to any port 22
sudo ufw enable
```

### 2. 定期更新

```bash
# 更新系统包
sudo apt-get update && sudo apt-get upgrade -y

# 更新 Docker 镜像
docker compose -f docker-compose.demo.yml pull
docker compose -f docker-compose.demo.yml up -d --build
```

### 3. 监控

建议设置：
- CloudWatch 监控（CPU, 内存, 磁盘）
- 日志聚合（CloudWatch Logs 或 ELK）
- 告警规则（磁盘使用率 > 80%，服务不健康等）

---

## 支持与反馈

- **文档问题**: 提交 Issue 到 GitHub
- **部署问题**: 查看 `docker compose logs` 或联系团队
- **Auth0 配置**: 参考 `docs/config/CONFIG_AUTH0.md`

---

**最后更新**: 2024-11-11
**维护者**: POSX DevOps Team

