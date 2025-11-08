@echo off
REM POSX Framework - 开发服务器启动脚本

echo =====================================
echo POSX Framework v1.0.0 - 开发服务器
echo =====================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

echo ✅ 虚拟环境已激活
echo.

REM 检查 Django 配置
echo 🔍 检查 Django 配置...
python manage.py check
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Django 配置检查失败！
    pause
    exit /b 1
)
echo ✅ Django 配置检查通过
echo.

REM 检查迁移状态
echo 🔍 检查迁移状态...
python manage.py showmigrations --plan | findstr /C:"[ ]" > nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  发现未应用的迁移，正在应用...
    python manage.py migrate
) else (
    echo ✅ 所有迁移已应用
)
echo.

REM 启动开发服务器
echo 🚀 启动开发服务器...
echo.
echo 服务器地址: http://localhost:8000
echo 健康检查: http://localhost:8000/health/
echo 详细检查: http://localhost:8000/ready/
echo 管理后台: http://localhost:8000/admin/
echo.
echo 按 Ctrl+C 停止服务器
echo =====================================
echo.

python manage.py runserver 0.0.0.0:8000


