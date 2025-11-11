# Phase 1 API 文档

## 目录

1. [站点配置管理 API](#站点配置管理-api)
2. [产品配置管理 API](#产品配置管理-api)

---

## 站点配置管理 API

### 基础信息

- **Base URL**: `/api/v1/admin/sites/`
- **权限**: `IsAdminUser` (超级管理员)
- **认证**: JWT Token

### 1. 创建站点

**端点**: `POST /api/v1/admin/sites/`

**请求体**:
```json
{
  "code": "NA",
  "name": "North America",
  "domain": "na.example.com",
  "is_active": true
}
```

**字段说明**:
- `code`: 站点代码（2-20字符，自动转大写，唯一）
- `name`: 站点名称
- `domain`: 站点域名（唯一）
- `is_active`: 是否激活（默认 true）

**响应** (201 Created):
```json
{
  "site_id": "uuid",
  "code": "NA",
  "name": "North America",
  "domain": "na.example.com",
  "is_active": true,
  "created_at": "2025-11-10T10:00:00Z"
}
```

**错误示例** (400 Bad Request):
```json
{
  "code": ["站点代码 'NA' 已存在"]
}
```

---

### 2. 查询站点列表

**端点**: `GET /api/v1/admin/sites/`

**查询参数**:
- `is_active` (boolean): 按激活状态过滤
- `code` (string): 按代码搜索（模糊匹配）
- `ordering` (string): 排序字段
  - 可选值: `code`, `-code`, `name`, `-name`, `created_at`, `-created_at`
  - 默认: `-created_at`

**请求示例**:
```
GET /api/v1/admin/sites/?is_active=true&ordering=code
```

**响应** (200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "site_id": "uuid",
      "code": "ASIA",
      "name": "Asia Pacific",
      "domain": "asia.example.com",
      "is_active": true,
      "created_at": "2025-11-10T10:00:00Z"
    },
    {
      "site_id": "uuid",
      "code": "NA",
      "name": "North America",
      "domain": "na.example.com",
      "is_active": true,
      "created_at": "2025-11-10T09:00:00Z"
    }
  ]
}
```

---

### 3. 获取站点详情

**端点**: `GET /api/v1/admin/sites/{site_id}/`

**响应** (200 OK):
```json
{
  "site_id": "uuid",
  "code": "NA",
  "name": "North America",
  "domain": "na.example.com",
  "is_active": true,
  "created_at": "2025-11-10T10:00:00Z"
}
```

---

### 4. 更新站点

**端点**: 
- `PUT /api/v1/admin/sites/{site_id}/` (完整更新)
- `PATCH /api/v1/admin/sites/{site_id}/` (部分更新)

**请求体** (PATCH 示例):
```json
{
  "name": "North America (Updated)",
  "is_active": false
}
```

**响应** (200 OK):
```json
{
  "site_id": "uuid",
  "code": "NA",
  "name": "North America (Updated)",
  "domain": "na.example.com",
  "is_active": false,
  "created_at": "2025-11-10T10:00:00Z"
}
```

---

### 5. 软删除站点

**端点**: `DELETE /api/v1/admin/sites/{site_id}/`

**说明**: 不会真正删除数据，只是将 `is_active` 设为 `false`

**响应** (204 No Content)

---

### 6. 激活站点

**端点**: `POST /api/v1/admin/sites/{site_id}/activate/`

**请求体**: 无

**响应** (200 OK):
```json
{
  "message": "站点 \"NA\" 已激活",
  "site_id": "uuid"
}
```

---

### 7. 站点统计

**端点**: `GET /api/v1/admin/sites/{site_id}/stats/`

**响应** (200 OK):
```json
{
  "site_id": "uuid",
  "site_code": "NA",
  "site_name": "North America",
  "is_active": true,
  "orders": {
    "total": 150,
    "paid": 120,
    "pending": 30
  },
  "tiers": {
    "total": 5,
    "active": 4
  },
  "agents": {
    "total": 50,
    "active": 45
  },
  "commissions": {
    "total_count": 200,
    "total_amount": "24000.00"
  }
}
```

---

## 产品配置管理 API

### 基础信息

- **Base URL**: `/api/v1/admin/tiers/`
- **权限**: `IsAdminUser` (超级管理员)
- **认证**: JWT Token

### 1. 创建产品

**端点**: `POST /api/v1/admin/tiers/`

**请求头**:
```
X-Site-Code: NA
```

**请求体**:
```json
{
  "name": "Tier A",
  "description": "First tier with 10,000 tokens",
  "list_price_usd": "1000.00",
  "tokens_per_unit": "10000.00",
  "total_units": 10000,
  "display_order": 1,
  "is_active": true,
  "bonus_tokens_per_unit": "500.00",
  "promotional_price_usd": "800.00",
  "promotion_valid_from": "2025-11-01T00:00:00Z",
  "promotion_valid_until": "2025-12-31T23:59:59Z"
}
```

**字段说明**:
- `name`: 产品名称（必填）
- `description`: 产品描述
- `list_price_usd`: 原价（必填，> 0）
- `tokens_per_unit`: 单位代币数（必填，> 0）
- `total_units`: 总库存（必填，> 0）
- `display_order`: 展示顺序（默认 0）
- `is_active`: 是否激活（默认 true）
- `bonus_tokens_per_unit`: 额外赠送代币（默认 0）
- `promotional_price_usd`: 促销价（可选，必须 < 原价）
- `promotion_valid_from`: 促销开始时间（设置促销价时必填）
- `promotion_valid_until`: 促销结束时间（设置促销价时必填）

**响应** (201 Created):
```json
{
  "tier_id": "uuid",
  "site_code": "NA",
  "site_name": "North America",
  "name": "Tier A",
  "description": "First tier with 10,000 tokens",
  "list_price_usd": "1000.00",
  "tokens_per_unit": "10000.00",
  "bonus_tokens_per_unit": "500.00",
  "promotional_price_usd": "800.00",
  "promotion_valid_from": "2025-11-01T00:00:00Z",
  "promotion_valid_until": "2025-12-31T23:59:59Z",
  "total_units": 10000,
  "sold_units": 0,
  "available_units": 10000,
  "display_order": 1,
  "version": 0,
  "is_active": true,
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:00:00Z"
}
```

**验证规则**:
1. 促销价必须低于原价
2. 设置促销价时必须同时设置促销时间范围
3. 促销结束时间必须晚于开始时间

---

### 2. 查询产品列表

**端点**: `GET /api/v1/admin/tiers/`

**查询参数**:
- `site_code` (string): 按站点过滤
- `is_active` (boolean): 按激活状态过滤
- `stock_status` (string): 按库存状态过滤
  - `sold_out`: 售罄
  - `low_stock`: 低库存（< 10%）
  - `in_stock`: 有库存
- `ordering` (string): 排序字段
  - 可选值: `display_order`, `-display_order`, `list_price_usd`, `-list_price_usd`, `created_at`, `-created_at`, `sold_units`, `-sold_units`
  - 默认: `display_order`

**请求示例**:
```
GET /api/v1/admin/tiers/?site_code=NA&is_active=true&stock_status=in_stock
```

**响应** (200 OK):
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "tier_id": "uuid",
      "site_code": "NA",
      "site_name": "North America",
      "name": "Tier A",
      "list_price_usd": "1000.00",
      "sold_units": 2500,
      "available_units": 7500,
      "is_active": true,
      ...
    }
  ]
}
```

---

### 3. 获取产品详情

**端点**: `GET /api/v1/admin/tiers/{tier_id}/`

**响应** (200 OK):
```json
{
  "tier_id": "uuid",
  "site_code": "NA",
  "site_name": "North America",
  "name": "Tier A",
  "description": "First tier",
  "list_price_usd": "1000.00",
  "tokens_per_unit": "10000.00",
  "bonus_tokens_per_unit": "500.00",
  "promotional_price_usd": "800.00",
  "promotion_valid_from": "2025-11-01T00:00:00Z",
  "promotion_valid_until": "2025-12-31T23:59:59Z",
  "total_units": 10000,
  "sold_units": 2500,
  "available_units": 7500,
  "display_order": 1,
  "version": 5,
  "is_active": true,
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T15:30:00Z"
}
```

---

### 4. 更新产品

**端点**: 
- `PUT /api/v1/admin/tiers/{tier_id}/` (完整更新)
- `PATCH /api/v1/admin/tiers/{tier_id}/` (部分更新)

**请求体** (PATCH 示例):
```json
{
  "list_price_usd": "1200.00",
  "promotional_price_usd": null,
  "is_active": true
}
```

**约束**:
- 新 `total_units` 不能低于 `sold_units`

**响应** (200 OK):
```json
{
  "tier_id": "uuid",
  "name": "Tier A",
  "list_price_usd": "1200.00",
  "promotional_price_usd": null,
  ...
}
```

---

### 5. 调整库存

**端点**: `POST /api/v1/admin/tiers/{tier_id}/adjust-inventory/`

**请求体**:
```json
{
  "adjustment": 1000,
  "reason": "补货"
}
```

**字段说明**:
- `adjustment`: 调整量（正数=增加，负数=减少，不能为0）
- `reason`: 调整原因（可选）

**约束**:
- 调整后的 `total_units` 不能低于 `sold_units`
- 调整后的 `total_units` 不能为负数

**响应** (200 OK):
```json
{
  "message": "库存调整成功",
  "tier_id": "uuid",
  "adjustment": 1000,
  "old_inventory": {
    "total": 10000,
    "available": 7500
  },
  "new_inventory": {
    "total": 11000,
    "available": 8500
  }
}
```

**错误示例** (400 Bad Request):
```json
{
  "adjustment": ["调整后总库存 (2000) 不能低于已售数量 (2500)"]
}
```

---

### 6. 软删除产品

**端点**: `DELETE /api/v1/admin/tiers/{tier_id}/`

**说明**: 不会真正删除数据，只是将 `is_active` 设为 `false`

**响应** (204 No Content)

---

### 7. 激活产品

**端点**: `POST /api/v1/admin/tiers/{tier_id}/activate/`

**请求体**: 无

**响应** (200 OK):
```json
{
  "message": "产品 \"Tier A\" 已激活",
  "tier_id": "uuid"
}
```

---

### 8. 产品统计

**端点**: `GET /api/v1/admin/tiers/{tier_id}/stats/`

**响应** (200 OK):
```json
{
  "tier_id": "uuid",
  "tier_name": "Tier A",
  "orders": {
    "total": 150,
    "paid": 120,
    "pending": 30
  },
  "revenue": {
    "total": "150000.00",
    "paid": "120000.00"
  },
  "inventory": {
    "total": 10000,
    "sold": 2500,
    "available": 7500,
    "stock_percentage": 75.0
  }
}
```

---

## 通用错误响应

### 400 Bad Request
```json
{
  "field_name": ["错误信息"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}
```

---

## 示例：使用流程

### 1. 创建站点和产品

```bash
# 1. 创建站点
curl -X POST http://localhost:8000/api/v1/admin/sites/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "NA",
    "name": "North America",
    "domain": "na.example.com",
    "is_active": true
  }'

# 2. 创建产品
curl -X POST http://localhost:8000/api/v1/admin/tiers/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Site-Code: NA" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tier A",
    "description": "10,000 tokens",
    "list_price_usd": "1000.00",
    "tokens_per_unit": "10000.00",
    "total_units": 10000,
    "display_order": 1
  }'

# 3. 补货
curl -X POST http://localhost:8000/api/v1/admin/tiers/{tier_id}/adjust-inventory/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "adjustment": 5000,
    "reason": "补货"
  }'
```

---

## 注意事项

1. **权限要求**: 所有管理端点都需要超级管理员权限
2. **站点隔离**: 产品自动关联到请求中的站点（通过 `X-Site-Code` 头或 `request.site`）
3. **软删除**: DELETE 操作不会真正删除数据，只是标记为不活跃
4. **乐观锁**: 产品使用 `version` 字段进行并发控制（库存调整使用悲观锁）
5. **审计日志**: 所有操作都会记录日志（包含管理员邮箱、操作时间等）
6. **验证严格**: 所有金额、数量字段都有严格的验证规则

