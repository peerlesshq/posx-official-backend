# POSX Framework v1.0.0 - Production Baseline

**Release Date**: 2025-11-07  
**Status**: Production Ready ✅  
**Code Name**: Foundation

---

## 🎯 上线前核对清单（6 条必检）⭐

### ✅ 1. RLS 迁移检查

**文件**: `backend/apps/core/migrations/0003_create_rls_indexes.py`

- [x] `atomic = False`（支持 CONCURRENTLY）
- [x] 所有必需索引已创建
- [x] `allocations(fireblocks_tx_id)` 唯一索引

**文件**: `backend/apps/core/migrations/0004_enable_rls_policies.py`

- [x] 包含 `FORCE ROW LEVEL SECURITY`
- [x] UUID 比较（`::uuid`）
- [x] allocations 表纳入 RLS
- [x] admin 只读策略（`FOR SELECT TO posx_admin USING (true)`）
- [x] `search_path` 固定（`ALTER ROLE SET search_path = public`）
- [x] `site_id` 不可变触发器（`forbid_site_change()`）
- [x] 默认权限（`ALTER DEFAULT PRIVILEGES`）
- [x] 完整的 `reverse_sql`

**验证命令**:
```bash
# 检查 RLS 状态
psql -c "SELECT tablename, rowsecurity FROM pg_tables WHERE tablename IN ('orders', 'tiers', 'commissions', 'allocations');"

# 检查策略
psql -c "SELECT schemaname, tablename, policyname FROM pg_policies WHERE tablename IN ('orders', 'tiers');"

# 检查触发器
psql -c "SELECT trigger_name, event_manipulation, event_object_table FROM information_schema.triggers WHERE trigger_name LIKE '%siteid%';"
```

---

### ✅ 2. 生产 CSP 检查

**文件**: `backend/config/settings/production.py`

- [x] **无** `'unsafe-inline'`
- [x] 必要域名已白名单（`js.stripe.com`、CDN）
- [x] `CSP_FRAME_ANCESTORS = ("'none'",)`（防嵌套）
- [x] `CSP_OBJECT_SRC = ("'none'",)`
- [x] `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'`

**验证命令**:
```bash
# 检查 CSP 配置
grep -n "unsafe-inline" backend/config/settings/production.py
# 应该返回空（或仅在注释中）

# 启动服务后检查响应头
curl -I https://yourdomain.com | grep -i "content-security-policy"
```

---

### ✅ 3. CSRF 与 API 路由一致性

**文件**: `backend/config/middleware/csrf_exempt.py`

- [x] `CSRFExemptMiddleware` 存在
- [x] 在 `CsrfViewMiddleware` **之前**

**文件**: `backend/config/settings/base.py`

- [x] `CSRF_EXEMPT_PATHS` 包含 `/api/v1/`、`/health/`、`/ready/`

**验证**:
```bash
# 检查中间件顺序
grep -A 20 "MIDDLEWARE = " backend/config/settings/base.py | grep -n csrf

# 测试 API 无需 CSRF
curl -X POST http://localhost:8000/api/v1/auth/nonce -d '{"wallet_address":"0x..."}' -H "Content-Type: application/json"
# 应该成功（不返回 403 CSRF failed）
```

---

### ✅ 4. 运行时入口与服务器

**文件**: `backend/config/wsgi.py`

- [x] 存在并正确配置

**文件**: `backend/config/celery.py`

- [x] `autodiscover_tasks()` 已调用

**文件**: `backend/config/__init__.py`

- [x] 导入 `celery_app`

**文件**: `docker-compose.prod.yml`

- [x] Backend 使用 `gunicorn config.wsgi:application`

**验证**:
```bash
# 测试 Celery 任务发现
python manage.py shell -c "from config import celery_app; print(celery_app.tasks)"

# 测试 Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --check-config
```

---

### ✅ 5. 生产 Compose 与静态资源

**文件**: `docker-compose.prod.yml`

- [x] Backend service 包含 `collectstatic --noinput`
- [x] 静态文件卷（`static_volume`）
- [x] Nginx 挂载静态文件卷（只读）

**验证**:
```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 检查静态文件
docker exec posx-backend ls -la /var/www/static/

# 测试静态文件访问
curl -I https://yourdomain.com/static/admin/css/base.css
# 应该返回 200
```

---

### ✅ 6. 健康/就绪端点健壮性

**文件**: `backend/apps/core/views/health.py`

- [x] 正确导入 `timezone`、`cache`、`MigrationExecutor`
- [x] 异常路径返回 **503**（不是 500）
- [x] 检查 DB、Redis、迁移、RLS

**验证**:
```bash
# 测试健康检查
curl http://localhost:8000/health/
# 应该返回 200 + JSON

# 测试就绪检查
curl -i http://localhost:8000/ready/
# 所有正常：返回 200
# 任何检查失败：返回 503

# 模拟 DB 故障
docker-compose stop postgres
curl -i http://localhost:8000/ready/
# 应该返回 503（不是 500）
```

---

## 🚀 快速开始

### 前置条件

- Docker 20.10+
- Docker Compose 2.0+
- 生产环境密钥（Auth0、Stripe、Fireblocks）

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url>
cd posx-framework-v1.0

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入开发环境密钥

# 3. 启动服务
docker-compose up -d

# 4. 运行迁移
docker-compose exec backend python manage.py migrate

# 5. 创建超级用户
docker-compose exec backend python manage.py createsuperuser

# 6. 访问
# - Backend: http://localhost:8000
# - Health: http://localhost:8000/health/
# - Ready: http://localhost:8000/ready/
# - Admin: http://localhost:8000/admin/
```

### 生产部署

```bash
# 1. 准备环境变量
cp .env.production.example .env.production
# 填入生产密钥

# 2. 构建镜像
docker-compose -f docker-compose.prod.yml build

# 3. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 4. 检查健康状态
curl https://yourdomain.com/ready/

# 5. 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 📁 项目结构

```
posx-framework-v1.0/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py           # 基础配置
│   │   │   ├── local.py          # 本地开发
│   │   │   ├── demo.py           # 演示环境
│   │   │   └── production.py    # ⭐ 生产配置（CSP 严格）
│   │   ├── middleware/
│   │   │   └── csrf_exempt.py   # ⭐ CSRF 豁免中间件
│   │   ├── wsgi.py              # ⭐ WSGI 配置
│   │   ├── celery.py            # ⭐ Celery 配置
│   │   └── urls.py              # URL 路由
│   ├── apps/
│   │   └── core/
│   │       ├── migrations/
│   │       │   ├── 0003_create_rls_indexes.py    # ⭐ RLS 索引
│   │       │   └── 0004_enable_rls_policies.py   # ⭐ RLS 策略
│   │       └── views/
│   │           └── health.py    # ⭐ 健康检查
│   ├── requirements/
│   │   └── production.txt       # 生产依赖
│   └── Dockerfile.prod          # 生产 Dockerfile
├── docker-compose.prod.yml      # ⭐ 生产 Compose
└── VERSION                      # 版本信息
```

---

## 🔒 安全特性

### 1. Row Level Security (RLS)
- ✅ FORCE enforcement（超级用户也受限）
- ✅ UUID 比较（类型安全）
- ✅ Admin 只读跨站（SELECT only）
- ✅ site_id 不可变（触发器保护）

### 2. CSP 严格模式
- ✅ 无 `unsafe-inline`（生产）
- ✅ Frame ancestors 阻止嵌套
- ✅ Object/embed 禁用
- ✅ Referrer Policy 严格

### 3. CSRF 智能豁免
- ✅ API endpoints 豁免
- ✅ 健康检查豁免
- ✅ Webhook 豁免

### 4. 其他安全措施
- ✅ HTTPS 强制
- ✅ HSTS (1 year)
- ✅ Secure cookies
- ✅ X-Frame-Options: DENY

---

## 📊 监控与日志

### 健康检查端点

- `/health/` - 简单健康检查（200 OK）
- `/ready/` - 详细就绪检查（检查 DB/Redis/迁移/RLS）
- `/version/` - 版本信息

### 日志级别

- **生产**: WARNING
- **Demo**: INFO
- **本地**: DEBUG

### 集成监控（可选）

- **Sentry**: 错误追踪
- **Prometheus**: 指标收集
- **Grafana**: 可视化

---

## 🛠️ 故障排查

### CSP 阻止脚本

**症状**: 浏览器控制台 CSP 错误

**解决**:
```python
# 开发环境：使用 config.settings.local（有 unsafe-inline）
# 生产环境：将脚本外链或使用 nonce
```

### 迁移失败

**症状**: `python manage.py migrate` 报错

**解决**:
```bash
# 查看详细错误
python manage.py migrate --verbosity 2

# 检查索引创建（CONCURRENTLY 需要非事务）
python manage.py sqlmigrate core 0003
```

### CSRF 验证失败

**症状**: API 返回 403 Forbidden

**解决**:
```bash
# 检查中间件顺序
grep -A 5 "CSRFExemptMiddleware" backend/config/settings/base.py

# 确认路径在豁免列表
grep "CSRF_EXEMPT_PATHS" backend/config/settings/base.py
```

---

## 📚 相关文档

- **[POSX_System_Specification_v1.0.0.md](POSX_System_Specification_v1.0.0.md)** - 完整系统规范
- **[POSX_System_Specification_v1.0.4_RLS_Production.md](POSX_System_Specification_v1.0.4_RLS_Production.md)** - RLS 生产级规范

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2025-11-07 | 首个生产版本（完整的 RLS + 安全加固） |

---

## 🙏 致谢

POSX Framework v1.0.0 - 生产就绪的多站点代币预售平台

**Production Ready** ✅ | **Security Hardened** 🔒 | **RLS Enabled** 🛡️

---

**下一步**: 立即部署！🚀
