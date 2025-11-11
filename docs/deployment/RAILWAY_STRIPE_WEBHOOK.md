# Railway Stripe Webhook 配置指南

本文档详细说明如何在 Railway 部署环境中配置 Stripe Webhook，确保支付事件正确处理。

---

## 概述

Stripe Webhook 是 POSX 订单支付流程的核心组件：

```
用户支付 → Stripe 处理 → Webhook 通知后端 → 更新订单状态 → 分配代币 → 计算佣金
```

---

## 前置条件

- ✅ Railway Backend 已部署并运行
- ✅ 已获取 Railway 域名（如 `posx-backend-prod.up.railway.app`）
- ✅ Stripe 账号（测试或生产）
- ✅ 后端 `/api/v1/webhooks/stripe/` 端点可访问

---

## 步骤 1: 验证 Webhook 端点

### 1.1 测试端点可访问性

```bash
curl -X POST https://<Railway域名>.up.railway.app/api/v1/webhooks/stripe/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**期望输出**:
```json
{"error": "Invalid payload"}
```
（返回 400 表示端点存在，但签名验证失败）

### 1.2 检查路由配置

在 Backend Service Shell 中：

```bash
cd backend
python manage.py show_urls | grep webhook
```

**期望输出**:
```
/api/v1/webhooks/stripe/    apps.webhooks.views.stripe_webhook_view    stripe_webhook
/api/v1/webhooks/fireblocks/    apps.webhooks.views.FireblocksWebhookView    fireblocks_webhook
```

---

## 步骤 2: 在 Stripe Dashboard 创建 Webhook

### 2.1 登录 Stripe Dashboard

- **测试环境**: [https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)
- **生产环境**: [https://dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks)

### 2.2 创建 Endpoint

1. 点击 **+ Add endpoint**
2. 填写配置：

#### Endpoint URL
```
https://<Railway域名>.up.railway.app/api/v1/webhooks/stripe/
```

**示例**:
```
https://posx-backend-production.up.railway.app/api/v1/webhooks/stripe/
```

⚠️ **注意**:
- 必须使用 `https://`（不能是 `http://`）
- 路径必须完整（包含 `/api/v1/webhooks/stripe/`）
- 末尾 `/` 不能省略

#### Description（可选）
```
POSX Production - Payment processing webhook
```

#### API version
选择最新版本或指定版本：
```
2025-08-27.basil
```

### 2.3 选择监听事件

根据 POSX 业务逻辑，选择以下事件：

#### 核心事件（必选）✅

| 事件名称 | 说明 | 处理逻辑 |
|---------|------|----------|
| `payment_intent.succeeded` | 支付成功 | 更新订单为 `paid`，触发代币分配 |
| `payment_intent.payment_failed` | 支付失败 | 更新订单为 `failed` |
| `charge.succeeded` | 扣款成功 | 二次确认支付（可选） |
| `charge.dispute.created` | 发生纠纷 | 记录纠纷，通知管理员 |

#### 可选事件 ⭕

| 事件名称 | 说明 | 处理逻辑 |
|---------|------|----------|
| `payment_intent.canceled` | 支付取消 | 更新订单为 `canceled` |
| `charge.failed` | 扣款失败 | 标记失败 |
| `charge.refunded` | 退款完成 | 处理退款逻辑 |
| `checkout.session.completed` | Checkout 完成 | 如使用 Stripe Checkout |

### 2.4 完成创建

点击 **Add endpoint**，Stripe 会生成 **Signing secret**。

---

## 步骤 3: 获取 Signing Secret

### 3.1 复制 Secret

创建完成后，Stripe 显示：

```
Signing secret
whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

点击 **Reveal** 按钮，复制完整密钥。

⚠️ **重要**: 此密钥仅显示一次，务必妥善保存。

### 3.2 区分测试/生产密钥

- **测试环境**: `whsec_test_...`（在测试模式下创建）
- **生产环境**: `whsec_...`（无 `test` 前缀）

---

## 步骤 4: 配置 Railway 环境变量

### 4.1 添加 Signing Secret

进入 Railway Backend Service → **Variables**：

```bash
STRIPE_WEBHOOK_SECRET=whsec_你复制的密钥
```

### 4.2 配置 Stripe API 密钥

#### 测试环境

```bash
MOCK_STRIPE=false
STRIPE_SECRET_KEY=sk_test_51xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_51xxxxx
STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx
```

#### 生产环境

```bash
MOCK_STRIPE=false
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### 4.3 重新部署

保存变量后，点击 **Redeploy** 或推送代码触发部署。

---

## 步骤 5: 测试 Webhook

### 5.1 使用 Stripe Dashboard 测试

1. 回到 Stripe Webhooks 页面
2. 点击你创建的 endpoint
3. 点击 **Send test webhook**
4. 选择事件类型：`payment_intent.succeeded`
5. 点击 **Send test webhook**

### 5.2 查看 Railway 日志

进入 Backend Service → **Deployments → Logs**，应该看到：

```log
[INFO] Received Stripe webhook: payment_intent.succeeded
[INFO] Event ID: evt_xxxxx
[INFO] Processing payment for order_id: <UUID>
[INFO] Order status updated: paid
```

### 5.3 检查响应状态

在 Stripe Dashboard 的 Webhook 详情页，查看 **Recent deliveries**：

| 时间 | 事件 | 状态 | 响应码 |
|------|------|------|--------|
| Just now | payment_intent.succeeded | ✅ Successful | 200 |

⚠️ **如果状态为失败**，展开查看响应详情：

```json
{
  "status": 400,
  "body": {
    "error": "Invalid signature"
  }
}
```

---

## 步骤 6: 真实支付测试

### 6.1 使用 Stripe 测试卡

在前端或 Retool 创建订单，使用以下测试卡支付：

| 卡号 | 场景 | 结果 |
|------|------|------|
| `4242 4242 4242 4242` | 成功支付 | Webhook 接收 `payment_intent.succeeded` |
| `4000 0000 0000 0002` | 卡被拒绝 | Webhook 接收 `payment_intent.payment_failed` |
| `4000 0000 0000 9995` | 资金不足 | Webhook 接收 `charge.failed` |

**通用测试数据**:
- **过期日期**: 任意未来日期（如 `12/34`）
- **CVC**: 任意 3 位数字（如 `123`）
- **邮编**: 任意 5 位数字（如 `12345`）

### 6.2 验证订单状态

```bash
# 在 Backend Service Shell
cd backend
python manage.py shell
```

```python
from apps.orders.models import Order

# 查找最近的订单
order = Order.objects.latest('created_at')
print(f"Order ID: {order.id}")
print(f"Status: {order.status}")  # 应为 'paid'
print(f"Stripe Payment Intent: {order.stripe_payment_intent_id}")
```

### 6.3 检查 Webhook 日志

```python
from apps.webhooks.models import WebhookEvent

# 查看最近的 Webhook 事件
events = WebhookEvent.objects.all().order_by('-received_at')[:5]
for event in events:
    print(f"{event.event_type} - {event.status} - {event.received_at}")
```

---

## 代码实现详解

### Webhook 处理流程

根据 `backend/apps/webhooks/views.py`：

```python
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook_view(request):
    """
    Stripe Webhook 入口
    
    流程：
    1. 签名验证
    2. 事件白名单检查
    3. 双重幂等保障
    4. 事件处理
    5. 返回 200
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # 1. 签名验证 ⭐
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return Response({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return Response({'error': 'Invalid signature'}, status=400)
    
    # 2. 事件白名单 ⭐
    ALLOWED_EVENT_TYPES = {
        'payment_intent.succeeded',
        'payment_intent.payment_failed',
        'charge.dispute.created',
    }
    
    if event.type not in ALLOWED_EVENT_TYPES:
        logger.warning(f"Ignored event: {event.type}")
        return Response(status=200)  # 返回200避免重试
    
    # 3. 幂等性检查 ⭐
    if check_and_mark_processed(event.id, source='stripe'):
        logger.info(f"Duplicate event: {event.id}")
        return Response(status=200)
    
    # 4. 事件处理
    if event.type == 'payment_intent.succeeded':
        handle_payment_succeeded(event)
    elif event.type == 'payment_intent.payment_failed':
        handle_payment_failed(event)
    elif event.type == 'charge.dispute.created':
        handle_dispute_created(event)
    
    return Response(status=200)
```

### 支付成功处理

```python
def handle_payment_succeeded(event):
    """处理支付成功事件"""
    payment_intent = event.data.object
    payment_intent_id = payment_intent.id
    
    try:
        # 查找订单
        order = Order.objects.get(stripe_payment_intent_id=payment_intent_id)
        
        # 状态检查（防止重复处理）
        if order.status == 'paid':
            logger.warning(f"Order {order.id} already paid")
            return
        
        # 更新订单
        with transaction.atomic():
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.payment_method = 'stripe'
            order.save()
        
        # 触发异步任务
        from apps.allocations.tasks import allocate_tokens
        from apps.commissions.tasks import calculate_commissions
        
        allocate_tokens.delay(str(order.id))
        calculate_commissions.delay(str(order.id))
        
        logger.info(f"Payment succeeded for order {order.id}")
        
    except Order.DoesNotExist:
        logger.error(f"Order not found: {payment_intent_id}")
```

---

## 安全最佳实践

### 1. 签名验证

✅ **必须验证**：每个 Webhook 请求都必须验证 `Stripe-Signature` 头。

❌ **禁止跳过**：不要禁用签名验证，即使在测试环境。

### 2. HTTPS 强制

✅ **仅 HTTPS**：Stripe 仅向 HTTPS 端点发送 Webhook。

❌ **禁止 HTTP**：本地测试使用 Stripe CLI 转发。

### 3. IP 白名单（可选）

Stripe Webhook 从固定 IP 段发送，可在反向代理层限制：

```
54.187.174.169/32
54.187.205.235/32
54.187.216.72/32
```

### 4. 幂等性保障

✅ **双重检查**：
1. `IdempotencyKey` 表记录事件 ID
2. 订单状态检查（避免重复处理）

### 5. 事件白名单

✅ **仅处理必需事件**：忽略不在白名单的事件，避免不必要的处理。

---

## 故障排查

### 问题 1: Webhook 返回 400（Invalid signature）

**原因**: Signing secret 不匹配  
**解决**:

1. 检查 Railway 环境变量 `STRIPE_WEBHOOK_SECRET`
2. 确认与 Stripe Dashboard 中的 Secret 一致
3. 确认没有复制多余的空格或换行符
4. 重新部署 Backend Service

### 问题 2: Webhook 返回 404

**原因**: URL 路径错误  
**解决**:

1. 检查 Stripe Endpoint URL 是否完整：
   ```
   https://<Railway域名>.up.railway.app/api/v1/webhooks/stripe/
   ```
2. 确认末尾 `/` 存在
3. 检查后端路由配置（`backend/config/urls.py`）

### 问题 3: Webhook 返回 500

**原因**: 后端处理逻辑错误  
**解决**:

1. 查看 Railway 日志：
   ```
   [ERROR] KeyError: 'payment_intent'
   ```
2. 检查事件数据结构是否匹配
3. 添加异常捕获和日志

### 问题 4: 订单未更新状态

**原因**: 事件未被处理或幂等键冲突  
**解决**:

1. 检查事件是否在白名单：
   ```python
   ALLOWED_EVENT_TYPES = {'payment_intent.succeeded', ...}
   ```
2. 检查幂等键表：
   ```sql
   SELECT * FROM webhooks_idempotencykey 
   WHERE key = 'evt_xxxxx';
   ```
3. 查看 Webhook 事件记录：
   ```python
   WebhookEvent.objects.filter(event_id='evt_xxxxx')
   ```

### 问题 5: 重复触发任务

**原因**: Webhook 被 Stripe 重试，但幂等性检查失效  
**解决**:

1. 确认幂等键创建成功：
   ```python
   def check_and_mark_processed(event_id: str) -> bool:
       try:
           IdempotencyKey.objects.create(key=event_id, ...)
           return False  # 首次处理
       except IntegrityError:
           return True  # 已处理
   ```
2. 添加订单状态二次检查

---

## 监控与日志

### 关键日志

在 Railway Backend Logs 中搜索：

```log
# 成功接收
[INFO] Received Stripe webhook: payment_intent.succeeded

# 签名验证失败
[ERROR] Signature verification failed: ...

# 重复事件
[INFO] Duplicate event: evt_xxxxx

# 订单处理成功
[INFO] Payment succeeded for order <UUID>

# 订单处理失败
[ERROR] Order not found: pi_xxxxx
```

### Stripe Dashboard 监控

1. Webhooks → 你的 endpoint → **Recent deliveries**
2. 查看成功率和响应时间
3. 点击失败的事件查看详细错误

### 设置告警（可选）

在 Railway 或 Sentry 中配置告警：
- Webhook 失败率 > 10%
- 响应时间 > 5 秒
- 500 错误频繁出现

---

## 从测试切换到生产

### 1. 更新 Stripe 密钥

```bash
# Railway Variables
MOCK_STRIPE=false
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # 生产 Webhook Secret
```

### 2. 在生产模式创建 Webhook

1. 切换到 Stripe **Live mode**
2. 创建新的 Webhook endpoint（使用生产域名）
3. 复制新的 Signing secret
4. 更新 Railway 环境变量

### 3. 测试生产 Webhook

使用真实信用卡进行小额测试（可随后退款）：

```bash
# 创建测试订单
curl -X POST https://<生产域名>/api/v1/orders/ \
  -H "Authorization: Bearer <生产Token>" \
  -H "X-Site-Code: NA" \
  -d '{"tier_id": "...", "quantity": 1, ...}'

# 完成支付（前端）

# 检查订单状态
curl https://<生产域名>/api/v1/orders/<order_id>/ \
  -H "Authorization: Bearer <生产Token>"
```

---

## 相关文档

- [Stripe Webhook 官方文档](https://stripe.com/docs/webhooks)
- [Stripe 测试卡号](https://stripe.com/docs/testing#cards)
- [Railway 部署指南](./RAILWAY_DEPLOYMENT_GUIDE.md)
- [环境变量配置](./RAILWAY_ENV_VARIABLES.md)

---

**创建时间**: 2025-01-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

