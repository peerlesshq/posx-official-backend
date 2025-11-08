# 🚀 POSX 启动和测试完整指南

## 📋 前置检查

### ✅ 已完成配置
- .env 文件已创建并配置完整
- Stripe CLI 已登录
- Redis Docker 容器运行中

### ⚠️ 核对清单（启动前必查）

#### 1. Auth0 Audience 一致性检查
```bash
# 打开 Auth0 控制台：https://manage.auth0.com/
# 进入：Applications → APIs → POSX API
# 检查 Identifier 字段是否完全一致（包括尾部斜杠）
```

**当前配置**：`http://localhost:8000/api/v1/`

**如果不一致，修改 .env：**
```bash
AUTH0_AUDIENCE=<粘贴Auth0控制台的完整Identifier>
```

#### 2. 环境变量最终配置

**.env 已更新为：**
- `ENV=local` （与Redis前缀保持一致）
- `DATABASE_URL=postgresql://posx_app:posx@localhost:5432/posx_local` （作为兜底）
- `CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` （前后端分离必须）

---

## 🎯 启动流程（4个终端）

### 终端1：Django 服务器

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend

# 1. 安装依赖（首次运行）
pip install -r requirements/production.txt

# 2. 运行数据库迁移（首次运行）
python manage.py migrate

# 3. 启动开发服务器
python manage.py runserver
```

**预期输出：**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### 终端2：Celery Worker（订单/佣金处理）

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend
celery -A config worker -l info
```

**预期输出：**
```
celery@HOSTNAME ready.
```

**⚠️ 重要**：这个进程处理：
- 订单过期任务
- 佣金计算任务
- 异步业务逻辑

---

### 终端3：Celery Beat（定时任务调度）

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend
celery -A config beat -l info
```

**预期输出：**
```
Scheduler: Starting...
```

**⚠️ 重要**：这个进程负责：
- 每5分钟扫描过期订单（`expire_pending_orders`）

---

### 终端4：Stripe Webhook 监听

```powershell
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**预期输出：**
```
> Ready! Your webhook signing secret is whsec_4b0b79987be979c07fe98e3df7d7353bb2a7ae5cc0227d0f01083c174120dbf9
```

**⚠️ 重要提醒**：
- `stripe listen` 每次重启时，检查输出的 `whsec_***` 
- 如果与 `.env` 中的不同，**必须同步更新 .env**
- 更新后需重启 Django 服务器

---

## 🧪 端到端测试（3个测试）

### 测试1：验证 Webhook 签名与幂等

**在新的PowerShell窗口运行：**

```powershell
# 触发测试事件
stripe trigger payment_intent.succeeded
```

**预期结果：**

**Stripe CLI（终端4）输出：**
```
[200] POST http://localhost:8000/api/v1/webhooks/stripe/ [evt_xxx]
```

**Django（终端1）日志：**
```
[webhook] Event received: payment_intent.succeeded
Signature verified ✅
Processing event: evt_xxx
```

**再次运行同样的命令：**
```powershell
stripe trigger payment_intent.succeeded
```

**预期：幂等跳过**
```
[webhook] Event evt_xxx already processed (idempotent skip)
```

---

### 测试2：完整订单流程（pending → paid → 佣金）

#### 步骤1：创建订单

```powershell
# 使用 curl 或 Postman 发送请求
curl -X POST http://localhost:8000/api/v1/orders/ `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <JWT_TOKEN>" `
  -H "X-Site-Code: NA" `
  -H "Idempotency-Key: test-order-001" `
  -d '{
    "tier_id": "<TIER_UUID>",
    "quantity": 1,
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "referral_code": ""
  }'
```

**预期响应：**
```json
{
  "order_id": "uuid-xxx",
  "status": "pending",
  "stripe_client_secret": "pi_xxx_secret_yyy"
}
```

**记录返回的 `stripe_payment_intent_id`**（格式：`pi_xxx`）

---

#### 步骤2：模拟支付成功

**使用实际的 PaymentIntent ID：**

```powershell
stripe trigger payment_intent.succeeded --add payment_intent:id=pi_xxx
```

**替换 `pi_xxx` 为步骤1返回的实际ID**

---

#### 步骤3：验证结果

**Django（终端1）日志应显示：**
```
[webhook] payment_intent.succeeded for pi_xxx
Order <order_id> status: pending → paid
Commission calculation triggered
```

**Celery Worker（终端2）日志应显示：**
```
[task] Calculating commission for order <order_id>
[task] Commission calculated: <amount>
```

**数据库验证：**
```sql
-- 订单状态已更新
SELECT order_id, status, final_price_usd FROM orders WHERE order_id = '<order_id>';

-- 佣金已记录
SELECT * FROM commissions WHERE order_id = '<order_id>';
```

---

### 测试3：失败路径（payment_failed → 库存回补）

**使用失败的 PaymentIntent：**

```powershell
stripe trigger payment_intent.payment_failed --add payment_intent:id=pi_xxx
```

**预期结果：**

**Django日志：**
```
[webhook] payment_intent.payment_failed for pi_xxx
Order <order_id> status: pending → failed
Inventory released: tier=<tier_id>, quantity=1
```

**数据库验证：**
```sql
-- 订单状态为 failed
SELECT order_id, status FROM orders WHERE order_id = '<order_id>';

-- 档位库存已回补
SELECT tier_id, available_units, sold_units FROM tiers WHERE tier_id = '<tier_id>';
```

---

## 🔍 常见问题排查

### ❌ 问题1：Webhook 签名验证失败

**错误信息：**
```
[webhook] Invalid signature
```

**排查步骤：**
1. 检查 Stripe CLI 输出的最新 `whsec_***`
2. 对比 `.env` 中的 `STRIPE_WEBHOOK_SECRET`
3. 如果不一致，更新 `.env` 并重启 Django

**验证命令：**
```powershell
# 查看当前监听的 secret
stripe listen --print-secret

# 对比 .env 中的值
cat .env | Select-String "STRIPE_WEBHOOK_SECRET"
```

---

### ❌ 问题2：触发事件后找不到订单

**错误信息：**
```
[webhook] Order not found for PaymentIntent pi_xxx
```

**原因：**
- `stripe trigger` 生成的是模拟事件，使用随机 `pi_xxx`
- 实际订单的 `pi_xxx` 与模拟的不匹配

**解决方案：**
- 创建订单后，使用返回的真实 `pi_xxx`
- 或者在 `MOCK_STRIPE=true` 模式下测试（不调用真实Stripe）

---

### ❌ 问题3：Celery 任务未执行

**排查步骤：**
1. 检查 Celery Worker 是否运行（终端2）
2. 检查 Redis 连接：
   ```powershell
   docker ps  # 确认Redis容器运行
   ```
3. 检查任务是否进入队列：
   ```python
   # Django shell
   python manage.py shell
   from celery import current_app
   current_app.control.inspect().active()
   ```

---

### ❌ 问题4：数据库连接失败

**错误信息：**
```
psycopg2.OperationalError: could not connect to server
```

**解决方案：**
```powershell
# 检查PostgreSQL服务
# 方法1：通过服务管理器
services.msc  # 查找 postgresql-x64-XX

# 方法2：通过命令行
psql -U postgres -c "SELECT version();"

# 如果数据库不存在，创建
createdb posx_local
```

---

## 📊 完整验证检查清单

运行所有测试后，确认：

- [ ] Django 服务器运行正常（`http://localhost:8000/`）
- [ ] Celery Worker 运行正常
- [ ] Celery Beat 运行正常
- [ ] Stripe Webhook 监听运行正常
- [ ] Webhook 签名验证通过
- [ ] 重复事件被幂等跳过
- [ ] 订单创建成功（返回 `pi_xxx`）
- [ ] 支付成功后订单状态更新为 `paid`
- [ ] 佣金计算任务被触发
- [ ] 支付失败后订单状态更新为 `failed`
- [ ] 库存正确回补

---

## 🎯 快速启动脚本（可选）

创建 `start_dev.ps1`：

```powershell
# 启动脚本：一键启动所有服务

Write-Host "Starting POSX Development Environment..." -ForegroundColor Cyan

# 启动 Django
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd E:\300_Code\314_POSX_Official_Sale_App\backend; python manage.py runserver"

# 启动 Celery Worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd E:\300_Code\314_POSX_Official_Sale_App\backend; celery -A config worker -l info"

# 启动 Celery Beat
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd E:\300_Code\314_POSX_Official_Sale_App\backend; celery -A config beat -l info"

# 启动 Stripe 监听
Start-Process powershell -ArgumentList "-NoExit", "-Command", "stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/"

Write-Host "All services started!" -ForegroundColor Green
Write-Host "Press Ctrl+C in each window to stop services." -ForegroundColor Yellow
```

**运行：**
```powershell
.\start_dev.ps1
```

---

## 📞 需要帮助？

如果遇到问题：
1. 检查所有4个终端的日志输出
2. 查看本文档的"常见问题排查"部分
3. 确认 `.env` 配置正确
4. 确认所有依赖已安装

---

## ✅ 启动完成

所有服务启动后，您可以开始开发和测试！🎉

