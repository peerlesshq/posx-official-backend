# POSX Development Environment Startup Script
# 一键启动所有必需服务

Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "POSX 开发环境启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "E:\300_Code\314_POSX_Official_Sale_App"
$backend = "$projectRoot\backend"

# 检查 .env 文件
if (-not (Test-Path "$projectRoot\.env")) {
    Write-Host "错误: .env 文件不存在！" -ForegroundColor Red
    Write-Host "请先运行配置向导。" -ForegroundColor Yellow
    exit 1
}

Write-Host "检查环境..." -ForegroundColor Yellow

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python 未安装或未添加到PATH" -ForegroundColor Red
    exit 1
}

# 检查 Stripe CLI
try {
    $stripeVersion = stripe --version 2>&1
    Write-Host "✓ Stripe CLI: $stripeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Stripe CLI 未安装或未添加到PATH" -ForegroundColor Red
    exit 1
}

# 检查 Redis
Write-Host "检查 Redis (Docker)..." -ForegroundColor Yellow
$redisRunning = docker ps --filter "ancestor=redis" --format "{{.Names}}" 2>$null
if ($redisRunning) {
    Write-Host "✓ Redis 容器运行中" -ForegroundColor Green
} else {
    Write-Host "⚠ Redis 容器未运行，尝试启动..." -ForegroundColor Yellow
    docker run -d -p 6379:6379 --name posx-redis redis 2>$null
    if ($?) {
        Write-Host "✓ Redis 已启动" -ForegroundColor Green
    } else {
        Write-Host "✗ Redis 启动失败，请手动检查" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动服务..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 服务1: Django
Write-Host "[1/4] 启动 Django 服务器..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "Write-Host '========================================' -ForegroundColor Cyan; Write-Host 'Django 开发服务器' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; cd $backend; python manage.py runserver"

Start-Sleep -Seconds 2

# 服务2: Celery Worker
Write-Host "[2/4] 启动 Celery Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "Write-Host '========================================' -ForegroundColor Cyan; Write-Host 'Celery Worker (任务处理)' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; cd $backend; celery -A config worker -l info"

Start-Sleep -Seconds 2

# 服务3: Celery Beat
Write-Host "[3/4] 启动 Celery Beat..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "Write-Host '========================================' -ForegroundColor Cyan; Write-Host 'Celery Beat (定时任务)' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; cd $backend; celery -A config beat -l info"

Start-Sleep -Seconds 2

# 服务4: Stripe Webhook
Write-Host "[4/4] 启动 Stripe Webhook 监听..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "Write-Host '========================================' -ForegroundColor Cyan; Write-Host 'Stripe Webhook 监听' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; Write-Host '重要提示：' -ForegroundColor Yellow; Write-Host '  - 复制输出的 whsec_*** 密钥' -ForegroundColor Gray; Write-Host '  - 确认与 .env 中的 STRIPE_WEBHOOK_SECRET 一致' -ForegroundColor Gray; Write-Host '  - 如果不一致，请更新 .env 并重启 Django' -ForegroundColor Gray; Write-Host ''; stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/"

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "所有服务已启动！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "运行中的服务：" -ForegroundColor Cyan
Write-Host "  1. Django 服务器: http://localhost:8000" -ForegroundColor Gray
Write-Host "  2. Celery Worker: 后台任务处理" -ForegroundColor Gray
Write-Host "  3. Celery Beat: 定时任务调度" -ForegroundColor Gray
Write-Host "  4. Stripe Webhook: 支付事件监听" -ForegroundColor Gray
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 检查 Stripe Webhook 窗口的 whsec_*** 密钥" -ForegroundColor Gray
Write-Host "  2. 确认与 .env 中的 STRIPE_WEBHOOK_SECRET 一致" -ForegroundColor Gray
Write-Host "  3. 参考 STARTUP_AND_TEST_GUIDE.md 运行测试" -ForegroundColor Gray
Write-Host ""
Write-Host "停止服务：在每个窗口按 Ctrl+C" -ForegroundColor Yellow
Write-Host ""

