# ⚡ 快速环境配置（3分钟）

## 🎯 目标

完成最小可运行配置，让您能立即启动POSX进行开发测试。

---

## 📝 3步完成配置

### 第1步：生成SECRET_KEY（30秒）

```bash
# 打开PowerShell，运行：
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 复制输出结果（类似这样）：
# django-insecure-k8@#mf2!x7n9$p4q&w5e6r7t8y9u0i1o2p3a4s5d6f
```

---

### 第2步：创建.env文件（2分钟）

在项目根目录创建 `.env` 文件：

```bash
cd E:\300_Code\314_POSX_Official_Sale_App
notepad .env
```

粘贴以下内容（**替换SECRET_KEY为第1步生成的**）：

```bash
# ===== 最小配置（立即可用）=====

# [步骤1生成的] Django密钥
SECRET_KEY=<粘贴第1步生成的SECRET_KEY>

# 调试模式
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# 数据库（如果您的PostgreSQL密码不是posx，请修改DB_PASSWORD）
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# SIWE钱包认证
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# Stripe Mock模式（开发用）
MOCK_STRIPE=true

# 环境标识
ENV=dev

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 前端
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA

# 订单配置（使用默认值）
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000

# ===== 可选配置（留空）=====
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_ISSUER=
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
```

**保存文件（Ctrl+S，关闭notepad）**

---

### 第3步：验证配置（30秒）

```bash
cd backend
python check_env.py
```

**如果看到**:
```
🎉 所有检查通过！您可以开始使用POSX了。
```

**说明配置成功！** ✅

---

## 🚀 启动服务

```bash
cd backend

# 运行迁移
python manage.py migrate

# 加载种子数据
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json

# 启动Django
python manage.py runserver

# 另一个终端：启动Celery（可选）
celery -A config worker -l info
celery -A config beat -l info
```

---

## 🧪 测试配置

### 测试1: 健康检查

```bash
curl http://localhost:8000/health/
```

**预期**: `{"status":"healthy"}`

---

### 测试2: 获取Nonce

```bash
curl -X POST http://localhost:8000/api/v1/auth/nonce -H "X-Site-Code: NA"
```

**预期**: 返回nonce和expires_in

---

### 测试3: 查询档位（需要先创建档位或Auth token）

```bash
# 如果有Auth token
curl http://localhost:8000/api/v1/tiers/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Site-Code: NA"
```

---

## ⚠️ 常见问题

### 问题1: SECRET_KEY报错

**错误**: `django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty.`

**解决**: 确保.env文件中有SECRET_KEY，且已生成随机值

---

### 问题2: 数据库连接失败

**错误**: `could not connect to server`

**解决**: 
1. 检查PostgreSQL是否运行
2. 检查DB_PASSWORD是否正确
3. 检查数据库`posx_local`是否已创建

```sql
-- 如果数据库不存在，创建它：
psql -U postgres
CREATE DATABASE posx_local;
CREATE USER posx_app WITH PASSWORD 'posx';
GRANT ALL PRIVILEGES ON DATABASE posx_local TO posx_app;
```

---

### 问题3: Redis连接失败

**错误**: `Error connecting to Redis`

**解决**: 启动Redis服务

```bash
# Windows（如果安装了Redis）
redis-server

# 或者使用Docker
docker run -d -p 6379:6379 redis:alpine
```

---

### 问题4: siwe模块未找到

**错误**: `ModuleNotFoundError: No module named 'siwe'`

**解决**: 安装依赖

```bash
cd backend
pip install -r requirements/production.txt
```

---

## ✅ 配置成功标志

您应该看到：

1. ✅ `python check_env.py` 全部通过
2. ✅ `python manage.py runserver` 启动成功
3. ✅ 日志显示：`✅ SIWE 配置已加载`
4. ✅ `curl http://localhost:8000/health/` 返回healthy
5. ✅ `curl .../auth/nonce` 返回nonce

**如果都成功，配置完成！** 🎉

---

## 📞 需要帮助？

告诉我您遇到的问题：
- 哪一步卡住了？
- 看到什么错误信息？
- 需要配置哪个具体的服务？

我会提供具体的解决方案！


