# Promo Code 系统完整文档

**版本**: 1.0.0  
**最后更新**: 2025-11-10

## 目录

1. [系统概述](#系统概述)
2. [数据模型](#数据模型)
3. [API 接口](#api-接口)
4. [配置说明](#配置说明)
5. [使用示例](#使用示例)
6. [测试指南](#测试指南)

---

## 系统概述

### 核心功能

Promo Code 系统支持：
- ✅ **4种折扣类型**: 百分比折扣、固定金额折扣、额外代币、组合优惠
- ✅ **使用限制**: 总使用次数、每用户使用次数、最低订单金额
- ✅ **适用范围**: 全站点或指定产品
- ✅ **有效期管理**: 开始时间和结束时间
- ✅ **多站点隔离**: RLS 安全保护
- ✅ **审计追踪**: 完整的使用记录

### 设计原则

- **安全性**: RLS 保护，多站点数据隔离
- **幂等性**: 同一订单不可重复使用同一促销码
- **精确性**: 所有金额使用 Decimal，避免浮点误差
- **灵活性**: 支持多种折扣类型和限制条件
- **友好性**: 前端友好的 API 响应格式

---

## 数据模型

### PromoCode

促销码主表，包含所有促销配置。

**字段说明**:

| 字段                 | 类型           | 说明                        |
| -------------------- | -------------- | --------------------------- |
| `promo_id`           | UUID           | 主键                        |
| `site`               | ForeignKey     | 所属站点                    |
| `code`               | CharField(50)  | 促销码（唯一，自动转大写）  |
| `name`               | CharField(100) | 促销码名称                  |
| `description`        | TextField      | 描述                        |
| `discount_type`      | CharField(20)  | 折扣类型                    |
| `discount_value`     | Decimal        | 折扣值                      |
| `bonus_tokens_value` | Decimal        | 额外代币                    |
| `max_uses`           | Integer        | 最大使用次数（null=无限制） |
| `uses_per_user`      | Integer        | 每用户最大使用次数          |
| `current_uses`       | Integer        | 当前使用次数                |
| `valid_from`         | DateTime       | 生效开始时间                |
| `valid_until`        | DateTime       | 生效结束时间                |
| `min_order_amount`   | Decimal        | 最低订单金额                |
| `applicable_tiers`   | ManyToMany     | 适用产品（空=全部）         |
| `is_active`          | Boolean        | 是否激活                    |

**折扣类型**:
- `percentage`: 百分比折扣（如 15% off）
- `fixed_amount`: 固定金额折扣（如 $10 off）
- `bonus_tokens`: 仅额外代币（如 +500 tokens）
- `combo`: 组合优惠（折扣 + 额外代币）

### PromoCodeUsage

促销码使用记录，用于审计和幂等性保证。

**字段说明**:

| 字段                   | 类型          | 说明               |
| ---------------------- | ------------- | ------------------ |
| `usage_id`             | UUID          | 主键               |
| `promo_code`           | ForeignKey    | 关联促销码         |
| `order`                | OneToOneField | 关联订单（一对一） |
| `user`                 | ForeignKey    | 使用者             |
| `discount_applied`     | Decimal       | 实际应用的折扣金额 |
| `bonus_tokens_applied` | Decimal       | 实际赠送的额外代币 |
| `created_at`           | DateTime      | 使用时间           |

---

## API 接口

### 1. 创建 Promo Code（管理员）

**端点**: `POST /api/v1/admin/promo-codes/`  
**权限**: IsAdminUser  
**描述**: 创建新的促销码

**请求体**:
```json
{
  "code": "SUMMER2025",
  "name": "夏季促销",
  "description": "2025年夏季特惠活动",
  "discount_type": "percentage",
  "discount_value": "15.00",
  "bonus_tokens_value": "0",
  "max_uses": 1000,
  "uses_per_user": 1,
  "valid_from": "2025-06-01T00:00:00Z",
  "valid_until": "2025-08-31T23:59:59Z",
  "min_order_amount": "50.00",
  "applicable_tier_ids": []
}
```

**响应**: 201 Created
```json
{
  "promo_id": "uuid",
  "code": "SUMMER2025",
  "name": "夏季促销",
  ...
}
```

### 2. 查询 Promo Code 列表（管理员）

**端点**: `GET /api/v1/admin/promo-codes/`  
**权限**: IsAdminUser

**查询参数**:
- `is_active`: true/false
- `discount_type`: percentage/fixed_amount/bonus_tokens/combo
- `search`: 搜索 code 或 name

**响应**: 200 OK
```json
[
  {
    "promo_id": "uuid",
    "code": "SUMMER2025",
    "name": "夏季促销",
    "discount_type": "percentage",
    "discount_value": "15.00",
    "current_uses": 120,
    "max_uses": 1000,
    "uses_remaining": 880,
    "valid_from": "2025-06-01T00:00:00Z",
    "valid_until": "2025-08-31T23:59:59Z",
    "is_active": true
  }
]
```

### 3. 更新 Promo Code（管理员）

**端点**: `PATCH /api/v1/admin/promo-codes/{id}/`  
**权限**: IsAdminUser

**请求体**:
```json
{
  "is_active": false
}
```

### 4. 停用 Promo Code（管理员）

**端点**: `POST /api/v1/admin/promo-codes/{id}/deactivate/`  
**权限**: IsAdminUser

**响应**: 200 OK
```json
{
  "message": "促销码已停用",
  "code": "SUMMER2025"
}
```

### 5. 验证 Promo Code（用户）

**端点**: `POST /api/v1/promo-codes/validate/`  
**权限**: IsAuthenticated

**请求体**:
```json
{
  "code": "SUMMER2025",
  "tier_id": "uuid",
  "quantity": 10
}
```

**响应**: 200 OK（成功）
```json
{
  "valid": true,
  "code": "SUMMER2025",
  "discount_amount": "15.00",
  "bonus_tokens": "0",
  "final_price": "85.00",
  "message": "优惠码有效：享受15%折扣"
}
```

**响应**: 200 OK（失败）
```json
{
  "valid": false,
  "code": "SUMMER2025",
  "discount_amount": "0",
  "bonus_tokens": "0",
  "error": "促销码已过期，截止时间：2025-08-31 23:59",
  "error_code": "PROMO_CODE_EXPIRED"
}
```

### 6. 订单预览（用户）

**端点**: `POST /api/v1/orders/preview/`  
**权限**: IsAuthenticated

**请求体**:
```json
{
  "tier_id": "uuid",
  "quantity": 10,
  "promo_code": "SUMMER2025"
}
```

**响应**: 200 OK
```json
{
  "tier_id": "uuid",
  "tier_name": "黄金套餐",
  "quantity": 10,
  "pricing": {
    "unit_price": "0.08",
    "subtotal": "0.80",
    "discount": "0.12",
    "final_price": "0.68"
  },
  "tokens": {
    "base_tokens": "9990.0",
    "tier_bonus": "1000.0",
    "promo_bonus": "0",
    "total_tokens": "10990.0"
  },
  "promo_code": {
    "code": "SUMMER2025",
    "description": "15%折扣",
    "applied": true
  },
  "tier_promotion": {
    "active": true,
    "original_price": "0.10",
    "promotional_price": "0.08",
    "discount_percentage": "20.00",
    "ends_at": "2025-11-30T23:59:59Z"
  }
}
```

### 7. 创建订单（用户）

**端点**: `POST /api/v1/orders/`  
**权限**: IsAuthenticated

**请求体**:
```json
{
  "tier_id": "uuid",
  "quantity": 10,
  "wallet_address": "0xabc...",
  "referral_code": "NA-ABC123",
  "promo_code": "SUMMER2025"
}
```

**请求头**:
```
Idempotency-Key: order-123-456
```

---

## 配置说明

### Django Admin 配置

1. 登录 Django Admin：`http://your-domain/admin/`
2. 导航到 "Promo Codes" 部分
3. 点击 "Add Promo Code" 创建新促销码

**配置步骤**:

1. **基本信息**
   - Site: 选择站点（NA/ASIA）
   - Code: 输入促销码（建议全大写，系统会自动转换）
   - Name: 输入名称
   - Description: 输入描述

2. **折扣配置**
   - Discount Type: 选择折扣类型
     - Percentage: 百分比折扣 → 填写 discount_value (0-100)
     - Fixed Amount: 固定金额 → 填写 discount_value (USD)
     - Bonus Tokens: 额外代币 → 填写 bonus_tokens_value
     - Combo: 组合 → 同时填写折扣和代币
   - Discount Value: 折扣值
   - Bonus Tokens Value: 额外代币

3. **使用限制**
   - Max Uses: 总使用次数（留空=无限制）
   - Uses Per User: 每用户使用次数
   - Min Order Amount: 最低订单金额
   - Applicable Tiers: 适用产品（留空=全部产品）

4. **有效期**
   - Valid From: 开始时间
   - Valid Until: 结束时间

5. **状态**
   - Is Active: 是否激活

### 产品促销配置

在 Tiers Admin 中配置：

1. **额外代币赠送**
   - Bonus Tokens Per Unit: 每单位额外赠送代币

2. **限时促销价**
   - Promotional Price USD: 促销价
   - Promotion Valid From: 促销开始时间
   - Promotion Valid Until: 促销结束时间

---

## 使用示例

### 示例1：百分比折扣

**配置**:
```
Code: SAVE15
Type: Percentage
Value: 15%
Min Amount: $50
Max Uses: 1000
Per User: 1
```

**结果**:
- $100 订单 → 折扣 $15 → 实付 $85

### 示例2：固定金额折扣

**配置**:
```
Code: GET10OFF
Type: Fixed Amount
Value: $10
Max Uses: 500
Per User: 2
```

**结果**:
- $100 订单 → 折扣 $10 → 实付 $90
- $5 订单 → 折扣 $5 → 实付 $0（不超过订单金额）

### 示例3：额外代币奖励

**配置**:
```
Code: BONUS500
Type: Bonus Tokens
Value: 500 tokens
Applicable: 仅黄金套餐
```

**结果**:
- 购买 10 单位黄金套餐
- 基础代币: 9990
- Tier 赠送: 1000
- Promo 奖励: 500
- **总计: 11490 代币**

### 示例4：组合优惠

**配置**:
```
Code: MEGA20
Type: Combo
Discount: 20%
Bonus: 1000 tokens
Min Amount: $200
```

**结果**:
- $250 订单 → 折扣 $50 → 实付 $200
- 额外获得 1000 代币

### 示例5：产品促销 + Promo Code

**产品配置**:
```
原价: $0.10/单位
促销价: $0.08/单位（11/1-11/30）
基础代币: 999/单位
赠送代币: 100/单位
```

**Promo Code**:
```
Code: DOUBLE20
Discount: 20%
Bonus: 200 tokens
```

**购买 10 单位的结果**:
- 小计: 10 × $0.08 = $0.80
- 折扣: $0.80 × 20% = $0.16
- **实付: $0.64**
- 基础代币: 10 × 999 = 9990
- 产品赠送: 10 × 100 = 1000
- Promo 赠送: 200
- **总代币: 11190**

---

## 测试指南

### 单元测试

运行测试：
```bash
python manage.py test apps.orders.tests.test_promo_codes
```

### 手动测试步骤

1. **创建测试促销码**
   ```bash
   # 登录 Django Admin
   # 创建促销码: TEST10OFF (10% 折扣)
   ```

2. **验证促销码**
   ```bash
   curl -X POST http://localhost:8000/api/v1/promo-codes/validate/ \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "TEST10OFF",
       "tier_id": "{tier_id}",
       "quantity": 10
     }'
   ```

3. **预览订单**
   ```bash
   curl -X POST http://localhost:8000/api/v1/orders/preview/ \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{
       "tier_id": "{tier_id}",
       "quantity": 10,
       "promo_code": "TEST10OFF"
     }'
   ```

4. **创建订单**
   ```bash
   curl -X POST http://localhost:8000/api/v1/orders/ \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: test-{timestamp}" \
     -d '{
       "tier_id": "{tier_id}",
       "quantity": 10,
       "wallet_address": "0x...",
       "promo_code": "TEST10OFF"
     }'
   ```

---

## 错误代码

| 错误代码                         | 说明                   |
| -------------------------------- | ---------------------- |
| `PROMO_CODE_NOT_FOUND`           | 促销码不存在           |
| `PROMO_CODE_SITE_MISMATCH`       | 促销码不适用于当前站点 |
| `PROMO_CODE_INACTIVE`            | 促销码已停用           |
| `PROMO_CODE_NOT_YET_VALID`       | 促销码尚未生效         |
| `PROMO_CODE_EXPIRED`             | 促销码已过期           |
| `PROMO_CODE_EXHAUSTED`           | 促销码使用次数已达上限 |
| `PROMO_CODE_USER_LIMIT_EXCEEDED` | 用户已达到使用次数限制 |
| `PROMO_CODE_MIN_AMOUNT_NOT_MET`  | 订单金额不满足最低要求 |
| `PROMO_CODE_TIER_NOT_APPLICABLE` | 促销码不适用于当前产品 |

---

## 常见问题

**Q: 促销码区分大小写吗？**  
A: 不区分。系统会自动将输入的促销码转换为大写。

**Q: 可以同时使用多个促销码吗？**  
A: 不可以。每个订单只能使用一个促销码。

**Q: 佣金基于折扣前还是折扣后的金额计算？**  
A: 基于折扣后的实付金额 (`final_price_usd`) 计算。

**Q: 如何查看促销码的使用记录？**  
A: 在 Django Admin 中访问 "Promo Code Usages"。

**Q: 促销码可以与产品促销叠加使用吗？**  
A: 可以。先应用产品促销价，再应用促销码折扣。

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-10  
**维护者**: POSX Development Team

