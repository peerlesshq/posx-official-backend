# Railway 部署验证清单

本清单用于确保 Railway 部署完成后，所有核心功能正常运行。

---

## 📋 部署前检查

### 代码准备

- [ ] 最新代码已推送到 GitHub `main` 分支
- [ ] `backend/requirements/production.txt` 包含 `dj-database-url` 和 `whitenoise`
- [ ] `backend/config/settings/railway.py` 文件已创建
- [ ] `.gitignore` 已排除敏感文件（`.env`, `*.pyc`, `staticfiles/`等）

### 环境变量准备

- [ ] 已生成 `SECRET_KEY`（使用随机密钥生成器）
- [ ] Auth0 凭据已获取（Domain, Audience, Client ID, Secret）
- [ ] Stripe 密钥已准备（测试或生产）
- [ ] 前端域名已确认（用于 CORS 配置）

---

## 🚀 Railway 服务创建

### 1. PostgreSQL Database

- [ ] PostgreSQL Service 已创建
- [ ] 状态显示为 **Active**
- [ ] `DATABASE_URL` 已自动注入
- [ ] 可在 Data 标签中浏览数据库

**验证命令**:
```bash
# 在 Backend Shell
echo $DATABASE_URL
# 应输出: postgresql://postgres:...@host:5432/railway
```

### 2. Redis

- [ ] Redis Service 已创建
- [ ] 状态显示为 **Active**
- [ ] `REDIS_URL` 已自动注入

**验证命令**:
```bash
echo $REDIS_URL
# 应输出: redis://default:...@host:6379
```

### 3. Backend Service

- [ ] Backend Service 已创建并连接 GitHub 仓库
- [ ] Start Command 已配置：
  ```bash
  cd backend && python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2
  ```
- [ ] 所有环境变量已添加（参考 [环境变量清单](./RAILWAY_ENV_VARIABLES.md)）
- [ ] Railway 域名已生成（如 `posx-backend-prod.up.railway.app`）
- [ ] 首次部署已完成（状态为 **Success**）

### 4. Celery Worker（可选）

- [ ] Celery Worker Service 已创建
- [ ] Start Command:
  ```bash
  cd backend && celery -A config worker --loglevel=info --concurrency=2
  ```
- [ ] 环境变量已共享或复制

### 5. Celery Beat（可选）

- [ ] Celery Beat Service 已创建
- [ ] Start Command:
  ```bash
  cd backend && celery -A config beat --loglevel=info
  ```
- [ ] 确认只有一个 Beat 实例运行

---

## ✅ 部署后验证

### 1. Health Checks

#### Simple Health Check

```bash
curl https://<Railway域名>.up.railway.app/health/
```

**期望输出**:
```json
{
  "status": "healthy"
}
```

- [ ] 返回 200 状态码
- [ ] JSON 包含 `"status": "healthy"`

#### Ready Check（详细健康检查）

```bash
curl https://<Railway域名>.up.railway.app/ready/
```

**期望输出**:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "migrations": "ok",
    "rls": "ok"
  },
  "timestamp": "2025-01-11T12:00:00Z"
}
```

- [ ] 返回 200 状态码
- [ ] `database` 为 `ok`
- [ ] `redis` 为 `ok`
- [ ] `migrations` 为 `ok`
- [ ] `rls` 为 `ok` ⭐（Row Level Security）

⚠️ **如果任一检查失败**，查看 Railway 日志排查问题。

---

### 2. 数据库迁移

在 Railway Backend Service Shell 中执行：

```bash
cd backend
python manage.py showmigrations
```

**验证**:
- [ ] 所有 app 的迁移都显示 `[X]`（已应用）
- [ ] 没有显示 `[ ]`（未应用）

**关键迁移**:
```
core
 [X] 0001_initial
 [X] 0002_create_initial_schema
 [X] 0003_create_rls_indexes
 [X] 0004_enable_rls_policies ⭐
```

#### 手动执行迁移（如需要）

```bash
python manage.py migrate
```

---

### 3. Row Level Security（RLS）验证 ⭐

#### 检查 RLS 状态

```bash
cd backend
python manage.py shell
```

```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schemaname, tablename, rowsecurity 
        FROM pg_tables 
        WHERE schemaname = 'public' AND rowsecurity = true;
    """)
    tables = cursor.fetchall()
    print(f"RLS enabled tables: {len(tables)}")
    for table in tables:
        print(f"  - {table[1]}")
```

**期望输出**:
```
RLS enabled tables: 8
  - orders_order
  - tiers_tier
  - commissions_commission
  - allocations_allocation
  - agents_agent
  - sites_siteconfig
  - vesting_vestingschedule
  - vesting_vestingrelease
```

- [ ] 至少 8 张表启用了 RLS
- [ ] 包含核心表：`orders_order`, `commissions_commission`, `allocations_allocation`

---

### 4. 静态文件

#### 验证 collectstatic

```bash
cd backend
python manage.py collectstatic --noinput --dry-run
```

**期望输出**:
```
X static files copied to '/app/backend/staticfiles'.
```

- [ ] 没有错误
- [ ] 文件数量 > 0

#### 访问静态文件（可选）

```bash
curl https://<Railway域名>.up.railway.app/static/admin/css/base.css
```

- [ ] 返回 200
- [ ] 内容为 CSS 文件

---

### 5. 种子数据

#### 加载 Sites 和 Commission Plans

```bash
cd backend
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json
```

**验证**:
```bash
python manage.py shell
```

```python
from apps.sites.models import SiteConfig
from apps.commissions.models import CommissionPlan

print(f"Sites: {SiteConfig.objects.count()}")
print(f"Commission Plans: {CommissionPlan.objects.count()}")
```

**期望输出**:
```
Sites: 2
Commission Plans: 3
```

- [ ] Sites 至少 2 个（NA, ASIA）
- [ ] Commission Plans 至少 1 个

---

### 6. 创建超级用户

```bash
cd backend

# 方式 1: 交互式
python manage.py createsuperuser

# 方式 2: 非交互式
DJANGO_SUPERUSER_PASSWORD=Demo_Admin_2024! \
python manage.py createsuperuser \
  --noinput \
  --username admin \
  --email admin@posx.io
```

**验证**:
- [ ] 超级用户创建成功
- [ ] 可访问 Admin 面板：`https://<Railway域名>/admin/`
- [ ] 使用创建的凭据登录成功

---

### 7. Auth0 JWT 验证

#### 获取测试 Token

使用 Auth0 测试工具或 Postman 获取 JWT Token。

#### 测试受保护端点

```bash
curl https://<Railway域名>.up.railway.app/api/v1/test/protected/ \
  -H "Authorization: Bearer <你的JWT>"
```

**期望输出**:
```json
{
  "message": "You are authenticated!",
  "user": "auth0|xxxxx"
}
```

- [ ] 返回 200
- [ ] 包含用户信息

#### 测试公开端点

```bash
curl https://<Railway域名>.up.railway.app/api/v1/test/public/
```

**期望输出**:
```json
{
  "message": "This is a public endpoint"
}
```

- [ ] 返回 200
- [ ] 无需 Token

---

### 8. CORS 验证

```bash
curl -H "Origin: https://posx.retool.com" \
  https://<Railway域名>.up.railway.app/api/v1/test/public/ \
  -v
```

**验证响应头**:
```
< Access-Control-Allow-Origin: https://posx.retool.com
< Access-Control-Allow-Credentials: true
```

- [ ] 响应头包含 `Access-Control-Allow-Origin`
- [ ] 值匹配请求的 Origin
- [ ] 如配置了 `CORS_ALLOW_CREDENTIALS`，应包含对应头

---

### 9. CSRF 豁免验证

API 端点应豁免 CSRF 检查：

```bash
curl -X POST https://<Railway域名>.up.railway.app/api/v1/test/public/ \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

- [ ] 返回成功（不是 403 Forbidden）
- [ ] 无需 CSRF Token

---

### 10. Stripe Webhook 验证

参考 [Stripe Webhook 配置指南](./RAILWAY_STRIPE_WEBHOOK.md)。

#### 测试 Webhook 端点可访问

```bash
curl -X POST https://<Railway域名>.up.railway.app/api/v1/webhooks/stripe/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**期望输出**:
```json
{"error": "Invalid payload"}
```

- [ ] 返回 400（端点存在，但签名验证失败）

#### 在 Stripe Dashboard 发送测试 Webhook

- [ ] Webhook endpoint 已创建
- [ ] Signing secret 已配置到 Railway
- [ ] 测试 Webhook 发送成功
- [ ] Railway 日志显示接收到事件

---

### 11. Celery Worker 验证（如已部署）

#### 查看 Worker 状态

```bash
cd backend
celery -A config inspect ping
```

**期望输出**:
```json
{
  "celery@hostname": {
    "ok": "pong"
  }
}
```

- [ ] Worker 响应 `pong`

#### 测试异步任务

```python
from apps.orders.tasks import process_order

# 触发测试任务
result = process_order.delay('test-order-id')
print(f"Task ID: {result.id}")

# 查看结果
result.get(timeout=10)
```

- [ ] 任务成功执行
- [ ] 在 Celery Worker 日志中看到任务记录

---

### 12. Celery Beat 验证（如已部署）

#### 查看定时任务

```bash
cd backend
python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all()
for task in tasks:
    print(f"{task.name}: Enabled={task.enabled}, Next Run={task.schedule}")
```

- [ ] 显示预期的定时任务（如 `unlock-vesting-releases`）
- [ ] `enabled=True`

#### 查看 Beat 日志

在 Celery Beat Service → Logs 中：

```log
[INFO] Scheduler: Sending due task unlock-vesting-releases
```

- [ ] 定时任务按计划触发

---

## 🔒 安全检查

### 1. Django 配置

```bash
cd backend
python manage.py shell
```

```python
from django.conf import settings

print(f"DEBUG: {settings.DEBUG}")  # 应为 False
print(f"SECRET_KEY starts with: {settings.SECRET_KEY[:10]}")  # 不应是默认值
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"SECURE_SSL_REDIRECT: {settings.SECURE_SSL_REDIRECT}")
```

**验证**:
- [ ] `DEBUG = False` ⭐
- [ ] `SECRET_KEY` 不是默认/示例值
- [ ] `ALLOWED_HOSTS` 包含 Railway 域名
- [ ] `SECURE_SSL_REDIRECT = True`

### 2. CSP 头检查

```bash
curl -I https://<Railway域名>.up.railway.app/
```

**验证响应头**:
```
Content-Security-Policy: default-src 'none'; script-src 'self' https://js.stripe.com; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

- [ ] `Content-Security-Policy` 存在且无 `'unsafe-inline'` ⭐
- [ ] `X-Frame-Options` 为 `DENY`
- [ ] `X-Content-Type-Options` 为 `nosniff`
- [ ] `Referrer-Policy` 已设置

### 3. HTTPS 强制

```bash
curl -I http://<Railway域名>.up.railway.app/ -L
```

- [ ] 自动重定向到 `https://`
- [ ] 最终响应为 200

### 4. 敏感信息检查

```bash
curl https://<Railway域名>.up.railway.app/api/v1/test/config/
```

- [ ] 不暴露 `SECRET_KEY`
- [ ] 不暴露数据库密码
- [ ] 不暴露 API 密钥

---

## 📊 性能检查

### 1. 响应时间

```bash
curl -w "\nTime: %{time_total}s\n" https://<Railway域名>.up.railway.app/health/
```

- [ ] `/health/` 响应 < 500ms
- [ ] `/ready/` 响应 < 2s

### 2. 并发测试（可选）

使用 `ab`（Apache Bench）或 `wrk`：

```bash
ab -n 100 -c 10 https://<Railway域名>.up.railway.app/health/
```

- [ ] 95% 请求 < 1s
- [ ] 无 5xx 错误

### 3. 数据库连接池

```python
from django.db import connection

print(f"Connections: {connection.queries}")
```

- [ ] 连接池正常工作
- [ ] 无连接泄漏

---

## 📝 日志验证

### 1. Backend 日志

在 Railway Backend Service → Deployments → Logs 中：

**正常日志**:
```log
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Worker process spawned (pid: xxx)
[INFO] "GET /health/ HTTP/1.1" 200
```

- [ ] 无 `[ERROR]` 日志
- [ ] Gunicorn 成功启动
- [ ] 请求正常处理

### 2. Celery Worker 日志

```log
[INFO] celery@hostname ready.
[INFO] Task apps.orders.tasks.process_order[...] succeeded in 0.123s
```

- [ ] Worker 启动成功
- [ ] 任务成功执行

### 3. Celery Beat 日志

```log
[INFO] Scheduler: Sending due task unlock-vesting-releases
```

- [ ] 定时任务按计划触发

---

## 🎯 功能端到端测试

### 1. 创建订单流程

1. **创建订单**（通过 API 或 Retool）:
   ```bash
   curl -X POST https://<Railway域名>/api/v1/orders/ \
     -H "Authorization: Bearer <Token>" \
     -H "X-Site-Code: NA" \
     -d '{"tier_id": "...", "quantity": 1, ...}'
   ```

2. **支付**（使用 Stripe 测试卡 `4242 4242 4242 4242`）

3. **验证订单状态**:
   ```bash
   curl https://<Railway域名>/api/v1/orders/<order_id>/ \
     -H "Authorization: Bearer <Token>"
   ```

**期望**:
- [ ] 订单创建成功（状态 `pending`）
- [ ] 支付后订单更新为 `paid`
- [ ] Webhook 日志显示接收 `payment_intent.succeeded`
- [ ] 代币分配任务已触发
- [ ] 佣金计算任务已触发

### 2. Retool 对接测试（如适用）

- [ ] Retool 可连接 Railway API
- [ ] 可查询订单列表
- [ ] 可查看订单详情
- [ ] 可执行管理操作（如审批佣金）

---

## 🚨 回滚计划

如果验证失败，记录回滚步骤：

### 1. 暂时禁用服务

在 Railway Service → Settings → **Pause Service**

### 2. 恢复数据库快照（如需要）

在 PostgreSQL Service → Data → Backups → **Restore**

### 3. 回滚代码

```bash
git revert <commit-hash>
git push origin main
```

Railway 自动重新部署。

---

## ✅ 部署完成确认

所有检查通过后，填写以下信息：

| 项目 | 值 |
|------|-----|
| **Railway 项目名称** | posx-demo |
| **Backend 域名** | https://posx-backend-prod.up.railway.app |
| **部署时间** | 2025-01-11 12:00 UTC |
| **部署人员** | @your-name |
| **Django 版本** | 4.2.7 |
| **Python 版本** | 3.11 |
| **数据库版本** | PostgreSQL 15 |
| **Redis 版本** | Redis 7 |

### 最终确认

- [ ] 所有 Health Checks 通过
- [ ] RLS 策略全部启用
- [ ] Stripe Webhook 配置完成
- [ ] Auth0 JWT 验证通过
- [ ] 端到端订单流程测试通过
- [ ] 日志无异常错误
- [ ] 安全检查全部通过
- [ ] 性能满足要求
- [ ] 文档已更新（如有新配置）

---

## 📚 相关文档

- [Railway 部署指南](./RAILWAY_DEPLOYMENT_GUIDE.md)
- [环境变量配置](./RAILWAY_ENV_VARIABLES.md)
- [Stripe Webhook 配置](./RAILWAY_STRIPE_WEBHOOK.md)
- [服务配置详解](./RAILWAY_SERVICE_CONFIGURATION.md)
- [Production Checklist](../../PRODUCTION_CHECKLIST.md)

---

**创建时间**: 2025-01-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

