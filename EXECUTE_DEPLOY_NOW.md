# 🚀 立即执行部署 - 完整指令

## 📋 执行前检查

- [x] 代码已提交到 GitHub
- [ ] DNS 已配置（demo-api.posx.io → 18.191.15.227）
- [ ] AWS 安全组已开放端口 22/80/443
- [ ] SSH 密钥已配置

---

## 步骤 1：提交 .env.demo.example 到仓库（在本地执行）

由于 `.env` 文件被 gitignore，请手动创建并提交示例文件：

```powershell
# 在 PowerShell 中执行
cd E:\300_Code\314_POSX_Official_Sale_App

# 创建 .env.demo.example
@"
# POSX Demo 环境配置示例
ENV=demo
SECRET_KEY=GENERATE_WITH_DEPLOY_SCRIPT_OR_MANUALLY
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.demo

ALLOWED_HOSTS=demo-api.posx.io,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io

DB_NAME=posx_demo
DB_USER=posx_app
DB_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=`${REDIS_URL}
CELERY_RESULT_BACKEND=`${REDIS_URL}

AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=https://demo-api.posx.io/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_CLIENT_ID=YOUR_CLIENT_ID_HERE
AUTH0_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE

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
"@ | Out-File -FilePath .env.demo.example -Encoding UTF8

# 提交
git add .env.demo.example deploy_demo_oneclick.sh verify_demo_deployment.sh EXECUTE_DEPLOY_NOW.md
git commit -m "Add demo deployment scripts and example env file"
git push origin main
```

---

## 步骤 2：一键部署（在本地执行 SSH 命令）

**⚠️ 重要：请将下面命令中的仓库地址替换为你的真实地址！**

### 方式 A：使用 Git Bash（推荐）

```bash
# 在 Git Bash 中执行
ssh ubuntu@18.191.15.227 << 'ENDSSH'
set -e

echo "=========================================="
echo "🚀 POSX Demo 环境一键部署"
echo "=========================================="

cd ~

# 克隆或更新项目（⚠️ 替换为你的仓库地址）
if [ ! -d "posx" ]; then
    echo "[1/8] 克隆项目..."
    git clone https://github.com/your-org/posx.git
    cd posx
else
    echo "[1/8] 更新项目..."
    cd posx
    git pull origin main
fi

echo "[2/8] 生成 .env.demo（包含真实凭据）..."

# 生成密钥
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")
DB_PASSWORD=$(python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(32)))")

cat > .env.demo << EOF
ENV=demo
SECRET_KEY=${SECRET_KEY}
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.demo

ALLOWED_HOSTS=demo-api.posx.io,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io

DB_NAME=posx_demo
DB_USER=posx_app
DB_PASSWORD=${DB_PASSWORD}
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

chmod 600 .env.demo
echo "✓ .env.demo 已创建"

echo "[3/8] 设置执行权限..."
chmod +x scripts/deploy_demo.sh deploy_demo_oneclick.sh verify_demo_deployment.sh

echo "[4/8] 执行部署脚本..."
./scripts/deploy_demo.sh --seed=minimal

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="

ENDSSH
```

### 方式 B：使用 PowerShell（如果没有 Git Bash）

```powershell
# 创建临时脚本
$script = @'
set -e
cd ~
[ ! -d "posx" ] && git clone https://github.com/your-org/posx.git
cd posx
git pull origin main

# 创建 .env.demo
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DB_PASSWORD=$(python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(32)))")

cat > .env.demo << EOF
ENV=demo
SECRET_KEY=${SECRET_KEY}
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.demo
ALLOWED_HOSTS=demo-api.posx.io,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://demo-api.posx.io
CORS_ALLOWED_ORIGINS=https://posx.retool.com,https://adminhq.posx.io
DB_NAME=posx_demo
DB_USER=posx_app
DB_PASSWORD=${DB_PASSWORD}
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
'@

# 执行
$script | ssh ubuntu@18.191.15.227 bash
```

---

## 步骤 3：验证部署（等待部署完成后执行）

### 3.1 基础验证（在本地执行）

```bash
# 健康检查
curl https://demo-api.posx.io/ready/

# 期望输出：{"status": "healthy", "checks": {...}}
```

### 3.2 完整验证（SSH 到服务器）

```bash
# SSH 到服务器
ssh ubuntu@18.191.15.227

# 进入项目目录
cd ~/posx

# 执行验证脚本
chmod +x verify_demo_deployment.sh
./verify_demo_deployment.sh
```

### 3.3 查看容器状态

```bash
# 查看所有容器
docker compose -f docker-compose.demo.yml ps

# 查看日志
docker compose -f docker-compose.demo.yml logs -f web
docker compose -f docker-compose.demo.yml logs caddy | grep -i certificate
```

---

## 步骤 4：访问验证

### 4.1 浏览器访问

**Django Admin**:
- URL: https://demo-api.posx.io/admin/
- 用户名: `admin`
- 密码: `Demo_Admin_2024!`

**健康检查**:
- URL: https://demo-api.posx.io/ready/
- 应显示 JSON 响应

### 4.2 API 测试（需要 JWT Token）

```bash
# 在 Retool 或前端获取 token 后测试
TOKEN="your_jwt_token"

curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Site-Code: NA" \
     https://demo-api.posx.io/api/v1/tiers/
```

---

## 🔧 故障排查

### 问题 1: SSH 连接失败

```bash
# 检查 SSH 密钥
ssh -v ubuntu@18.191.15.227

# 检查安全组端口 22 是否开放
```

### 问题 2: Git 克隆失败

```bash
# 确保仓库地址正确
# 如果是私有仓库，需要配置 SSH 密钥或使用 HTTPS + token
```

### 问题 3: SSL 证书未签发

```bash
# SSH 到服务器检查
ssh ubuntu@18.191.15.227
cd ~/posx
docker compose -f docker-compose.demo.yml logs caddy | tail -50

# 等待 5-10 分钟后重试
docker compose -f docker-compose.demo.yml restart caddy
```

### 问题 4: 健康检查失败

```bash
# 查看 web 日志
docker compose -f docker-compose.demo.yml logs web | tail -100

# 检查数据库
docker compose -f docker-compose.demo.yml exec db psql -U posx_app -d posx_demo -c "SELECT 1;"
```

---

## 📚 相关文档

- **快速开始**: docs/QUICK_START_DEMO.md
- **详细部署**: docs/DEPLOY_DEMO.md
- **环境变量**: docs/ENV_FILES_DEMO.md
- **完整总结**: DEPLOY_DEMO_SUMMARY.md

---

## ✅ 完成检查清单

- [ ] 步骤 1: .env.demo.example 已提交
- [ ] 步骤 2: 一键部署命令已执行
- [ ] 步骤 3: 验证脚本通过
- [ ] 步骤 4: 浏览器可访问 Admin
- [ ] Retool 已配置并测试成功

---

**祝部署顺利！** 🎉

如遇问题，请查看详细文档或查看日志排查。

