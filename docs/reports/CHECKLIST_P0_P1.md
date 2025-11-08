# ✅ P0/P1 核对完成报告

## 🔍 核对结果

### P0 必核对项 ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| **ENV=local** | ✅ 已修复 | 删除了重复的 `ENV=dev`，仅保留 `ENV=local` |
| **DATABASE_URL** | ✅ 已配置 | `postgresql://posx_app:posx@localhost:5432/posx_local` |
| **CSRF_TRUSTED_ORIGINS** | ✅ 已配置 | `http://localhost:3000,http://127.0.0.1:3000` |
| **AUTH0_AUDIENCE** | ⚠️ 需人工核对 | 当前：`http://localhost:8000/api/v1/`<br>**请登录 Auth0 控制台确认** |
| **STRIPE_WEBHOOK_SECRET** | ⚠️ 需同步检查 | 当前：`whsec_4b0b7998...`<br>**每次 `stripe listen` 重启后检查** |

---

## 📋 P0 核对步骤（现在执行）

### 1. ✅ 已完成：.env 关键配置

```bash
ENV=local                                              # ✅ 已修复
DATABASE_URL=postgresql://posx_app:posx@localhost:5432/posx_local  # ✅ 已配置
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000   # ✅ 已配置
```

### 2. ⚠️ 待人工核对：Auth0 Audience

**操作步骤：**

1. 打开 Auth0 控制台：https://manage.auth0.com/
2. 进入：**Applications → APIs → POSX API**
3. 查看 **Identifier** 字段
4. 对比当前配置：`http://localhost:8000/api/v1/`

**核对重点：**
- ✅ 协议（http/https）一致
- ✅ 域名/端口一致
- ✅ 路径一致
- ✅ **尾部斜杠 `/` 是否一致**（这是最容易忽略的）

**如果不一致，修改 .env：**
```powershell
notepad .env
# 找到 AUTH0_AUDIENCE= 这一行，修改为完全一致的值
```

### 3. ⚠️ 每次启动检查：Stripe Webhook Secret

**检查命令：**
```powershell
stripe listen --print-secret
```

**预期输出：**
```
whsec_4b0b79987be979c07fe98e3df7d7353bb2a7ae5cc0227d0f01083c174120dbf9
```

**对比 .env 中的值：**
```powershell
cat .env | Select-String "STRIPE_WEBHOOK_SECRET="
```

**如果不一致：**
1. 更新 `.env` 文件中的 `STRIPE_WEBHOOK_SECRET`
2. **重启 Django 服务器**（Ctrl+C 后重新运行）

---

## 📋 P1 检查清单（启动前）

### 1. ✅ 四个终端启动（已提供脚本）

**一键启动：**
```powershell
.\start_dev.ps1
```

**或手动启动（4个终端窗口）：**

**终端1 - Django：**
```powershell
cd backend
python manage.py runserver
```
**预期**：`Starting development server at http://127.0.0.1:8000/`

**终端2 - Celery Worker：**
```powershell
cd backend
celery -A config worker -l info
```
**预期**：`celery@HOSTNAME ready.`

**终端3 - Celery Beat：**
```powershell
cd backend
celery -A config beat -l info
```
**预期**：`Scheduler: Starting...`

**终端4 - Stripe Webhook：**
```powershell
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```
**预期**：`Ready! Your webhook signing secret is whsec_***`

---

### 2. ✅ 触发事件使用真实 pi_XXX（已在指南中强调）

**错误示例：**
```powershell
# ❌ 不带 pi_XXX，会生成随机 ID
stripe trigger payment_intent.succeeded
# 结果：Order not found for PaymentIntent pi_random123
```

**正确示例：**
```powershell
# ✅ 使用真实订单的 pi_XXX
stripe trigger payment_intent.succeeded --add payment_intent:id=pi_3ABC...
# 结果：Order status updated: pending → paid
```

**获取真实 pi_XXX 的方法：**
1. 创建订单（POST `/api/v1/orders/`）
2. 从响应中获取 `stripe_payment_intent_id`
3. 使用该 ID 触发事件

---

### 3. ✅ Redis/PostgreSQL 检查（start_dev.ps1 已包含）

**手动检查命令：**

**Redis（Docker）：**
```powershell
docker ps | Select-String "redis"
```
**预期**：显示运行中的 Redis 容器

**PostgreSQL：**
```powershell
psql -U postgres -c "SELECT version();"
```
**预期**：显示 PostgreSQL 版本

**数据库是否存在：**
```powershell
psql -U postgres -c "\l" | Select-String "posx_local"
```
**预期**：显示 posx_local 数据库

---

### 4. ✅ 端到端三项自测（STARTUP_AND_TEST_GUIDE.md 已覆盖）

#### 测试A：验签+幂等 ✅

**操作：**
```powershell
# 第一次触发
stripe trigger payment_intent.succeeded

# 第二次触发（相同事件）
stripe trigger payment_intent.succeeded
```

**预期日志：**
```
# 第一次
[webhook] Event received: evt_xxx
Signature verified ✅
Processing event...

# 第二次（幂等跳过）
[webhook] Event evt_xxx already processed (idempotent skip)
```

---

#### 测试B：成功流 pending→paid→佣金 ✅

**操作：**
```powershell
# 1. 创建订单（使用 API 或 curl）
# 2. 获取返回的 pi_XXX
# 3. 触发支付成功
stripe trigger payment_intent.succeeded --add payment_intent:id=pi_XXX
```

**预期日志：**

**Django（终端1）：**
```
[webhook] payment_intent.succeeded for pi_XXX
Order <order_id> status: pending → paid
Commission calculation triggered
```

**Celery Worker（终端2）：**
```
[task] Calculating commission for order <order_id>
[task] Commission saved: <amount> USD
```

**SQL 校验：**
```sql
-- 订单状态已更新
SELECT order_id, status, final_price_usd FROM orders WHERE order_id = '<order_id>';
-- 预期：status = 'paid'

-- 佣金已记录
SELECT * FROM commissions WHERE order_id = '<order_id>';
-- 预期：至少1条记录
```

---

#### 测试C：失败流 pending→failed→库存回补 ✅

**操作：**
```powershell
stripe trigger payment_intent.payment_failed --add payment_intent:id=pi_XXX
```

**预期日志：**

**Django：**
```
[webhook] payment_intent.payment_failed for pi_XXX
Order <order_id> status: pending → failed
Inventory released: tier=<tier_id>, quantity=<qty>
```

**SQL 校验：**
```sql
-- 订单状态为 failed
SELECT order_id, status FROM orders WHERE order_id = '<order_id>';
-- 预期：status = 'failed'

-- 库存已回补
SELECT tier_id, available_units, sold_units FROM tiers WHERE tier_id = '<tier_id>';
-- 预期：available_units 增加，sold_units 减少
```

---

## 📊 核对总结

### P0 核对状态

| 项目 | 自动检查 | 人工核对 | 状态 |
|------|---------|---------|------|
| ENV=local | ✅ 已修复 | - | ✅ 完成 |
| DATABASE_URL | ✅ 已配置 | - | ✅ 完成 |
| CSRF_TRUSTED_ORIGINS | ✅ 已配置 | - | ✅ 完成 |
| Auth0 Audience | - | ⚠️ 需核对 | ⏳ 待确认 |
| Stripe Webhook Secret | ✅ 已配置 | ⚠️ 每次启动检查 | ⏳ 需监控 |

### P1 检查状态

| 项目 | 文档覆盖 | 脚本支持 | 状态 |
|------|---------|---------|------|
| 四个终端启动 | ✅ | ✅ start_dev.ps1 | ✅ 就绪 |
| 真实 pi_XXX 提醒 | ✅ | - | ✅ 已强调 |
| Redis/PG 检查 | ✅ | ✅ 部分自动 | ✅ 就绪 |
| 三项端到端测试 | ✅ | - | ✅ 详细指南 |

---

## ✅ 专家建议执行度

### P0（3/3 已实施，2/3 需人工确认）

- ✅ `.env` 三项关键配置已添加
- ✅ 核对清单已详细说明
- ⚠️ Auth0 Audience - 需登录控制台核对
- ⚠️ Stripe Secret - 需每次启动时检查

### P1（4/4 已完整覆盖）

- ✅ 四个终端启动流程（有脚本 + 手动指南）
- ✅ 真实 pi_XXX 使用提醒（已在测试指南中强调）
- ✅ Redis/PG 检查（start_dev.ps1 包含自动检查）
- ✅ 三项端到端测试（详细步骤 + 预期日志 + SQL 校验）

---

## 🎯 总结

### ✅ 已完成
- 所有文档和脚本已覆盖 P0/P1 要点
- .env 配置已修复（删除重复的 ENV=dev）
- 启动脚本和测试指南完整

### ⚠️ 需您操作
1. **立即核对**：登录 Auth0 控制台确认 Audience
2. **启动时检查**：运行 `stripe listen --print-secret`，对比 .env

### 🚀 下一步
```powershell
# 1. 核对 Auth0（如需要）
# 2. 启动所有服务
.\start_dev.ps1

# 3. 运行测试（参考 STARTUP_AND_TEST_GUIDE.md）
```

---

**专家的分析完全正确！文档和环境已准备就绪，只需盯紧 Audience 一致性和 whsec 同步这两件事。** ✅

