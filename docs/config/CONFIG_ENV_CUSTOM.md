# 🎯 您的专属配置文件

根据您提供的信息，我已经准备好了完整配置。请按照以下步骤操作：

---

## 第1步：创建.env文件（1分钟）

### 操作：

```powershell
# 在PowerShell中运行
cd E:\300_Code\314_POSX_Official_Sale_App
notepad .env
```

### 复制以下内容到notepad：

```bash
# ============================================
# POSX 开发环境配置
# 基于您的实际配置
# ============================================

# Django核心
SECRET_KEY=django-insecure-dev-7x9k2m5n8p1q4r6t9w2y5u8i0o3a6s9d2f5g8h1j4k7m0n3p6
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# 数据库
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# Redis（Docker）
REDIS_URL=redis://localhost:6379/0

# Auth0
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/

# SIWE钱包认证
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# Stripe（您的测试密钥）
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=
MOCK_STRIPE=false

# 订单配置
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000
ENV=dev

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 前端
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_SITE_CODES=NA,ASIA

# Fireblocks（Phase D使用）
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
```

**保存（Ctrl+S）并关闭notepad**

---

## 第2步：安装Stripe CLI（5分钟）

### Windows安装方法（选一种）

#### 方法A：Scoop（推荐）

```powershell
# 1. 安装Scoop（如未安装）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# 2. 安装Stripe CLI
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe

# 3. 验证
stripe --version
```

#### 方法B：直接下载

1. 访问：https://github.com/stripe/stripe-cli/releases/latest
2. 下载 `stripe_*_windows_x86_64.zip`
3. 解压到 `C:\stripe\`
4. 添加到PATH：
   ```powershell
   # 以管理员运行PowerShell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\stripe", "User")
   ```
5. 重启PowerShell，验证：
   ```powershell
   stripe --version
   ```

---

## 第3步：配置Stripe CLI（2分钟）

### 操作1：登录Stripe

```bash
stripe login
```

**流程**：
1. 按Enter打开浏览器
2. 确认配对码
3. 点击"Allow access"
4. 返回终端看到"Done!"

---

### 操作2：启动Webhook监听

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**输出**：
```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxx
```

**🔑 复制这个 `whsec_***` 值**

---

### 操作3：更新.env文件

```powershell
notepad .env
```

找到这一行：
```bash
STRIPE_WEBHOOK_SECRET=
```

粘贴密钥：
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
```

**保存并关闭**

---

## 第4步：启动所有服务（3分钟）

### 终端1：Redis（Docker）

```bash
# 如果Redis还未启动
docker run -d -p 6379:6379 --name posx-redis redis:alpine

# 验证
redis-cli ping
# 应该返回：PONG
```

---

### 终端2：PostgreSQL

```bash
# 确保PostgreSQL正在运行
# 创建数据库（如果还没有）
psql -U postgres
```

在psql中执行：
```sql
CREATE DATABASE posx_local;
CREATE USER posx_app WITH PASSWORD 'posx';
GRANT ALL PRIVILEGES ON DATABASE posx_local TO posx_app;
ALTER DATABASE posx_local OWNER TO posx_app;
\q
```

---

### 终端3：Stripe CLI（保持运行）

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/
```

**保持此终端运行**，您会看到webhook事件转发

---

### 终端4：Django服务器

```bash
cd E:\300_Code\314_POSX_Official_Sale_App\backend

# 安装依赖（如未安装）
pip install -r requirements/production.txt

# 运行迁移
python manage.py migrate

# 加载种子数据
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json

# 启动服务
python manage.py runserver
```

**查看启动日志**，应该看到：
```
✅ Auth0 配置已加载: Domain=dev-posx.us..., Audience=http://localhost:8000...
✅ SIWE 配置已加载: Domain=localhost, ChainID=11155111, URI=http://localhost:3000
System check identified no issues (0 silenced).
Starting development server at http://127.0.0.1:8000/
```

---

### 终端5：Celery Worker（可选）

```bash
cd E:\300_Code\314_POSX_Official_Sale_App\backend
celery -A config worker -l info
```

---

### 终端6：Celery Beat（可选）

```bash
cd E:\300_Code\314_POSX_Official_Sale_App\backend
celery -A config beat -l info
```

---

## 🧪 第5步：验证配置（2分钟）

### 测试1：健康检查

```bash
curl http://localhost:8000/health/
```

**预期**: `{"status":"healthy"}`

---

### 测试2：获取Nonce

```bash
curl -X POST http://localhost:8000/api/v1/auth/nonce -H "X-Site-Code: NA"
```

**预期**: 
```json
{
  "nonce": "很长的随机字符串",
  "expires_in": 300,
  "issued_at": "2025-11-08T..."
}
```

---

### 测试3：触发Stripe Webhook

```bash
# 在新终端运行
stripe trigger payment_intent.succeeded
```

**查看Django终端**，应该看到：
```
[webhook] Event received: payment_intent.succeeded
```

**查看Stripe CLI终端**，应该看到：
```
2025-11-08 12:00:00   <-- [200] POST http://localhost:8000/api/v1/webhooks/stripe/
```

---

## ✅ 配置完成检查清单

- [ ] .env文件已创建
- [ ] SECRET_KEY已设置
- [ ] 数据库配置正确（DB_PASSWORD）
- [ ] Redis连接成功（Docker运行）
- [ ] Auth0配置已填写
- [ ] SIWE配置已填写
- [ ] Stripe密钥已填写
- [ ] Stripe CLI已安装
- [ ] Stripe CLI已登录
- [ ] STRIPE_WEBHOOK_SECRET已设置
- [ ] Django启动成功
- [ ] 健康检查通过
- [ ] Nonce获取成功
- [ ] Stripe webhook测试通过

---

## 📊 您的配置总结

| 配置项 | 值 | 状态 |
|--------|-----|------|
| Auth0 Domain | dev-posx.us.auth0.com | ✅ |
| Auth0 Audience | http://localhost:8000/api/v1/ | ✅ |
| SIWE Domain | localhost | ✅ |
| SIWE Chain ID | 11155111（Sepolia） | ✅ |
| Stripe Mode | 真实测试密钥 | ✅ |
| Stripe CLI | 需要安装和配置 | 🔄 |
| Redis | Docker运行 | ✅ |
| 数据库 | PostgreSQL本地 | ✅ |

---

## 🆘 遇到问题？

### 如果PostgreSQL未安装

```bash
# 使用Docker运行PostgreSQL
docker run -d \
  --name posx-postgres \
  -e POSTGRES_DB=posx_local \
  -e POSTGRES_USER=posx_app \
  -e POSTGRES_PASSWORD=posx \
  -p 5432:5432 \
  postgres:15-alpine

# 验证
docker ps | findstr postgres
```

### 如果Redis未启动

```bash
# 启动Redis Docker容器
docker run -d --name posx-redis -p 6379:6379 redis:alpine

# 验证
docker ps | findstr redis
```

### 如果Stripe CLI安装失败

**备选方案**：暂时使用Mock模式

在.env中改为：
```bash
MOCK_STRIPE=true
STRIPE_WEBHOOK_SECRET=mock_secret
```

这样可以先开发测试，稍后再配置真实Stripe。

---

## 📞 现在请执行：

1. **创建.env文件** - 复制上面的配置
2. **告诉我**：
   - PostgreSQL是否已运行？
   - Redis Docker是否已运行？
   - 是否成功安装了Stripe CLI？

我会根据您的情况继续指导！ 🎯

