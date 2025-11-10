# 🎯 Webhook 配置指南

**更新时间**: 2025-11-08  
**状态**: 根据当前代码情况

---

## 📋 当前代码状态

### ✅ 已实现的 Webhook

| Webhook        | 端点                           | 状态         | 事件类型                                                                                  |
| -------------- | ------------------------------ | ------------ | ----------------------------------------------------------------------------------------- |
| **Stripe**     | `/api/v1/webhooks/stripe/`     | ✅ 已实现     | `payment_intent.succeeded`<br>`payment_intent.payment_failed`<br>`charge.dispute.created` |
| **Fireblocks** | `/api/v1/webhooks/fireblocks/` | ⚠️ **未实现** | -                                                                                         |

### ⚠️ 重要说明

- **Stripe Webhook**: 已完全实现，可直接配置使用
- **Fireblocks Webhook**: 代码中只有模型支持，**视图和路由尚未实现**。如需使用，需要先实现端点。

---

## 🔧 Stripe Webhook 配置

### 开发环境配置

#### 步骤 1: 启动 Stripe CLI 监听

**在 PowerShell 中运行：**

```powershell
# 确保已登录
stripe login

# 启动 webhook 监听（保持窗口打开）
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**预期输出：**
```
> Ready! You are using Stripe API Version [2024-XX-XX]. 
> Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxx (^C to quit)
```

**🔑 关键：复制 `whsec_***` 这个密钥！**

#### 步骤 2: 配置环境变量

**打开 `.env` 文件，添加或更新：**

```bash
# Stripe 配置
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx  # ⚠️ 替换为步骤1中的实际值
MOCK_STRIPE=false
```

#### 步骤 3: 测试 Webhook

**保持监听窗口运行，打开新的 PowerShell 窗口：**

```powershell
# 启动 Django
cd E:\300_Code\314_POSX_Official_Sale_App\backend
python manage.py runserver

# 在另一个窗口触发测试事件
stripe trigger payment_intent.succeeded
```

**预期结果：**
- Stripe CLI 窗口显示：`[200] POST http://localhost:8000/api/v1/webhooks/stripe/`
- Django 窗口显示：`[webhook] Event received: payment_intent.succeeded`

**✅ 如果看到这些，说明配置成功！**

---

### 生产环境配置

#### 步骤 1: 在 Stripe Dashboard 创建 Webhook

1. 登录 [Stripe Dashboard](https://dashboard.stripe.com/)
2. 进入：**Developers → Webhooks**
3. 点击 **Add endpoint**
4. 填写配置：
   - **Endpoint URL**: `https://api.posx.io/api/v1/webhooks/stripe/`
     - ⚠️ 替换为您的实际生产域名
   - **Description**: `POSX Payment Webhook`
   - **Status**: `Active`

#### 步骤 2: 选择事件类型

**在 "Listen for" 部分，选择以下事件：**

- ✅ `payment_intent.succeeded` - 支付成功
- ✅ `payment_intent.payment_failed` - 支付失败
- ✅ `charge.dispute.created` - 争议创建（可选）

**⚠️ 注意：** 代码中只处理这 3 种事件，其他事件会被忽略并返回 200。

#### 步骤 3: 获取 Signing Secret

1. 创建 webhook 后，点击 **Reveal** 显示 Signing secret
2. 复制 `whsec_***` 值

#### 步骤 4: 配置生产环境变量

**在生产环境 `.env` 或环境变量中设置：**

```bash
STRIPE_SECRET_KEY=sk_live_xxx  # 生产密钥
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx  # 步骤3中获取的值
MOCK_STRIPE=false
```

#### 步骤 5: 验证配置

**使用 Stripe CLI 测试生产端点：**

```powershell
# 发送测试事件到生产环境
stripe trigger payment_intent.succeeded --override endpoint=https://api.posx.io/api/v1/webhooks/stripe/
```

**或在 Dashboard 中：**
1. 进入 Webhook 详情页
2. 点击 **Send test webhook**
3. 选择 `payment_intent.succeeded`
4. 检查服务器日志确认收到

---

## 🔥 Fireblocks Webhook 配置（待实现）

### ⚠️ 当前状态

**代码中尚未实现 Fireblocks webhook 端点**，但模型已支持。如需使用，需要：

1. 实现 `fireblocks_webhook_view` 视图
2. 添加路由 `/api/v1/webhooks/fireblocks/`
3. 实现签名验证（RSA-SHA512）
4. 实现事件处理逻辑

### 计划中的配置（参考）

#### 端点信息

- **URL**: `https://api.posx.io/api/v1/webhooks/fireblocks/`
- **方法**: `POST`
- **签名算法**: RSA-SHA512
- **签名 Header**: `X-Fireblocks-Signature`

#### 需要监听的事件

根据系统规范，需要监听：

- `TRANSACTION_STATUS_UPDATED` - 交易状态更新
  - `COMPLETED` - 交易完成
  - `FAILED` - 交易失败
  - `CANCELLED` - 交易取消

#### 环境变量配置

```bash
# Fireblocks 配置
FIREBLOCKS_API_KEY=xxx
FIREBLOCKS_PRIVATE_KEY=<pem-content>
FIREBLOCKS_BASE_URL=https://api.fireblocks.io  # 生产环境
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=POSX
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=<pem-content>  # 用于验证签名
```

#### 在 Fireblocks Console 配置

1. 登录 [Fireblocks Console](https://console.fireblocks.io/)
2. 进入：**Developer center → Webhooks**
3. 点击 **Create webhook**
4. 填写配置：
   - **Endpoint URL**: `https://api.posx.io/api/v1/webhooks/fireblocks/`
   - **Description**: `POSX Token Allocation Webhook`
   - **Status**: `Active`
5. 在 **Listen for** 部分，展开并选择：
   - ✅ **Transactions** → `TRANSACTION_STATUS_UPDATED`
6. 点击 **Create webhook**

**⚠️ 注意：** 此配置需要在代码实现端点后才能生效。

---

## 🔍 配置检查清单

### Stripe Webhook

#### 开发环境
- [ ] Stripe CLI 已登录（`stripe login`）
- [ ] Webhook 监听正在运行（`stripe listen`）
- [ ] `.env` 文件已配置 `STRIPE_WEBHOOK_SECRET`
- [ ] `STRIPE_WEBHOOK_SECRET` 与 `stripe listen` 输出一致
- [ ] Django 服务器可以启动
- [ ] 测试事件可以触发并接收

#### 生产环境
- [ ] Stripe Dashboard 中已创建 webhook 端点
- [ ] 端点 URL 正确（包含 `/api/v1/webhooks/stripe/`）
- [ ] 已选择正确的事件类型（3种）
- [ ] 生产环境变量已配置 `STRIPE_WEBHOOK_SECRET`
- [ ] 使用生产密钥（`sk_live_*`）
- [ ] 已测试生产端点

### Fireblocks Webhook

- [ ] ⚠️ **代码端点已实现**（当前未实现）
- [ ] Fireblocks Console 中已创建 webhook
- [ ] 端点 URL 正确（包含 `/api/v1/webhooks/fireblocks/`）
- [ ] 已选择 `TRANSACTION_STATUS_UPDATED` 事件
- [ ] 环境变量已配置 `FIREBLOCKS_WEBHOOK_PUBLIC_KEY`
- [ ] 签名验证已实现

---

## 🎯 代码实现位置

### Stripe Webhook（已实现）

| 文件                                   | 说明                               |
| -------------------------------------- | ---------------------------------- |
| `backend/apps/webhooks/views.py`       | Webhook 视图（签名验证、事件处理） |
| `backend/apps/webhooks/urls.py`        | URL 路由配置                       |
| `backend/apps/webhooks/models.py`      | 幂等性模型（IdempotencyKey）       |
| `backend/apps/webhooks/utils/audit.py` | 审计日志工具                       |

**关键代码：**

```python
# 端点路径
POST /api/v1/webhooks/stripe/

# 支持的事件
ALLOWED_EVENT_TYPES = {
    'payment_intent.succeeded',
    'payment_intent.payment_failed',
    'charge.dispute.created',
}
```

### Fireblocks Webhook（待实现）

**需要创建的文件：**

- `backend/apps/webhooks/views.py` - 添加 `fireblocks_webhook_view`
- `backend/apps/webhooks/urls.py` - 添加路由
- `backend/apps/webhooks/utils/fireblocks.py` - 签名验证工具

**参考实现位置：**

- 规范文档：`docs/specs/SPEC_SYSTEM_ARCH_v1.0.0.md` (第 9.2 节)
- 示例代码：`docs/reports/REPORT_REVIEW_ANALYSIS.md` (第 1386-1442 行)

---

## 🆘 常见问题

### Q1: Stripe webhook 返回 400 错误？

**A:** 检查以下几点：

1. **签名密钥不匹配**
   ```powershell
   # 检查当前监听的 secret
   stripe listen --print-secret
   # 对比 .env 中的 STRIPE_WEBHOOK_SECRET
   ```

2. **端点 URL 错误**
   - 开发环境：`http://localhost:8000/api/v1/webhooks/stripe/`
   - 生产环境：`https://api.posx.io/api/v1/webhooks/stripe/`
   - ⚠️ 注意尾部斜杠 `/`

3. **Django 服务器未运行**
   ```powershell
   # 确认服务器运行在 8000 端口
   python manage.py runserver
   ```

### Q2: 事件被忽略（返回 200 但未处理）？

**A:** 检查事件类型是否在白名单中：

```python
# 代码中只处理这 3 种事件
ALLOWED_EVENT_TYPES = {
    'payment_intent.succeeded',
    'payment_intent.payment_failed',
    'charge.dispute.created',
}
```

其他事件会被忽略并返回 200（避免 Stripe 重试）。

### Q3: Fireblocks webhook 如何配置？

**A:** 当前代码中**尚未实现** Fireblocks webhook 端点。需要：

1. 先实现代码端点（参考规范文档）
2. 再在 Fireblocks Console 中配置

### Q4: 如何测试 webhook？

**开发环境：**
```powershell
# 触发测试事件
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
```

**生产环境：**
- 在 Stripe Dashboard 中点击 **Send test webhook**
- 或使用 Stripe CLI：`stripe trigger --override endpoint=https://api.posx.io/api/v1/webhooks/stripe/`

---

## 📚 相关文档

- **Stripe 配置**: `docs/config/CONFIG_STRIPE.md`
- **环境变量配置**: `docs/config/CONFIG_ENV_SETUP.md`
- **系统规范**: `docs/specs/SPEC_SYSTEM_ARCH_v1.0.0.md`
- **Phase D 交付**: `docs/phases/PHASE_D_DELIVERY.md`

---

## ✅ 快速参考

### Stripe Webhook 端点

**开发环境：**
```
http://localhost:8000/api/v1/webhooks/stripe/
```

**生产环境：**
```
https://api.posx.io/api/v1/webhooks/stripe/
```

### Fireblocks Webhook 端点（待实现）

**生产环境：**
```
https://api.posx.io/api/v1/webhooks/fireblocks/
```

### 环境变量

```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_xxx  # 开发: sk_test_*, 生产: sk_live_*
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Fireblocks（待实现）
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=<pem-content>
```

---

**最后更新**: 2025-11-08  
**维护者**: POSX Team

