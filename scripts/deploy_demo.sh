#!/bin/bash
# ============================================
# POSX Demo 环境一键部署脚本
# ============================================
# 
# 功能：
# - 检测 Ubuntu 22.04
# - 安装 Docker & Docker Compose
# - 生成 .env.demo（如不存在）
# - 启动容器并初始化数据
# - 健康检查
# 
# 使用方法：
#   chmod +x scripts/deploy_demo.sh
#   ./scripts/deploy_demo.sh [--seed=minimal|none|full]
# 
# ============================================

set -e  # 遇错即退出

# ============================================
# 颜色输出
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# 日志函数
# ============================================
log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# ============================================
# 参数解析
# ============================================
SEED_MODE="minimal"  # 默认最小化种子数据

for arg in "$@"; do
    case $arg in
        --seed=*)
            SEED_MODE="${arg#*=}"
            shift
            ;;
        *)
            ;;
    esac
done

# 验证 seed 参数
if [[ ! "$SEED_MODE" =~ ^(minimal|none|full)$ ]]; then
    error "无效的 --seed 参数: $SEED_MODE (允许: minimal, none, full)"
fi

# ============================================
# 配置
# ============================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env.demo"
ENV_EXAMPLE="$PROJECT_DIR/.env.demo.example"
COMPOSE_FILE="docker-compose.demo.yml"
LOG_FILE="$HOME/posx-deploy-$(date +%Y%m%d_%H%M%S).log"

info "POSX Demo 环境部署脚本"
info "====================================="
info "项目目录: $PROJECT_DIR"
info "日志文件: $LOG_FILE"
info "Seed 模式: $SEED_MODE"
info "====================================="

# ============================================
# 1. 系统检测
# ============================================
log "检测操作系统..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    info "检测到系统: $OS $VER"
    
    if [[ ! "$OS" =~ "Ubuntu" ]]; then
        warn "此脚本为 Ubuntu 优化，当前系统: $OS"
        read -p "是否继续？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "用户取消"
        fi
    fi
else
    error "无法检测操作系统"
fi

# ============================================
# 2. DNS 检查
# ============================================
log "检查 DNS 解析..."

DEMO_DOMAIN="demo-api.posx.io"
EXPECTED_IP="18.191.15.227"

RESOLVED_IP=$(dig +short $DEMO_DOMAIN | tail -n1)

if [ -z "$RESOLVED_IP" ]; then
    warn "DNS 解析失败: $DEMO_DOMAIN"
    warn "请确保 DNS 已正确配置"
else
    if [ "$RESOLVED_IP" = "$EXPECTED_IP" ]; then
        log "DNS 解析正确: $DEMO_DOMAIN → $RESOLVED_IP"
    else
        warn "DNS 解析结果: $DEMO_DOMAIN → $RESOLVED_IP"
        warn "期望 IP: $EXPECTED_IP"
        warn "如果 DNS 尚未生效，请等待传播完成"
    fi
fi

# ============================================
# 3. 安装 Docker
# ============================================
if command -v docker &> /dev/null; then
    log "Docker 已安装: $(docker --version)"
else
    log "开始安装 Docker..."
    
    sudo apt-get update | tee -a "$LOG_FILE"
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release | tee -a "$LOG_FILE"
    
    # 添加 Docker GPG 密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加 Docker 仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装 Docker
    sudo apt-get update | tee -a "$LOG_FILE"
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin | tee -a "$LOG_FILE"
    
    # 将当前用户加入 docker 组
    sudo usermod -aG docker $USER
    
    log "Docker 安装完成"
    warn "请注销并重新登录以使 docker 组生效，或运行: newgrp docker"
fi

# 检查 Docker Compose
if command -v docker compose &> /dev/null; then
    log "Docker Compose 已安装: $(docker compose version)"
else
    error "Docker Compose 未安装或不可用"
fi

# ============================================
# 4. 生成 .env.demo
# ============================================
cd "$PROJECT_DIR"

if [ -f "$ENV_FILE" ]; then
    log ".env.demo 已存在，跳过生成"
else
    log "生成 .env.demo..."
    
    if [ ! -f "$ENV_EXAMPLE" ]; then
        error ".env.demo.example 不存在，无法生成配置"
    fi
    
    # 复制示例文件
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    
    # 生成 SECRET_KEY
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || \
                 python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")
    
    sed -i "s/GENERATE_WITH_DEPLOY_SCRIPT_OR_MANUALLY/$SECRET_KEY/" "$ENV_FILE"
    
    # 生成强密码
    DB_PASSWORD=$(python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(32)))")
    sed -i "s/CHANGE_ME_TO_STRONG_PASSWORD/$DB_PASSWORD/" "$ENV_FILE"
    
    log ".env.demo 已生成"
    warn "请编辑 $ENV_FILE 并填写以下必要信息："
    warn "  - AUTH0_CLIENT_ID"
    warn "  - AUTH0_CLIENT_SECRET"
    
    read -p "是否现在编辑？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} "$ENV_FILE"
    else
        warn "请手动编辑 $ENV_FILE 后重新运行此脚本"
        exit 0
    fi
fi

# ============================================
# 5. 启动容器
# ============================================
log "启动 Docker 容器..."

docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" up -d --build | tee -a "$LOG_FILE"

log "等待服务健康检查..."

# 等待最多 120 秒
for i in {1..24}; do
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
        log "服务启动成功"
        break
    fi
    
    if [ $i -eq 24 ]; then
        error "服务健康检查超时，请查看日志: docker compose -f $COMPOSE_FILE logs"
    fi
    
    info "等待中... ($i/24)"
    sleep 5
done

# ============================================
# 6. 执行数据库迁移
# ============================================
log "执行数据库迁移..."

docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput | tee -a "$LOG_FILE"

log "数据库迁移完成"

# ============================================
# 7. 加载种子数据
# ============================================
if [ "$SEED_MODE" = "none" ]; then
    info "跳过种子数据加载 (--seed=none)"
elif [ "$SEED_MODE" = "minimal" ]; then
    log "加载最小化种子数据..."
    
    # 加载 sites
    if [ -f "backend/fixtures/seed_sites.json" ]; then
        docker compose -f "$COMPOSE_FILE" exec -T web python manage.py loaddata fixtures/seed_sites.json | tee -a "$LOG_FILE" || warn "Sites 数据加载失败（可能已存在）"
    else
        warn "seed_sites.json 不存在"
    fi
    
    # 加载 commission_plans
    if [ -f "backend/fixtures/seed_commission_plans.json" ]; then
        docker compose -f "$COMPOSE_FILE" exec -T web python manage.py loaddata fixtures/seed_commission_plans.json | tee -a "$LOG_FILE" || warn "Commission plans 数据加载失败（可能已存在）"
    else
        warn "seed_commission_plans.json 不存在"
    fi
    
    log "种子数据加载完成"
elif [ "$SEED_MODE" = "full" ]; then
    log "加载全量测试数据..."
    
    # 加载所有 fixtures
    for fixture in backend/fixtures/*.json; do
        if [ -f "$fixture" ]; then
            FIXTURE_NAME=$(basename "$fixture")
            docker compose -f "$COMPOSE_FILE" exec -T web python manage.py loaddata "fixtures/$FIXTURE_NAME" | tee -a "$LOG_FILE" || warn "$FIXTURE_NAME 加载失败"
        fi
    done
    
    log "全量数据加载完成"
fi

# ============================================
# 8. 创建超级用户（非交互）
# ============================================
log "创建超级用户..."

docker compose -f "$COMPOSE_FILE" exec -T web python manage.py shell <<'PYEOF'
from django.contrib.auth import get_user_model

User = get_user_model()

# 尝试创建超级用户
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@posx.io',
        password='Demo_Admin_2024!'
    )
    print("✅ 超级用户创建成功")
    print("   用户名: admin")
    print("   密码: Demo_Admin_2024!")
else:
    print("ℹ️  超级用户已存在，跳过创建")
PYEOF

log "超级用户设置完成"

# ============================================
# 9. 健康检查
# ============================================
log "执行健康检查..."

sleep 5  # 等待服务完全启动

# 检查本地健康端点
HEALTH_URL="http://localhost/ready/"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    log "本地健康检查通过 ✓"
else
    warn "本地健康检查失败 (HTTP $HEALTH_RESPONSE)"
fi

# 检查 HTTPS 端点（如果 DNS 已生效）
HTTPS_URL="https://$DEMO_DOMAIN/ready/"
if [ -n "$RESOLVED_IP" ]; then
    info "检查 HTTPS 端点..."
    sleep 10  # 等待 Let's Encrypt 证书签发
    
    HTTPS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HTTPS_URL" 2>/dev/null || echo "000")
    
    if [ "$HTTPS_RESPONSE" = "200" ]; then
        log "HTTPS 健康检查通过 ✓"
    else
        warn "HTTPS 健康检查失败 (HTTP $HTTPS_RESPONSE)"
        warn "证书签发可能需要几分钟，请稍后手动检查"
    fi
fi

# ============================================
# 10. 安全提醒
# ============================================
warn ""
warn "====================================="
warn "安全检查清单："
warn "====================================="
warn "1. 限制 SSH 访问到固定 IP："
warn "   sudo ufw allow from YOUR_IP to any port 22"
warn "2. 确保端口 80/443 开放："
warn "   sudo ufw allow 80/tcp"
warn "   sudo ufw allow 443/tcp"
warn "3. 定期备份数据库："
warn "   docker compose -f $COMPOSE_FILE exec db pg_dump -U posx_app posx_demo > backup.sql"
warn "4. 查看日志："
warn "   docker compose -f $COMPOSE_FILE logs -f web"
warn "====================================="

# ============================================
# 11. 部署完成
# ============================================
log ""
log "====================================="
log "部署完成！"
log "====================================="
log ""
log "访问地址："
log "  API: https://$DEMO_DOMAIN/api/v1/"
log "  健康检查: https://$DEMO_DOMAIN/ready/"
log "  Admin: https://$DEMO_DOMAIN/admin/"
log ""
log "超级用户凭据："
log "  用户名: admin"
log "  邮箱: admin@posx.io"
log "  密码: Demo_Admin_2024!"
log ""
log "Auth0 配置:"
log "  Domain: dev-posx.us.auth0.com"
log "  Audience: https://$DEMO_DOMAIN/api/v1/"
log ""
log "常用命令："
log "  查看日志: docker compose -f $COMPOSE_FILE logs -f [service]"
log "  重启服务: docker compose -f $COMPOSE_FILE restart [service]"
log "  停止服务: docker compose -f $COMPOSE_FILE down"
log ""
log "详细文档: docs/DEPLOY_DEMO.md"
log "====================================="

exit 0

