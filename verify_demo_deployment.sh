#!/bin/bash
# ============================================
# POSX Demo 部署验证脚本
# ============================================
# 
# 使用方法：
# 在服务器上执行：./verify_demo_deployment.sh
# 或在本地执行：ssh ubuntu@18.191.15.227 'bash -s' < verify_demo_deployment.sh
# 
# ============================================

set -e

echo "=========================================="
echo "🔍 POSX Demo 环境验证"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

FAILED=0

# 检查 1: 容器状态
echo "[1/8] 检查容器状态..."
cd ~/posx
if docker compose -f docker-compose.demo.yml ps | grep -q "healthy\|running"; then
    pass "容器正在运行"
    docker compose -f docker-compose.demo.yml ps
else
    fail "容器未运行或不健康"
    docker compose -f docker-compose.demo.yml ps
    FAILED=1
fi
echo ""

# 检查 2: 本地健康检查
echo "[2/8] 检查本地健康端点..."
HEALTH_RESPONSE=$(curl -s http://localhost/ready/ 2>/dev/null || echo "")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    pass "本地健康检查通过"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    fail "本地健康检查失败"
    echo "$HEALTH_RESPONSE"
    FAILED=1
fi
echo ""

# 检查 3: HTTPS 健康检查
echo "[3/8] 检查 HTTPS 端点..."
HTTPS_RESPONSE=$(curl -s https://demo-api.posx.io/ready/ 2>/dev/null || echo "")
if echo "$HTTPS_RESPONSE" | grep -q "healthy"; then
    pass "HTTPS 健康检查通过"
    echo "$HTTPS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HTTPS_RESPONSE"
else
    warn "HTTPS 健康检查失败（SSL 证书可能还在签发中，等待 5-10 分钟）"
    echo "$HTTPS_RESPONSE"
fi
echo ""

# 检查 4: SSL 证书
echo "[4/8] 检查 SSL 证书..."
if curl -I https://demo-api.posx.io 2>/dev/null | grep -q "HTTP/2 200\|HTTP/2 301"; then
    pass "SSL 证书已签发"
    curl -I https://demo-api.posx.io 2>/dev/null | head -n 5
else
    warn "SSL 证书可能还在签发中"
fi
echo ""

# 检查 5: 数据库连接
echo "[5/8] 检查数据库连接..."
if docker compose -f docker-compose.demo.yml exec -T db psql -U posx_app -d posx_demo -c "SELECT 1;" >/dev/null 2>&1; then
    pass "数据库连接正常"
else
    fail "数据库连接失败"
    FAILED=1
fi
echo ""

# 检查 6: Redis 连接
echo "[6/8] 检查 Redis 连接..."
if docker compose -f docker-compose.demo.yml exec -T redis redis-cli ping | grep -q "PONG"; then
    pass "Redis 连接正常"
else
    fail "Redis 连接失败"
    FAILED=1
fi
echo ""

# 检查 7: 数据库迁移
echo "[7/8] 检查数据库迁移状态..."
MIGRATIONS=$(docker compose -f docker-compose.demo.yml exec -T web python manage.py showmigrations --plan 2>/dev/null | grep -c "\\[X\\]" || echo "0")
if [ "$MIGRATIONS" -gt 0 ]; then
    pass "数据库迁移已执行（共 $MIGRATIONS 个）"
else
    fail "未检测到数据库迁移"
    FAILED=1
fi
echo ""

# 检查 8: 超级用户
echo "[8/8] 检查超级用户..."
HAS_SUPERUSER=$(docker compose -f docker-compose.demo.yml exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(is_superuser=True).exists())" 2>/dev/null | tail -n1)
if [ "$HAS_SUPERUSER" = "True" ]; then
    pass "超级用户已创建"
else
    warn "超级用户可能未创建"
fi
echo ""

# 总结
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有核心检查通过！${NC}"
    echo ""
    echo "🌐 访问地址："
    echo "   API:    https://demo-api.posx.io/api/v1/"
    echo "   Admin:  https://demo-api.posx.io/admin/"
    echo "   Health: https://demo-api.posx.io/ready/"
    echo ""
    echo "🔑 默认凭据："
    echo "   用户名: admin"
    echo "   密码:   Demo_Admin_2024!"
    echo ""
    echo "📝 下一步："
    echo "   1. 在浏览器访问 Admin 面板"
    echo "   2. 在 Retool 中配置 API 连接"
    echo "   3. 测试 API 端点"
else
    echo -e "${RED}❌ 部分检查失败${NC}"
    echo ""
    echo "🔧 故障排查："
    echo "   查看日志: docker compose -f docker-compose.demo.yml logs -f"
    echo "   查看状态: docker compose -f docker-compose.demo.yml ps"
    echo "   重启服务: docker compose -f docker-compose.demo.yml restart"
    echo ""
    echo "📚 详细文档: docs/DEPLOY_DEMO.md"
fi
echo "=========================================="

exit $FAILED

