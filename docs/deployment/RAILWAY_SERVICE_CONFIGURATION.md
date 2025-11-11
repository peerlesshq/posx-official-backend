# Railway 服务配置详解

本文档详细说明如何在 Railway 中配置多个服务，包括 Backend、PostgreSQL、Redis、Celery Worker 和 Beat。

---

## 架构概览

```
┌─────────────────────────────────────────────┐
│           Railway Project                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐     ┌──────────────┐    │
│  │  PostgreSQL  │────▶│   Backend    │    │
│  │   Database   │     │   (Django)   │    │
│  └──────────────┘     └──────────────┘    │
│                              │              │
│  ┌──────────────┐           │              │
│  │    Redis     │◀──────────┤              │
│  │              │            │              │
│  └──────────────┘            │              │
│         │                    │              │
│         ├────────────────────┤              │
│         │                    │              │
│  ┌──────▼──────┐      ┌─────▼──────┐      │
│  │Celery Worker│      │Celery Beat │      │
│  │  (异步任务)  │      │  (定时任务) │      │
│  └─────────────┘      └────────────┘      │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Service 1: PostgreSQL Database

### 创建步骤

1. 在 Railway 项目页面，点击 **+ New**
2. 选择 **Database → PostgreSQL**
3. Railway 自动创建并配置

### 自动注入的变量

Railway 会自动在所有 Service 中注入以下变量：

```bash
DATABASE_URL=postgresql://postgres:password@host:5432/railway
PGHOST=host.railway.internal
PGPORT=5432
PGUSER=postgres
PGPASSWORD=<自动生成>
PGDATABASE=railway
```

### 配置选项

| 设置项 | 推荐值 | 说明 |
|--------|--------|------|
| **Instance Type** | Shared | Demo 环境使用 Shared，生产用 Dedicated |
| **Storage** | 1GB | 自动扩展 |
| **Backups** | 启用 | 自动每日备份 |

### 数据库管理

#### 连接数据库

1. **Railway 内置客户端**：
   - PostgreSQL Service → **Data** 标签
   - 浏览表、执行 SQL

2. **外部客户端（DBeaver/pgAdmin）**：
   ```bash
   # 在 PostgreSQL Service → Connect 获取连接信息
   Host: <public-host>.railway.app
   Port: <random-port>
   Database: railway
   User: postgres
   Password: <查看 Variables>
   ```

#### 执行 SQL

```sql
-- 检查 RLS 状态
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND rowsecurity = true;

-- 查看迁移记录
SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 10;
```

---

## Service 2: Redis

### 创建步骤

1. 点击 **+ New → Database → Redis**
2. Railway 自动配置

### 自动注入的变量

```bash
REDIS_URL=redis://default:password@host:6379
REDIS_HOST=host.railway.internal
REDIS_PORT=6379
REDIS_PASSWORD=<自动生成>
```

### 配置选项

| 设置项 | 推荐值 | 说明 |
|--------|--------|------|
| **Memory Limit** | 256MB | Demo 环境足够 |
| **Eviction Policy** | `allkeys-lru` | 内存满时删除最少使用的键 |

### Redis 管理

#### 连接 Redis

```bash
# 使用 redis-cli（在 Backend Service Shell）
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD

# 测试连接
> PING
PONG

# 查看所有键
> KEYS *

# 查看 Celery 任务队列
> LLEN celery
```

#### 清空 Redis（谨慎）

```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD FLUSHALL
```

---

## Service 3: Backend (Django)

### 创建步骤

1. 点击 **+ New → GitHub Repo**
2. 选择 `posx-official-backend` 仓库
3. Railway 自动检测并创建 Service

### 构建配置

#### Settings → Build

| 设置项 | 配置 |
|--------|------|
| **Builder** | Nixpacks（默认） |
| **Root Directory** | `/` 或 `/backend` |
| **Watch Paths** | `backend/**` |

#### 自定义构建命令（可选）

如果需要自定义构建：

**Build Command**:
```bash
pip install --upgrade pip && pip install -r backend/requirements/production.txt
```

**Install Command**:
```bash
# 留空，使用默认
```

### 启动配置

#### Settings → Deploy

**Start Command**:
```bash
cd backend && python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --threads $THREADS --timeout 60 --access-logfile - --error-logfile -
```

**环境变量**（Settings → Variables）:
```bash
WEB_CONCURRENCY=2
THREADS=2
```

#### Gunicorn 配置说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--workers` | `2` | 工作进程数（推荐：CPU核心数 × 2 + 1） |
| `--threads` | `2` | 每个 worker 的线程数 |
| `--timeout` | `60` | 请求超时（秒） |
| `--bind` | `0.0.0.0:$PORT` | 监听地址（Railway 自动注入 `$PORT`） |
| `--access-logfile` | `-` | 访问日志输出到 stdout |
| `--error-logfile` | `-` | 错误日志输出到 stderr |

### 健康检查

Railway 自动配置健康检查：

- **Path**: `/health/`
- **Interval**: 30 秒
- **Timeout**: 10 秒
- **Success Threshold**: 3 次成功
- **Failure Threshold**: 3 次失败

### 域名配置

#### 生成 Railway 域名

1. Backend Service → **Settings → Networking**
2. 点击 **Generate Domain**
3. 复制域名（形如 `posx-backend-production.up.railway.app`）

#### 添加自定义域名

1. 点击 **Custom Domain**
2. 输入 `demo-api.posx.io`
3. Railway 提供 CNAME 记录：
   ```
   demo-api.posx.io -> <target>.railway.app
   ```
4. 在 DNS 提供商添加 CNAME
5. 等待 SSL 证书签发（5-10 分钟）

### 资源限制

| 资源 | Hobby Plan | Pro Plan |
|------|------------|----------|
| **Memory** | 512MB | 8GB |
| **CPU** | 共享 | 独占 |
| **Disk** | 临时存储 | 可添加 Volume |

---

## Service 4: Celery Worker

### 创建步骤

1. 点击 **+ New → Empty Service**
2. **Service Name**: `celery-worker`
3. 连接相同的 GitHub 仓库

### 构建配置

与 Backend Service 共享构建配置。

### 启动配置

**Start Command**:
```bash
cd backend && celery -A config worker --loglevel=info --concurrency=2 --max-tasks-per-child=100
```

#### Celery Worker 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `-A config` | - | 指定 Celery App 路径 |
| `--loglevel` | `info` | 日志级别（debug/info/warning/error） |
| `--concurrency` | `2` | 并发 worker 数量 |
| `--max-tasks-per-child` | `100` | 每个 worker 处理任务后重启（防止内存泄漏） |

### 环境变量

复制 Backend Service 的所有环境变量，或使用 **Shared Variables**（推荐）。

**关键变量**:
```bash
DJANGO_SETTINGS_MODULE=config.settings.railway
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
```

### 监控 Worker

#### 查看日志

```bash
# 在 Railway Dashboard
Celery Worker Service → Deployments → Logs
```

#### 查看任务队列

```bash
# 在 Backend Shell
cd backend
celery -A config inspect active
celery -A config inspect stats
```

---

## Service 5: Celery Beat

### 创建步骤

1. 点击 **+ New → Empty Service**
2. **Service Name**: `celery-beat`
3. 连接相同的 GitHub 仓库

### 启动配置

**Start Command**:
```bash
cd backend && celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

#### Celery Beat 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `-A config` | - | 指定 Celery App 路径 |
| `--loglevel` | `info` | 日志级别 |
| `--scheduler` | `DatabaseScheduler` | 使用数据库存储定时任务 |

⚠️ **注意**: Celery Beat 只能有一个实例运行，否则会重复执行任务。

### 定时任务配置

在 `backend/config/settings/base.py` 中已配置：

```python
CELERY_BEAT_SCHEDULE = {
    'unlock-vesting-releases': {
        'task': 'apps.vesting.tasks.unlock_vesting_releases',
        'schedule': crontab(hour=0, minute=0),  # 每天0点
    },
    'reconcile-stuck-releases': {
        'task': 'apps.vesting.tasks.reconcile_stuck_releases',
        'schedule': crontab(minute='*/5'),  # 每5分钟
    },
    'cleanup-old-idempotency-keys': {
        'task': 'apps.vesting.tasks.cleanup_old_idempotency_keys',
        'schedule': crontab(hour=2, minute=0),  # 每天2点
    },
}
```

### 查看定时任务

```bash
# 在 Backend Shell
cd backend
python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# 查看所有定时任务
for task in PeriodicTask.objects.all():
    print(f"{task.name}: {task.crontab}")
```

---

## 服务依赖关系

### 启动顺序

Railway 支持健康检查依赖：

```yaml
# 伪代码示例（Railway 自动处理）
Backend:
  depends_on:
    - PostgreSQL (healthy)
    - Redis (healthy)

Celery Worker:
  depends_on:
    - Backend (started)
    - Redis (healthy)

Celery Beat:
  depends_on:
    - Backend (started)
    - Redis (healthy)
```

### 配置依赖（可选）

如果需要显式配置：

1. Backend Service → **Settings → Deployments**
2. **Wait for Services**: 选择 PostgreSQL 和 Redis
3. Railway 会等待依赖服务健康后再启动

---

## Shared Variables（推荐）

### 创建共享变量

1. 项目根级别 → **Shared Variables**
2. 添加所有 Service 通用的变量：
   ```bash
   DJANGO_SETTINGS_MODULE=config.settings.railway
   SECRET_KEY=<共享密钥>
   AUTH0_DOMAIN=dev-posx.us.auth0.com
   # ... 其他共享变量
   ```

### 引用共享变量

在各 Service 的 Variables 中：

```bash
# Backend Service
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Celery Worker Service
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
```

---

## 资源优化

### Hobby Plan（免费/个人）

| Service | Workers | Threads | Memory |
|---------|---------|---------|--------|
| Backend | 2 | 2 | 512MB |
| Celery Worker | 2 | - | 512MB |
| Celery Beat | 1 | - | 256MB |

### Pro Plan（生产）

| Service | Workers | Threads | Memory |
|---------|---------|---------|--------|
| Backend | 4 | 4 | 2GB |
| Celery Worker | 4 | - | 1GB |
| Celery Beat | 1 | - | 512MB |

### 调整策略

#### 降低资源消耗

```bash
# Backend
WEB_CONCURRENCY=1
THREADS=2

# Celery Worker
celery -A config worker --concurrency=1
```

#### 提高性能

```bash
# Backend
WEB_CONCURRENCY=4
THREADS=4
GUNICORN_TIMEOUT=120

# Celery Worker
celery -A config worker --concurrency=4 --prefetch-multiplier=2
```

---

## 监控与日志

### Railway 日志

#### 实时日志

```bash
# 在 Railway Dashboard
Service → Deployments → 最新部署 → Logs
```

#### 过滤日志

- 搜索框支持关键词过滤
- 按时间范围筛选
- 按日志级别筛选（INFO/WARNING/ERROR）

### 关键日志位置

| Service | 关键日志 |
|---------|----------|
| Backend | `[INFO] Received Stripe webhook`, `[ERROR] Database connection failed` |
| Celery Worker | `[INFO] Task apps.orders.tasks.process_order[...] succeeded` |
| Celery Beat | `[INFO] Scheduler: Sending due task unlock-vesting-releases` |

### 日志导出（可选）

Railway Pro Plan 支持日志导出到：
- **Datadog**
- **Logtail**
- **Papertrail**

---

## 故障排查

### Backend 启动失败

**症状**: Service 状态为 `Crashed`  
**排查步骤**:

1. 查看日志：Deployments → Logs
2. 常见错误：
   - `ModuleNotFoundError`: 依赖缺失 → 检查 `requirements/production.txt`
   - `django.db.utils.OperationalError`: 数据库连接失败 → 检查 `DATABASE_URL`
   - `CSRF verification failed`: CSRF 配置错误 → 检查 `CSRF_TRUSTED_ORIGINS`

### Celery Worker 无任务执行

**症状**: 任务一直 `PENDING` 状态  
**排查步骤**:

1. 检查 Worker 是否运行：
   ```bash
   cd backend
   celery -A config inspect ping
   ```

2. 检查 Broker 连接：
   ```bash
   redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD LLEN celery
   ```

3. 查看 Worker 日志：
   ```
   [ERROR] Cannot connect to redis://...
   ```

### Celery Beat 重复执行任务

**症状**: 同一任务被执行多次  
**原因**: 运行了多个 Beat 实例  
**解决**:

1. 确保只有一个 Beat Service
2. 停止所有 Beat 实例
3. 启动单个 Beat

---

## 最佳实践

### 1. 使用 Health Checks

确保所有 Service 配置健康检查：

```python
# backend/apps/core/views/health.py
@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'healthy'})
```

### 2. 启用自动部署

Settings → GitHub → **Auto Deploy**: `main` 分支

### 3. 配置部署通知

Settings → Notifications → 添加 Slack/Discord Webhook

### 4. 使用环境隔离

创建多个 Railway 项目：
- `posx-demo`（Demo 环境）
- `posx-staging`（Staging 环境）
- `posx-production`（生产环境）

### 5. 定期备份

- PostgreSQL: 启用自动备份
- Redis: 定期导出快照（如需持久化）

---

## 相关文档

- [Railway 部署指南](./RAILWAY_DEPLOYMENT_GUIDE.md)
- [环境变量配置](./RAILWAY_ENV_VARIABLES.md)
- [部署验证清单](./RAILWAY_DEPLOYMENT_CHECKLIST.md)

---

**创建时间**: 2025-01-11  
**维护者**: POSX DevOps Team  
**版本**: v1.0.0

