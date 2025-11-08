# 🔧 Stripe CLI 配置指南

## 📋 概述

Stripe CLI 可以将 Stripe 的 webhook 事件转发到您的本地开发服务器（localhost:8000），无需公网暴露。

**官方文档**: https://docs.stripe.com/stripe-cli/install

---

## 🚀 第1步：安装 Stripe CLI（Windows）

### 方法1：使用 Scoop（推荐）

```powershell
# 1. 安装Scoop（如果还没有）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# 2. 安装Stripe CLI
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe
```

### 方法2：直接下载

1. 访问：https://github.com/stripe/stripe-cli/releases/latest
2. 下载 `stripe_X.X.X_windows_x86_64.zip`
3. 解压到任意目录（如 `C:\stripe\`）
4. 添加到PATH环境变量

### 方法3：使用Chocolatey

```powershell
choco install stripe-cli
```

### 验证安装

```bash
stripe --version
```

**预期输出**: `stripe version X.X.X`

---

## 🔐 第2步：登录 Stripe CLI

### 操作：

```bash
stripe login
```

### 流程：

1. **CLI 会输出**：
   ```
   Your pairing code is: enjoy-enough-outwit-win
   This pairing code verifies your authentication with Stripe.
   Press Enter to open the browser...
   ```

2. **按 Enter** 打开浏览器

3. **在浏览器中**：
   - 登录您的 Stripe 账号
   - 确认配对码
   - 点击 "Allow access"

4. **返回终端**，应该看到：
   ```
   Done! The Stripe CLI is configured for [您的账号] with account id acct_***
   ```

**✅ 登录成功！**

---

## 🎧 第3步：启动本地 Webhook 监听

### 操作：

```bash
# 启动监听（转发到本地8000端口）
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

### 预期输出：

```
> Ready! You are using Stripe API Version [2024-XX-XX]. Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxx (^C to quit)
```

**🔑 重要！复制这个 `whsec_***` 密钥**

---

## 📝 第4步：配置 Webhook Secret

### 操作1：复制密钥

从上一步的输出中复制 `whsec_***` 开头的完整字符串

### 操作2：添加到.env

打开 `.env` 文件，找到：

```bash
STRIPE_WEBHOOK_SECRET=
```

粘贴密钥：

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
```

### 操作3：保存.env并重启Django

```bash
# Ctrl+C 停止Django服务器

# 重新启动
cd backend
python manage.py runserver
```

**✅ Stripe Webhook 配置完成！**

---

## 🧪 第5步：测试 Webhook

### 保持监听运行

**终端1**：Stripe CLI监听
```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**终端2**：Django服务器
```bash
cd backend
python manage.py runserver
```

### 触发测试事件

**终端3**：触发事件
```bash
# 测试支付成功
stripe trigger payment_intent.succeeded
```

### 预期输出

**Stripe CLI（终端1）**：
```
2025-11-08 12:00:00   --> payment_intent.succeeded [evt_xxx]
2025-11-08 12:00:00   <-- [200] POST http://localhost:8000/api/v1/webhooks/stripe/ [evt_xxx]
```

**Django（终端2）**：
```
[webhook] Event received: payment_intent.succeeded
Signature verified ✅
```

**✅ 如果看到这些，Webhook工作正常！**

---

## 📊 完整工作流程

```
Stripe                     Stripe CLI                  Your Backend
  |                             |                            |
  | webhook event              |                            |
  |--------------------------->|                            |
  |                            |                            |
  |                            | HTTP POST                  |
  |                            |--------------------------->|
  |                            |                            |
  |                            |                 verify signature
  |                            |                 process event
  |                            |                            |
  |                            |         200 OK             |
  |                            |<---------------------------|
```

---

## 🎯 常用 Stripe CLI 命令

### 触发测试事件

```bash
# 支付成功
stripe trigger payment_intent.succeeded

# 支付失败
stripe trigger payment_intent.payment_failed

# 退款
stripe trigger charge.refunded

# 争议
stripe trigger charge.dispute.created

# 查看所有可触发的事件
stripe trigger --help
```

### 查看事件日志

```bash
# 实时查看Stripe事件
stripe events tail

# 查看最近的事件
stripe events list --limit 10
```

### 测试支付流程

```bash
# 使用测试卡号创建支付
# 成功卡号：4242 4242 4242 4242
# 失败卡号：4000 0000 0000 0002
```

**测试卡号列表**: https://stripe.com/docs/testing#cards

---

## 📋 配置检查清单

### 完成后应该有：

- [x] Stripe CLI 已安装（`stripe --version`）
- [x] Stripe CLI 已登录（`stripe login`）
- [x] 监听已启动（`stripe listen --forward-to ...`）
- [x] STRIPE_WEBHOOK_SECRET 已配置到.env
- [x] Django已重启（读取新的webhook secret）
- [x] 测试事件触发成功（`stripe trigger ...`）

---

## ⚠️ 常见问题

### 问题1: stripe命令未找到

**错误**: `'stripe' is not recognized as an internal or external command`

**解决**: 
1. 重新安装Stripe CLI
2. 确认PATH环境变量包含stripe.exe路径
3. 重启PowerShell

---

### 问题2: 登录失败

**错误**: `Failed to authenticate`

**解决**: 
1. 检查网络连接
2. 确认Stripe账号有效
3. 尝试使用API key登录：
   ```bash
   stripe login --api-key sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
   ```

---

### 问题3: Webhook未收到

**检查**:
1. Django服务器是否运行在8000端口
2. Stripe CLI监听是否正在运行
3. Webhook路由是否正确配置

```bash
# 检查路由
curl http://localhost:8000/api/v1/webhooks/stripe/ -X POST

# 应该返回405或类似错误（说明路由存在）
```

---

## 🎉 成功标志

您应该看到：

1. ✅ `stripe --version` 显示版本号
2. ✅ `stripe login` 登录成功
3. ✅ `stripe listen` 显示 "Ready!"
4. ✅ `stripe trigger payment_intent.succeeded` 后端收到事件
5. ✅ 终端显示 `[200] POST` 成功响应

---

## 📞 下一步

配置完Stripe CLI后，我们继续配置其他部分！


