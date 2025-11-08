#!/bin/bash
# Phase C 自动化验收脚本

echo "🧪 POSX Phase C 验收测试"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 测试函数
run_test() {
    local test_name=$1
    local test_cmd=$2
    
    echo -n "测试: $test_name ... "
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
    fi
}

# 1. 金额工具测试
echo "1️⃣ 金额处理工具测试"
echo "----------------------------------"

run_test "to_cents转换" \
    "python manage.py test apps.core.tests_money.MoneyUtilsTestCase.test_to_cents"

run_test "from_cents转换" \
    "python manage.py test apps.core.tests_money.MoneyUtilsTestCase.test_from_cents"

run_test "往返转换一致性" \
    "python manage.py test apps.core.tests_money.MoneyUtilsTestCase.test_round_trip_conversion"

echo ""

# 2. Nonce服务测试
echo "2️⃣ Nonce服务测试"
echo "----------------------------------"

run_test "Nonce生成与消费" \
    "python manage.py test apps.users.tests_siwe.NonceServiceTestCase.test_generate_and_consume_nonce"

run_test "Nonce站点隔离" \
    "python manage.py test apps.users.tests_siwe.NonceServiceTestCase.test_nonce_site_isolation"

echo ""

# 3. 库存服务测试
echo "3️⃣ 库存乐观锁测试"
echo "----------------------------------"

run_test "库存锁定成功" \
    "python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_lock_inventory_success"

run_test "库存不足拒绝" \
    "python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_lock_inventory_insufficient"

run_test "并发锁库存（10线程）" \
    "python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_concurrent_lock_inventory"

run_test "库存回补" \
    "python manage.py test apps.tiers.tests_inventory.InventoryServiceTestCase.test_release_inventory"

echo ""

# 4. 订单流程测试
echo "4️⃣ 订单流程测试"
echo "----------------------------------"

run_test "订单快照创建" \
    "python manage.py test apps.orders.tests_e2e.OrderE2ETestCase.test_commission_snapshot_created"

run_test "订单超时取消" \
    "python manage.py test apps.orders.tests_e2e.OrderE2ETestCase.test_order_timeout_cancellation"

echo ""

# 汇总
echo "=================================="
echo "测试结果汇总:"
echo "----------------------------------"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
TOTAL=$((PASSED + FAILED))
echo "总计: $TOTAL"

# 计算通过率
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo "通过率: $PASS_RATE%"
    
    if [ $PASS_RATE -eq 100 ]; then
        echo ""
        echo -e "${GREEN}🎉 所有测试通过！Phase C 验收成功！${NC}"
        exit 0
    else
        echo ""
        echo -e "${YELLOW}⚠️ 部分测试失败，请检查日志${NC}"
        exit 1
    fi
else
    echo ""
    echo -e "${RED}❌ 无法运行测试，请检查环境配置${NC}"
    exit 1
fi


