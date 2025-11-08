# 🚀 POSX v1.0 上线前检查清单

**版本**: v1.0.0  
**检查日期**: _________  
**检查人**: _________  

---

## ✅ 核心检查点（6 条必检）⭐

### 1️⃣ RLS 迁移

#### `0003_create_rls_indexes.py`

- [ ] `atomic = False`（支持 CONCURRENTLY）
- [ ] 所有必需索引已创建：
  - [ ] `idx_orders_site`
  - [ ] `idx_orders_pk_site`
  - [ ] `idx_comm_site_order`
  - [ ] `idx_tiers_site_act`
  - [ ] `idx_alloc_site_order`
  - [ ] `uq_alloc_fireblocks_tx` (UNIQUE)
  - [ ] `idx_comm_configs_site`

**验证命令**:
```bash
python manage.py sqlmigrate core 0003
```

#### `0004_enable_rls_policies.py`

- [ ] 包含 `FORCE ROW LEVEL SECURITY`
- [ ] UUID 比较（`::uuid`）
- [ ] allocations 表纳入 RLS
- [ ] admin 只读策略（7 个表）
- [ ] `search_path` 固定
- [ ] `site_id` 不可变触发器
- [ ] 默认权限（`ALTER DEFAULT PRIVILEGES`）
- [ ] 完整的 `reverse_sql`

**验证命令**:
```bash
# 检查 RLS 状态
psql -c "SELECT tablename, rowsecurity FROM pg_tables WHERE tablename IN ('orders', 'tiers', 'commissions', 'allocations');"

# 检查策略
psql -c "SELECT schemaname, tablename, policyname FROM pg_policies WHERE tablename = 'orders';"

# 检查触发器
psql -c "SELECT trigger_name FROM information_schema.triggers WHERE trigger_name LIKE '%siteid%';"

# 检查默认权限
psql -c "SELECT defaclobjtype, defaclrole::regrole FROM pg_default_acl;"
```

---

### 2️⃣ 生产 CSP

#### `config/settings/production.py`

- [ ] **无** `'unsafe-inline'` 在 `CSP_SCRIPT_SRC`
- [ ] **无** `'unsafe-inline'` 在 `CSP_STYLE_SRC`
- [ ] **无** `'unsafe-eval'`
- [ ] 必要域名已白名单：
  - [ ] `js.stripe.com`
  - [ ] CDN 域名（如有）
- [ ] 额外安全头：
  - [ ] `CSP_FRAME_ANCESTORS = ("'none'",)`
  - [ ] `CSP_OBJECT_SRC = ("'none'",)`
  - [ ] `CSP_BASE_URI = ("'self'",)`
  - [ ] `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'`

**验证命令**:
```bash
# 检查配置文件
grep -n "unsafe-inline" backend/config/settings/production.py
# 应该返回空

# 生产环境检查响应头
curl -I https://yourdomain.com | grep -i "content-security-policy"
```

---

### 3️⃣ CSRF 与 API 路由一致性

#### `config/middleware/csrf_exempt.py`

- [ ] 文件存在
- [ ] `CSRFExemptMiddleware` 类实现正确

#### `config/settings/base.py`

- [ ] `MIDDLEWARE` 中 `CSRFExemptMiddleware` 在 `CsrfViewMiddleware` **之前**
- [ ] `CSRF_EXEMPT_PATHS` 包含：
  - [ ] `/api/v1/`
  - [ ] `/health/`
  - [ ] `/ready/`
  - [ ] `/version/`
  - [ ] `/api/v1/webhooks/`

**验证命令**:
```bash
# 检查中间件顺序
grep -A 30 "MIDDLEWARE = " backend/config/settings/base.py | grep -n csrf

# 测试 API 无需 CSRF
curl -X POST http://localhost:8000/api/v1/auth/nonce \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}'
# 应该返回 200 或 400（业务错误），不应该是 403 CSRF
```

---

### 4️⃣ 运行时入口与服务器

#### WSGI 配置

- [ ] `config/wsgi.py` 存在
- [ ] `WSGI_APPLICATION = 'config.wsgi.application'` 在 settings

#### Celery 配置

- [ ] `config/celery.py` 存在
- [ ] `autodiscover_tasks()` 已调用
- [ ] `config/__init__.py` 导入 `celery_app`

#### Docker Compose

- [ ] Backend 使用 `gunicorn config.wsgi:application`
- [ ] 不使用 `uvicorn` （除非需要 ASGI）

**验证命令**:
```bash
# 测试 Celery 任务发现
python manage.py shell -c "from config import celery_app; print(celery_app.tasks.keys())"

# 测试 Gunicorn 配置
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --check-config
```

---

### 5️⃣ 生产 Compose 与静态资源

#### `docker-compose.prod.yml`

- [ ] Backend command 包含 `collectstatic --noinput`
- [ ] 静态文件卷（`static_volume`）已定义
- [ ] 媒体文件卷（`media_volume`）已定义
- [ ] Nginx 挂载静态文件卷（只读）

**验证命令**:
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

### 6️⃣ 健康/就绪端点健壮性

#### `apps/core/views/health.py`

- [ ] 正确导入：
  - [ ] `from django.utils import timezone`
  - [ ] `from django.core.cache import cache`
  - [ ] `from django.db.migrations.executor import MigrationExecutor`
- [ ] 异常路径返回 **503**（不是 500）
- [ ] 检查项：
  - [ ] 数据库连接
  - [ ] Redis 连接
  - [ ] 迁移状态
  - [ ] RLS 状态（可选）

**验证命令**:
```bash
# 正常情况
curl -i http://localhost:8000/ready/
# 应该返回 200

# 模拟 DB 故障
docker-compose stop postgres
curl -i http://localhost:8000/ready/
# 应该返回 503（不是 500）

# 恢复
docker-compose start postgres
```

---

## 🔐 安全检查

### HTTPS & SSL

- [ ] SSL 证书已配置（非自签名）
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SECURE_PROXY_SSL_HEADER` 已配置
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000`

### 密钥管理

- [ ] 所有密钥已从代码中移除
- [ ] 使用环境变量或密钥管理服务
- [ ] 生产密钥与测试密钥不同：
  - [ ] Stripe: `sk_live_xxx`（不是 `sk_test_xxx`）
  - [ ] Auth0: 生产租户
  - [ ] Fireblocks: 生产 API Key

---

## 🗄️ 数据库检查

### 迁移

- [ ] 所有迁移已执行
- [ ] 无待应用迁移

```bash
python manage.py showmigrations
# 所有迁移应该有 [X] 标记
```

### 备份

- [ ] 自动备份已配置
- [ ] 备份保留策略已设置
- [ ] 备份恢复已测试

### 性能

- [ ] 索引已创建
- [ ] 慢查询已优化
- [ ] 连接池已配置

---

## 🔧 应用检查

### Django Checks

```bash
python manage.py check --deploy
# 应该无错误和警告
```

### 环境变量

- [ ] 所有必需环境变量已设置
- [ ] `.env.production` 文件已创建
- [ ] 敏感信息未提交到版本控制

### 日志

- [ ] 日志级别设置为 WARNING（生产）
- [ ] 日志聚合已配置（CloudWatch/ELK）
- [ ] 敏感信息未记录（密码、token）

---

## 📊 监控与告警

### Sentry

- [ ] Sentry 已配置
- [ ] 测试事件已发送
- [ ] 告警规则已设置

### 健康检查

- [ ] Kubernetes/ALB 健康检查指向 `/ready/`
- [ ] 健康检查间隔已配置
- [ ] 不健康阈值已设置

### 告警

- [ ] 错误率告警
- [ ] 响应时间告警
- [ ] 数据库连接告警
- [ ] 磁盘空间告警

---

## 🚀 部署流程

### 预部署

- [ ] 代码已审查
- [ ] 测试已通过
- [ ] 数据库备份已完成
- [ ] 回滚计划已准备

### 部署

- [ ] 构建 Docker 镜像
- [ ] 推送到镜像仓库
- [ ] 更新 Kubernetes/ECS 配置
- [ ] 执行滚动更新

### 后部署

- [ ] 健康检查通过
- [ ] 烟雾测试通过
- [ ] 日志无异常
- [ ] 监控指标正常

---

## 📝 文档检查

- [ ] README.md 已更新
- [ ] API 文档已更新
- [ ] 部署文档已更新
- [ ] Runbook 已准备

---

## ✅ 最终确认

- [ ] 所有核心检查点（1-6）已完成
- [ ] 安全检查已通过
- [ ] 数据库检查已通过
- [ ] 监控告警已配置
- [ ] 部署流程已验证

**签字确认**:

技术负责人: ________________  日期: _________

运维负责人: ________________  日期: _________

产品负责人: ________________  日期: _________

---

**🎉 检查完成！准备上线！**
