# Phase B 补充改进验收清单（10分钟快速验证）

## ⚡ 快速验收（5个核心场景）

### 1. 跨站点 RLS 隔离（2分钟）

```bash
export BASE_URL=http://localhost:8000
export TOKEN=<your_jwt>

# 在 NA 站点创建计划
PLAN_ID=$(curl -s -X POST $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Plan","version":1,"mode":"level"}' \
  | jq -r '.plan_id')

# 尝试从 ASIA 站点访问（应该 404）
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: ASIA" \
  $BASE_URL/api/v1/commission-plans/$PLAN_ID/

# ✅ 预期：404 + error_code = "RESOURCE.NOT_FOUND"
```

---

### 2. 输入校验增强（2分钟）

```bash
# 测试1：层级越界
curl -s -X POST $BASE_URL/api/v1/commission-plans/$PLAN_ID/tiers/bulk/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -H "Content-Type: application/json" \
  -d '{"tiers":[{"level":11,"rate_percent":"12.00"}]}'

# ✅ 预期：400 + "层级必须在 1-10 之间"

# 测试2：mode=level 时设置 diff_reward_enabled
curl -s -X POST $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bad Plan","version":1,"mode":"level","diff_reward_enabled":true}'

# ✅ 预期：400 + "mode='level' 时不支持差额奖励"
```

---

### 3. 激活版本原子保证（2分钟）

```bash
# 创建两个版本
V1_ID=$(curl -s -X POST $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -d '{"name":"Multi Plan","version":1,"mode":"level"}' | jq -r '.plan_id')

V2_ID=$(curl -s -X POST $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -d '{"name":"Multi Plan","version":2,"mode":"level"}' | jq -r '.plan_id')

# 激活 V1
curl -s -X PATCH $BASE_URL/api/v1/commission-plans/$V1_ID/activate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -d '{"is_active":true}'

# 激活 V2（应该自动停用 V1）
curl -s -X PATCH $BASE_URL/api/v1/commission-plans/$V2_ID/activate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA" \
  -d '{"is_active":true}'

# 查询激活计划（应该只有 V2）
curl -s "$BASE_URL/api/v1/commission-plans/?is_active=true&name=Multi+Plan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA"

# ✅ 预期：count=1, results[0].version=2
```

---

### 4. scope=all 强制分页（1分钟）

```bash
# 不带分页参数（应该 400）
curl -s "$BASE_URL/api/v1/agents/me/customers?scope=all" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA"

# ✅ 预期：400 + "scope=\"all\" 时必须提供 page 和 size 参数"

# 带分页参数（应该 200）
curl -s "$BASE_URL/api/v1/agents/me/customers?scope=all&page=1&size=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: NA"

# ✅ 预期：200 + 分页字段
```

---

### 5. Auth0 JWKS 失败快速返回（1分钟）

```bash
# 模拟：清空 Auth0 配置（需要重启服务）
# 1. 临时注释掉 .env 中的 AUTH0_DOMAIN
# 2. 重启服务：python manage.py runserver
# 3. 发送请求

curl -s $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer invalid_token" \
  -H "X-Site-Code: NA"

# ✅ 预期：401 + "AUTH.UNAUTHORIZED" + request_id 字段

# 查看日志：
# ✅ 预期：ERROR AUTH.JWKS_FETCH_FAILED
```

---

## 🧪 RLS 自动化测试（2分钟）

```bash
cd backend

# 运行 RLS 烟雾测试
python manage.py test apps.commission_plans.tests_rls -v 2

# ✅ 预期输出：
# test_cross_site_data_invisible ... ok
# test_cross_site_update_blocked ... ok
# test_set_local_auto_reset_after_transaction ... ok
# test_concurrent_set_local_isolation ... ok
# test_rls_query_performance ... ok
#
# Ran 5 tests in 0.X s
# OK
```

---

## 📋 改进功能对照表

| # | 改进项 | 文件 | 验证场景 |
|---|--------|------|---------|
| 1 | Auth0 启动校验 | `apps/core/apps.py` | 启动时看日志 |
| 2 | JWKS 快速失败 | `apps/core/authentication.py` | 场景5 |
| 3 | 统一错误响应 | `apps/core/exceptions.py` | 所有场景 |
| 4 | 输入增强校验 | `apps/commission_plans/serializers.py` | 场景2 |
| 5 | 激活原子保证 | `apps/commission_plans/serializers.py` | 场景3 |
| 6 | 强制分页 | `apps/agents/views.py` | 场景4 |
| 7 | RLS 烟雾测试 | `apps/commission_plans/tests_rls.py` | 自动化测试 |

---

## ✅ 验收标准

### 必须通过（100%）

- [ ] 跨站点数据不可见（场景1）
- [ ] 输入越界返回 400 + 友好错误（场景2）
- [ ] 并发激活仅一个生效（场景3）
- [ ] scope=all 无分页拒绝（场景4）
- [ ] RLS 自动化测试全通过（自动化测试）

### 推荐验证（可选）

- [ ] Auth0 配置缺失时有警告日志
- [ ] 所有错误响应包含 `code` 和 `request_id`
- [ ] JWKS 失败时日志包含 `AUTH.JWKS_FETCH_FAILED`

---

## 🚀 快速修复（如果验证失败）

### 问题 1：RLS 测试失败

```bash
# 检查 RLS 状态
psql -U posx_app -d posx_local -c "
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'commission_plans';
"

# 重新运行迁移
python manage.py migrate commission_plans --fake-initial
python manage.py migrate commission_plans
```

### 问题 2：激活并发失败

```bash
# 检查数据库事务隔离级别
psql -U posx_app -d posx_local -c "SHOW default_transaction_isolation;"

# 应该是 "read committed" 或更高
```

### 问题 3：分页参数不生效

```bash
# 检查代码逻辑
grep -n "PAGINATION_REQUIRED" backend/apps/agents/views.py

# 确认返回 400
```

---

**验收时间**: 10 分钟  
**完成标准**: 5/5 场景通过 + RLS 测试通过  
**状态**: ⬜ 待验收



