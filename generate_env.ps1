# ============================================
# POSX 环境配置生成脚本
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  POSX 环境配置生成器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已存在.env
if (Test-Path ".env") {
    Write-Host "警告: .env 文件已存在" -ForegroundColor Yellow
    $overwrite = Read-Host "是否覆盖? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "已取消" -ForegroundColor Red
        exit
    }
}

# 生成SECRET_KEY
Write-Host "正在生成 SECRET_KEY..." -ForegroundColor Green
$secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

if (-not $secretKey) {
    Write-Host "错误: 无法生成SECRET_KEY，请确保已安装Django" -ForegroundColor Red
    exit
}

Write-Host "SECRET_KEY 已生成: $($secretKey.Substring(0,20))..." -ForegroundColor Green

# 创建.env内容
$envContent = @"
# ============================================
# POSX 开发环境配置
# 自动生成于: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# ============================================

# ============================================
# Django 核心配置
# ============================================
SECRET_KEY=$secretKey
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# ============================================
# 数据库配置
# ============================================
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# ============================================
# Redis 配置（Docker）
# ============================================
REDIS_URL=redis://localhost:6379/0

# ============================================
# Auth0 配置
# ============================================
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/

# ============================================
# SIWE 配置
# ============================================
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# ============================================
# Stripe 配置
# ============================================
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=
MOCK_STRIPE=false

# ============================================
# 订单配置
# ============================================
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# ============================================
# Celery 配置
# ============================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false

# ============================================
# 前端配置
# ============================================
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA

# ============================================
# Fireblocks（Phase D）
# ============================================
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io

# ============================================
# 其他配置
# ============================================
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7
"@

# 写入文件
$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host ""
Write-Host "✅ .env 文件已创建！" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  下一步操作：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 安装Stripe CLI:" -ForegroundColor Yellow
Write-Host "   scoop install stripe/stripe-cli/stripe" -ForegroundColor White
Write-Host ""
Write-Host "2. 登录Stripe:" -ForegroundColor Yellow
Write-Host "   stripe login" -ForegroundColor White
Write-Host ""
Write-Host "3. 启动Webhook监听:" -ForegroundColor Yellow
Write-Host "   stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/" -ForegroundColor White
Write-Host "   复制输出的 whsec_*** 到 .env 的 STRIPE_WEBHOOK_SECRET" -ForegroundColor White
Write-Host ""
Write-Host "4. 启动Django:" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   python manage.py migrate" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "5. 验证配置:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:8000/health/" -ForegroundColor White
Write-Host ""

