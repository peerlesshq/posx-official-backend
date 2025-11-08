# POSX Phase B 验收测试手册

## 📋 测试概述

本文档提供 5 个核心 API 端点的 curl 测试示例和预期响应，用于验证 Phase B 实施成果。

---

## 🔧 前置准备

### 1. 启动服务

```bash
# 方式 1: Docker Compose（推荐）
docker-compose up

# 方式 2: 本地开发服务器
cd backend
python manage.py runserver
```

### 2. 运行数据库迁移

```bash
cd backend

# 运行所有迁移
python manage.py migrate

# 加载种子数据
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json
```

### 3. 获取测试 Token

**方式 1: Auth0 Dashboard**
1. 登录 Auth0 Dashboard
2. 进入 Applications → APIs → 选择你的 API
3. 点击 "Test" 标签页
4. 复制生成的 Access Token

**方式 2: M2M 应用（推荐生产测试）**
```bash
curl --request POST \
  --url https://YOUR_DOMAIN.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://api.posx.io",
    "grant_type": "client_credentials"
  }'
```

**方式 3: 临时绕过认证（仅本地开发）**
```python
# backend/config/settings/local.py
# 临时注释掉认证要求（仅用于测试站点上下文）
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],  # 空列表 = 无认证
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # 允许匿名
    ],
    # ...
}
```

### 4. 设置环境变量

```bash
export SITE=NA
export TOKEN=<your_auth0_token>
export BASE_URL=http://localhost:8000
```

---

## 🧪 测试场景

### 测试 #1: 创建佣金计划

**目的**: 验证 Auth0 认证 + 站点上下文 + 佣金计划创建

**请求**:
```bash
curl -X POST $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Plan A",
    "version": 1,
    "mode": "level",
    "diff_reward_enabled": false
  }'
```

**预期响应**:
```json
HTTP/1.1 201 Created
Content-Type: application/json

{
  "plan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "site_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Plan A",
  "version": 1,
  "mode": "level",
  "diff_reward_enabled": false,
  "effective_from": null,
  "effective_to": null,
  "is_active": false,
  "tiers": [],
  "tiers_count": 0,
  "created_at": "2025-11-08T12:00:00Z",
  "updated_at": "2025-11-08T12:00:00Z"
}
```

**关键验证点**:
- ✅ HTTP 状态码: `201 Created`
- ✅ `site_id` 匹配当前站点（NA）
- ✅ `plan_id` 为有效 UUID
- ✅ `tiers_count` 为 0（尚未添加层级）

**可能的错误**:
| HTTP | 错误原因 | 解决方案 |
|------|---------|---------|
| 400 | 站点不存在 | 检查 `X-Site-Code` 和种子数据 |
| 401 | Token 无效/过期 | 重新获取 Token |
| 403 | 权限不足 | 确认用户有 staff 权限 |

---

### 测试 #2: 批量创建层级

**目的**: 验证批量层级创建 + 数据验证

**前置**: 获取上一步创建的 `plan_id`

**请求**:
```bash
export PLAN_ID=f47ac10b-58cc-4372-a567-0e02b2c3d479

curl -X POST $BASE_URL/api/v1/commission-plans/$PLAN_ID/tiers/bulk/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Content-Type: application/json" \
  -d '{
    "tiers": [
      {"level": 1, "rate_percent": "12.00", "hold_days": 7},
      {"level": 2, "rate_percent": "5.00", "hold_days": 7},
      {"level": 3, "rate_percent": "3.00", "hold_days": 7}
    ]
  }'
```

**预期响应**:
```json
HTTP/1.1 201 Created
Content-Type: application/json

{
  "message": "成功创建 3 个层级",
  "tiers": [
    {
      "tier_id": "850e8400-e29b-41d4-a716-446655440000",
      "level": 1,
      "rate_percent": "12.00",
      "min_sales": "0.000000",
      "diff_cap_percent": null,
      "hold_days": 7,
      "created_at": "2025-11-08T12:01:00Z"
    },
    {
      "tier_id": "850e8400-e29b-41d4-a716-446655440001",
      "level": 2,
      "rate_percent": "5.00",
      "min_sales": "0.000000",
      "diff_cap_percent": null,
      "hold_days": 7,
      "created_at": "2025-11-08T12:01:00Z"
    },
    {
      "tier_id": "850e8400-e29b-41d4-a716-446655440002",
      "level": 3,
      "rate_percent": "3.00",
      "min_sales": "0.000000",
      "diff_cap_percent": null,
      "hold_days": 7,
      "created_at": "2025-11-08T12:01:00Z"
    }
  ]
}
```

**关键验证点**:
- ✅ HTTP 状态码: `201 Created`
- ✅ `message` 包含成功消息
- ✅ `tiers` 数组包含 3 个元素
- ✅ 每个 tier 有唯一的 `tier_id`
- ✅ `level` 按顺序（1, 2, 3）

**可能的错误**:
| HTTP | 错误原因 | 解决方案 |
|------|---------|---------|
| 400 | 层级重复 | 确保 level 唯一 |
| 400 | rate_percent 超出范围 | 检查 0-100 范围 |
| 404 | plan_id 不存在 | 检查 URL 和站点隔离 |

---

### 测试 #3: 查询某时点生效的计划

**目的**: 验证时间范围过滤 + 站点隔离

**请求**:
```bash
curl -X GET "$BASE_URL/api/v1/commission-plans/?active_at=2025-11-08T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"
```

**预期响应**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "plan_id": "650e8400-e29b-41d4-a716-446655440000",
      "name": "Standard Plan",
      "version": 1,
      "mode": "level",
      "is_active": true,
      "effective_from": "2025-11-01T00:00:00Z",
      "effective_to": null,
      "tiers_count": 3,
      "created_at": "2025-11-01T00:00:00Z"
    },
    {
      "plan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "Plan A",
      "version": 1,
      "mode": "level",
      "is_active": false,
      "effective_from": null,
      "effective_to": null,
      "tiers_count": 3,
      "created_at": "2025-11-08T12:00:00Z"
    }
  ]
}
```

**关键验证点**:
- ✅ HTTP 状态码: `200 OK`
- ✅ `results` 仅包含当前站点（NA）的计划
- ✅ 按 `created_at` 降序排列
- ✅ `tiers_count` 正确显示层级数量

**站点隔离验证**:
```bash
# 切换到 ASIA 站点
export SITE=ASIA

curl -X GET "$BASE_URL/api/v1/commission-plans/?active_at=2025-11-08T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"

# 应该返回空列表（ASIA 站点没有计划）
```

**预期响应**（ASIA 站点）:
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

---

### 测试 #4: 查询我的下线结构

**目的**: 验证代理树递归查询 + 站点隔离

**前置**: 需要创建测试代理树数据（临时用 SQL）

```sql
-- 在 psql 中执行（需要先设置 app.current_site_id）
SET LOCAL app.current_site_id = '550e8400-e29b-41d4-a716-446655440000'; -- NA 站点

-- 创建测试用户（如果不存在）
INSERT INTO users (user_id, email, referral_code, is_active)
VALUES 
  ('450e8400-e29b-41d4-a716-446655440000', 'agent1@test.com', 'NA-AGENT1', true),
  ('450e8400-e29b-41d4-a716-446655440001', 'agent2@test.com', 'NA-AGENT2', true),
  ('450e8400-e29b-41d4-a716-446655440002', 'agent3@test.com', 'NA-AGENT3', true)
ON CONFLICT (user_id) DO NOTHING;

-- 创建代理树（agent1 → agent2 → agent3）
INSERT INTO agent_trees (tree_id, site_id, agent, parent, depth, path, active)
VALUES 
  ('950e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', '450e8400-e29b-41d4-a716-446655440001', '450e8400-e29b-41d4-a716-446655440000', 1, '/450e8400-e29b-41d4-a716-446655440000/450e8400-e29b-41d4-a716-446655440001/', true),
  ('950e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', '450e8400-e29b-41d4-a716-446655440002', '450e8400-e29b-41d4-a716-446655440001', 2, '/450e8400-e29b-41d4-a716-446655440000/450e8400-e29b-41d4-a716-446655440001/450e8400-e29b-41d4-a716-446655440002/', true);
```

**请求**:
```bash
curl -X GET "$BASE_URL/api/v1/agents/me/structure?depth=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"
```

**预期响应**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "agent_id": "450e8400-e29b-41d4-a716-446655440000",
  "site_code": "NA",
  "total_downlines": 2,
  "structure": [
    {
      "agent_id": "450e8400-e29b-41d4-a716-446655440001",
      "parent_id": "450e8400-e29b-41d4-a716-446655440000",
      "depth": 1,
      "path": "/450e8400-e29b-41d4-a716-446655440000/450e8400-e29b-41d4-a716-446655440001/",
      "level": 1,
      "total_customers": 0
    },
    {
      "agent_id": "450e8400-e29b-41d4-a716-446655440002",
      "parent_id": "450e8400-e29b-41d4-a716-446655440001",
      "depth": 2,
      "path": "/450e8400-e29b-41d4-a716-446655440000/450e8400-e29b-41d4-a716-446655440001/450e8400-e29b-41d4-a716-446655440002/",
      "level": 2,
      "total_customers": 0
    }
  ]
}
```

**关键验证点**:
- ✅ HTTP 状态码: `200 OK`
- ✅ `total_downlines` 正确（2）
- ✅ `structure` 按层级排序
- ✅ `path` 显示完整层级路径
- ✅ `level` 递增（1, 2）

**注意**: 如果当前用户没有下线，`structure` 为空数组：
```json
{
  "agent_id": "user-uuid",
  "site_code": "NA",
  "total_downlines": 0,
  "structure": []
}
```

---

### 测试 #5: 查询我的客户（整条线）

**目的**: 验证客户列表查询 + 分页 + 搜索

**请求**:
```bash
curl -X GET "$BASE_URL/api/v1/agents/me/customers?scope=all&page=1&size=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"
```

**预期响应**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "total": 2,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "customers": [
    {
      "user_id": "450e8400-e29b-41d4-a716-446655440001",
      "email": "agent2@test.com",
      "referral_code": "NA-AGENT2",
      "depth": 1,
      "total_sales": "0.00",
      "last_order_at": null
    },
    {
      "user_id": "450e8400-e29b-41d4-a716-446655440002",
      "email": "agent3@test.com",
      "referral_code": "NA-AGENT3",
      "depth": 2,
      "total_sales": "0.00",
      "last_order_at": null
    }
  ]
}
```

**关键验证点**:
- ✅ HTTP 状态码: `200 OK`
- ✅ `total` 正确显示总数
- ✅ `customers` 数组包含下线用户
- ✅ `depth` 显示层级深度
- ✅ 分页字段正确（`page`, `page_size`, `total_pages`）

**测试搜索功能**:
```bash
# 按邮箱搜索
curl -X GET "$BASE_URL/api/v1/agents/me/customers?scope=all&search=agent2" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"

# 应该仅返回 agent2@test.com
```

**测试层级过滤**:
```bash
# 仅查询 level=1 的直接下线
curl -X GET "$BASE_URL/api/v1/agents/me/customers?scope=all&level=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"

# 应该仅返回 depth=1 的用户
```

---

## 📊 测试结果汇总表

| # | 测试场景 | HTTP 状态码 | 关键字段 | 站点隔离 | RLS 验证 |
|---|---------|------------|---------|---------|---------|
| 1 | 创建佣金计划 | 201 | `plan_id`, `site_id` | ✅ | ✅ |
| 2 | 批量创建层级 | 201 | `tiers[]`, `message` | ✅ | ✅ |
| 3 | 查询生效计划 | 200 | `results[]`, `count` | ✅ | ✅ |
| 4 | 查询下线结构 | 200 | `structure[]`, `total_downlines` | ✅ | ✅ |
| 5 | 查询客户列表 | 200 | `customers[]`, `total` | ✅ | ✅ |

---

## 🔍 RLS 验证测试

### 测试站点隔离

**步骤 1**: 在 NA 站点创建计划
```bash
export SITE=NA
curl -X POST $BASE_URL/api/v1/commission-plans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE" \
  -H "Content-Type: application/json" \
  -d '{"name": "NA Plan", "version": 1, "mode": "level"}'

# 记录返回的 plan_id
export NA_PLAN_ID=<plan_id>
```

**步骤 2**: 切换到 ASIA 站点，尝试访问 NA 计划
```bash
export SITE=ASIA
curl -X GET $BASE_URL/api/v1/commission-plans/$NA_PLAN_ID/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Site-Code: $SITE"

# 预期: 404 Not Found（RLS 隔离生效）
```

**预期响应**:
```json
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Not found."
}
```

✅ **验证通过**: ASIA 站点无法访问 NA 站点的数据

---

## 🐛 故障排查

### 问题 1: 401 Unauthorized

**可能原因**:
- Token 无效或过期
- Auth0 配置错误（`AUTH0_DOMAIN`, `AUTH0_AUDIENCE`）
- JWKS 端点无法访问

**解决方案**:
```bash
# 检查 Auth0 配置
python manage.py shell
>>> from django.conf import settings
>>> settings.AUTH0_DOMAIN
>>> settings.AUTH0_AUDIENCE

# 测试 JWKS 端点
curl https://{AUTH0_DOMAIN}/.well-known/jwks.json

# 重新获取 Token
```

### 问题 2: 400 Bad Request（无站点）

**可能原因**:
- 站点数据未加载
- `X-Site-Code` 拼写错误
- 站点未激活（`is_active=False`）

**解决方案**:
```bash
# 检查站点数据
python manage.py shell
>>> from apps.sites.models import Site
>>> Site.objects.all()
>>> Site.objects.get(code='NA')

# 重新加载 fixtures
python manage.py loaddata fixtures/seed_sites.json
```

### 问题 3: 404 Not Found（计划不存在）

**可能原因**:
- RLS 站点隔离（跨站点访问）
- `plan_id` 不存在
- 迁移未运行

**解决方案**:
```bash
# 检查迁移状态
python manage.py showmigrations commission_plans

# 运行迁移
python manage.py migrate commission_plans

# 检查 RLS 策略
psql -U posx_app -d posx_local -c "\d+ commission_plans"
```

---

## ✅ 验收通过标准

### 必需通过的测试

- [ ] 测试 #1: 创建佣金计划（201）
- [ ] 测试 #2: 批量创建层级（201）
- [ ] 测试 #3: 查询生效计划（200）
- [ ] 测试 #4: 查询下线结构（200）
- [ ] 测试 #5: 查询客户列表（200）

### 必需验证的安全特性

- [ ] Auth0 JWT 认证（401 on invalid token）
- [ ] 站点上下文（400 on missing site）
- [ ] RLS 站点隔离（404 on cross-site access）
- [ ] 数据验证（400 on invalid input）

### 可选验证（推荐）

- [ ] 分页功能（`page`, `size` 参数）
- [ ] 搜索功能（`search` 参数）
- [ ] 过滤功能（`is_active`, `active_at` 参数）
- [ ] 错误响应格式统一

---

**验收日期**: _________  
**验收人员**: _________  
**验收结果**: [ ] 通过 / [ ] 不通过  
**备注**: _______________



