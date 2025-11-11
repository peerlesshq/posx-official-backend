# Railway 部署最终检查清单

## 当前状态

✅ **已完成**：
- 代码已修复并推送（删除有问题的迁移）
- RLS 迁移已添加跳过机制
- 数据库连接配置已优化
- Postgres 和 Redis 已创建并连接

❌ **待修复**：
- DEBUG 仍为 True（应为 False）
- CELERY 配置指向 localhost（应引用 Railway Redis）
- Start Command 不完整（缺少 gunicorn）
- 模型与迁移不同步警告

---

## 🎯 最终修复步骤

### 步骤 1: 修改环境变量（Railway Variables）

进入 Railway → `posx-official-backend` → **Variables**，修改以下 3 个：

#### 1.1 修改 DEBUG
```
DEBUG=False
```

#### 1.2 修改 CELERY_BROKER_URL
```
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
```

#### 1.3 修改 CELERY_RESULT_BACKEND
```
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

---

### 步骤 2: 确认 Start Command（Settings → Deploy）

**应该是**：
```bash
python manage.py migrate && python manage.py collectstatic --noinput && python manage.py createsuperuser --noinput; gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2
```

**检查要点**：
- ✅ 包含 `migrate`
- ✅ 包含 `collectstatic`
- ✅ 包含 `createsuperuser`（可选）
- ✅ 包含 `gunicorn`（最重要！）
- ✅ `--bind 0.0.0.0:$PORT`
- ✅ 使用 `&&` 和 `;` 正确连接

---

### 步骤 3: 删除旧 Postgres 并重建（如果还有模型同步警告）

如果步骤 1-2 完成后仍然有 "Your models have changes" 警告：

1. **删除 Postgres Service**
   - Postgres → Settings → Danger → Delete Service
   
2. **等待 3 分钟**

3. **重新创建**
   - + New → Database → PostgreSQL
   
4. **连接到 Backend**
   - Add Variable Reference 或手动添加 `DATABASE_URL`

---

### 步骤 4: 手动触发重新部署

无论是否重置数据库，都执行：

1. Backend Service → **Deployments**
2. 点击最新部署右侧的 **⋮** (三个点)
3. 选择 **Redeploy**

---

### 步骤 5: 验证部署成功

#### 5.1 查看 Deploy Logs

应该看到（完整流程）：
```
✅ Auth0 配置已加载
✅ Running migrations:
  ✅ Applying contenttypes.0001_initial... OK
  ✅ ... (所有迁移)
  ✅ No migrations to apply. (或所有迁移 OK)
✅ Collecting static files...
  X static files copied to '/app/backend/staticfiles'
✅ Superuser created successfully. (或 already exists)
✅ Starting gunicorn 21.2.0
✅ Listening at: http://0.0.0.0:8000
✅ Booting worker with pid: XXX
```

#### 5.2 测试端点

```bash
# 健康检查
curl https://posx-official-backend-demo.up.railway.app/health/
# 期望: {"status": "healthy"}

# 详细检查
curl https://posx-official-backend-demo.up.railway.app/ready/
# 期望: {"status": "healthy", "checks": {...}}
```

#### 5.3 访问 Admin

```
https://posx-official-backend-demo.up.railway.app/admin/
```

- Username: `admin`
- Password: `Demo_Admin_2024!`

---

## 🔍 如果仍然 502

### 检查 Deploy Logs 最后几行

如果看到：
- ❌ 只有迁移，没有 `Starting gunicorn` → Start Command 不完整
- ❌ `ModuleNotFoundError` → 依赖缺失
- ❌ `Address already in use` → 端口冲突
- ❌ `Worker timeout` → 资源不足或配置错误

### 检查 HTTP Logs

查看实际请求的状态码和响应时间，帮助定位问题。

---

## 📊 部署成功的标志

- ✅ Deploy Logs 显示 `Listening at: http://0.0.0.0:8000`
- ✅ HTTP Logs 显示 200 状态码
- ✅ `/health/` 返回 JSON
- ✅ `/admin/` 显示登录页面
- ✅ 可以使用超级用户登录

---

## 🎉 完成后的下一步

1. 删除超级用户环境变量（`DJANGO_SUPERUSER_*` 3个）
2. 测试 API 端点
3. 配置 Retool 连接
4. 验证 Stripe Webhook
5. 进行功能演示

---

**执行步骤 1-4，然后告诉我部署结果！** 🚀

