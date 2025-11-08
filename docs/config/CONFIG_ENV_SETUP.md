# 🎯 POSX 环境配置完整指南

## ✅ 当前状态

1. ✅ Stripe CLI 已安装并配置到PATH
2. ✅ Redis 使用Docker（已运行）
3. ✅ 所有配置信息已收集

---

## 📋 配置步骤（按顺序执行）

### 步骤1：生成 Django SECRET_KEY

**在PowerShell中运行：**

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**复制输出的密钥**（类似：`django-insecure-xxx...`）

---

### 步骤2：创建 .env 文件

**方法1：使用模板（推荐）**

```powershell
# 复制模板文件
Copy-Item .env.template .env

# 编辑.env文件
notepad .env
```

**方法2：手动创建**

```powershell
notepad .env
```

然后复制以下内容（**记得替换SECRET_KEY**）：

```bash
# Django核心配置
SECRET_KEY=<粘贴步骤1生成的密钥>
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# 数据库配置
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# Redis配置（Docker）
REDIS_URL=redis://localhost:6379/0

# Auth0配置
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/

# SIWE配置
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# Stripe配置
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=
MOCK_STRIPE=false

# 订单配置
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false

# 前端配置
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA
WALLETCONNECT_PROJECT_ID=cbc675a7819dd3d4bcc1c8c75bc16d86
```

**保存并关闭notepad**

---

### 步骤3：登录 Stripe CLI

**在PowerShell中运行：**

```powershell
stripe login
```

**操作流程：**
1. 按 `Enter` 打开浏览器
2. 登录您的Stripe账号
3. 确认配对码
4. 点击 "Allow access"

**预期输出：**
```
Done! The Stripe CLI is configured for [您的账号] with account id acct_***
```

---

### 步骤4：启动 Stripe Webhook 监听

**⚠️ 重要：保持这个终端窗口打开！**

**在PowerShell中运行：**

```powershell
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**预期输出：**
```
> Ready! You are using Stripe API Version [2024-XX-XX]. 
> Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxx (^C to quit)
```

**🔑 关键：复制 `whsec_***` 这个密钥！**

---

### 步骤5：配置 Webhook Secret

**打开 `.env` 文件：**

```powershell
notepad .env
```

**找到这一行：**
```bash
STRIPE_WEBHOOK_SECRET=
```

**替换为：**
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
```

**⚠️ 将 `whsec_xxxxxxxxxxxxxxxxxxxx` 替换为步骤4中复制的实际密钥！**

**保存并关闭notepad**

---

### 步骤6：验证配置

**在PowerShell中运行：**

```powershell
cd backend
python check_env.py
```

**预期输出：**
```
✅ 所有检查通过！您可以开始使用POSX了。
```

**如果看到错误，请根据提示修复。**

---

### 步骤7：测试 Stripe Webhook（可选）

**保持步骤4的监听窗口运行**

**打开新的PowerShell窗口，启动Django：**

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend
python manage.py runserver
```

**再打开一个PowerShell窗口，触发测试事件：**

```powershell
stripe trigger payment_intent.succeeded
```

**预期结果：**
- Stripe CLI窗口显示：`[200] POST http://localhost:8000/api/v1/webhooks/stripe/`
- Django窗口显示：`[webhook] Event received: payment_intent.succeeded`

**✅ 如果看到这些，说明配置成功！**

---

## 📊 配置检查清单

完成所有步骤后，确认：

- [ ] `.env`文件已创建
- [ ] `SECRET_KEY`已生成并配置
- [ ] Stripe CLI已登录（`stripe login`）
- [ ] Webhook监听正在运行（`stripe listen`）
- [ ] `STRIPE_WEBHOOK_SECRET`已填入实际值
- [ ] `check_env.py`检查通过
- [ ] 数据库连接正常（如果已创建数据库）
- [ ] Redis连接正常（Docker已运行）

---

## 🎯 快速命令参考

```powershell
# 生成SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 创建.env（从模板）
Copy-Item .env.template .env

# 登录Stripe
stripe login

# 启动webhook监听
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/

# 验证配置
cd backend
python check_env.py

# 启动Django
python manage.py runserver

# 触发测试事件
stripe trigger payment_intent.succeeded
```

---

## 🆘 常见问题

### Q: stripe命令找不到？
**A:** 重新打开PowerShell窗口，PATH需要重启才能生效。

### Q: 数据库连接失败？
**A:** 
1. 确认PostgreSQL服务运行
2. 确认数据库已创建：`createdb posx_local`
3. 确认用户和密码正确

### Q: Redis连接失败？
**A:** 
1. 确认Docker中的Redis容器运行：`docker ps`
2. 确认端口6379未被占用

### Q: Webhook未收到事件？
**A:** 
1. 确认Django运行在8000端口
2. 确认监听命令正在运行
3. 检查路由是否正确

---

## 📞 下一步

配置完成后，您可以：

1. 运行数据库迁移：`python manage.py migrate`
2. 创建初始数据：`python manage.py loaddata fixtures/seed_sites.json`
3. 启动开发服务器：`python manage.py runserver`
4. 开始开发！

---

## 📚 参考文档

- `STRIPE_CONFIG_COMPLETE.md` - Stripe CLI详细配置
- `ENVIRONMENT_SETUP_GUIDE.md` - 完整环境配置指南
- `backend/ENV_SETUP_WIZARD.md` - 交互式配置向导

