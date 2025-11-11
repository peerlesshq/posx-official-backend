#!/bin/bash
# ============================================
# POSX Demo 一键部署脚本（在本地执行）
# ============================================
# 
# 使用方法：
# 1. 在 Windows Git Bash 或 PowerShell (WSL) 中执行
# 2. 或直接复制内容到服务器执行
# 
# ============================================

set -e

echo "=========================================="
echo "🚀 POSX Demo 环境一键部署"
echo "=========================================="
echo ""

# 检查是否在远程服务器上
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "✓ 检测到系统: $NAME $VERSION_ID"
else
    echo "⚠️  无法检测系统类型"
fi

echo ""

# 进入主目录
cd ~
echo "[1/10] 📂 切换到主目录: $(pwd)"

# 克隆或更新项目
if [ ! -d "posx" ]; then
    echo "[2/10] 📥 克隆项目..."
    # 替换为你的真实仓库地址
    git clone https://github.com/your-org/posx.git
    echo "✓ 项目克隆完成"
else
    echo "[2/10] 🔄 更新项目..."
    cd posx
    git pull origin main
    cd ~
    echo "✓ 项目更新完成"
fi

cd posx
echo "✓ 当前目录: $(pwd)"
echo ""

# 创建 .env.demo
echo "[3/10] 🔐 生成 .env.demo（包含真实凭据）..."

# 生成 SECRET_KEY
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")

# 生成 DB_PASSWORD
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
echo "✓ .env.demo 创建完成（SECRET_KEY 和 DB_PASSWORD 已自动生成）"
echo ""

# 设置脚本执行权限
echo "[4/10] 🔧 设置脚本执行权限..."
chmod +x scripts/deploy_demo.sh
echo "✓ 权限设置完成"
echo ""

# 执行部署脚本
echo "[5/10] 🚀 执行部署脚本..."
echo "=========================================="
./scripts/deploy_demo.sh --seed=minimal

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "📍 访问地址："
echo "   API:    https://demo-api.posx.io/api/v1/"
echo "   Health: https://demo-api.posx.io/ready/"
echo "   Admin:  https://demo-api.posx.io/admin/"
echo ""
echo "🔑 默认凭据："
echo "   用户名: admin"
echo "   密码:   Demo_Admin_2024!"
echo ""
echo "📊 常用命令："
echo "   查看日志: docker compose -f docker-compose.demo.yml logs -f web"
echo "   查看状态: docker compose -f docker-compose.demo.yml ps"
echo "   重启服务: docker compose -f docker-compose.demo.yml restart"
echo ""
echo "=========================================="

exit 0

