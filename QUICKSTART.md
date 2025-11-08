# 🚀 POSX Framework v1.0 - 快速设置指南

**所需时间**: 15 分钟  
**难度**: 简单  

---

## 📋 前置条件

确保已安装：
- ✅ Docker 20.10+
- ✅ Docker Compose 2.0+
- ✅ Git

---

## 1️⃣ 克隆项目（或解压）

```bash
# 如果是 Git 仓库
git clone <repo-url>
cd posx-framework-v1.0

# 如果是压缩包
tar -xzf posx-framework-v1.0.tar.gz
cd posx-framework-v1.0
```

---

## 2️⃣ 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

### 必需配置项

```bash
# Django
SECRET_KEY=your-secret-key-here   # ⭐ 必须修改

# Database
DB_PASSWORD=your-db-password       # ⭐ 建议修改

# Auth0（注册账号后获取）
AUTH0_DOMAIN=dev-xxx.auth0.com
AUTH0_AUDIENCE=https://api.posx.local
AUTH0_ISSUER=https://dev-xxx.auth0.com/
```

### 可选配置项（测试环境）

```bash
# Stripe（使用测试密钥）
STRIPE_SECRET_KEY=sk_test_xxx

# Fireblocks（使用沙盒环境）
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
```

---

## 3️⃣ 启动服务

```bash
# 启动所有服务
make up

# 或使用 docker-compose
docker-compose up -d
```

等待服务启动（约 30 秒）...

---

## 4️⃣ 运行数据库迁移

```bash
# 执行迁移
make migrate

# 或使用 docker-compose
docker-compose exec backend python manage.py migrate
```

你应该看到：
```
✅ RLS 索引已创建
✅ RLS 策略已启用
✅ 所有迁移已完成
```

---

## 5️⃣ 创建管理员账户

```bash
# 创建超级用户
make createsuperuser

# 或使用 docker-compose
docker-compose exec backend python manage.py createsuperuser
```

输入：
- Username: `admin`
- Email: `admin@example.com`
- Password: `你的密码`

---

## 6️⃣ 验证安装

### 检查健康状态

```bash
# 方法 1: 使用 Make
make health

# 方法 2: 使用 curl
curl http://localhost:8000/health/
curl http://localhost:8000/ready/
```

你应该看到：
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "migrations": "ok",
    "rls": "ok"
  }
}
```

### 检查 RLS 状态

```bash
make check-rls
```

你应该看到所有表的 `rowsecurity` 为 `t` (true)。

---

## 7️⃣ 访问应用

### Backend API
- **URL**: http://localhost:8000
- **Health**: http://localhost:8000/health/
- **Ready**: http://localhost:8000/ready/
- **Admin**: http://localhost:8000/admin/
  - Username: `admin`
  - Password: `你创建的密码`

### 查看日志

```bash
# 所有服务日志
make logs

# 或指定服务
docker-compose logs -f backend
docker-compose logs -f postgres
```

---

## 🎯 下一步

### 本地开发

1. **修改代码**: 后端代码在 `backend/` 目录
2. **自动重启**: Django 开发服务器会自动重启
3. **查看日志**: 使用 `make logs`

### 数据库操作

```bash
# 进入数据库 shell
make dbshell

# 创建迁移
make makemigrations

# 应用迁移
make migrate
```

### 测试

```bash
# 运行测试
make test

# 代码覆盖率
make coverage
```

---

## 🔧 常见问题

### 端口冲突

**错误**: `bind: address already in use`

**解决**:
```bash
# 查看占用端口的进程
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# 停止进程或修改 docker-compose.yml 中的端口
```

### 数据库连接失败

**错误**: `could not connect to server`

**解决**:
```bash
# 检查 PostgreSQL 是否启动
docker-compose ps postgres

# 查看日志
docker-compose logs postgres

# 重启服务
docker-compose restart postgres
```

### 迁移失败

**错误**: `relation does not exist`

**解决**:
```bash
# 重置数据库（⚠️  会删除所有数据）
make dbreset

# 或手动
docker-compose down -v
docker-compose up -d
make migrate
```

### RLS 未启用

**症状**: `check-rls` 显示 `rowsecurity = f`

**解决**:
```bash
# 重新运行 RLS 迁移
docker-compose exec backend python manage.py migrate core 0004

# 验证
make check-rls
```

---

## 🛑 停止服务

```bash
# 停止所有服务
make down

# 或使用 docker-compose
docker-compose down

# 停止并删除数据（⚠️  危险）
docker-compose down -v
```

---

## 📚 更多文档

- **[README.md](README.md)** - 项目概述
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - 上线前检查清单
- **[POSX_System_Specification_v1.0.0.md](POSX_System_Specification_v1.0.0.md)** - 完整系统规范
- **[POSX_System_Specification_v1.0.4_RLS_Production.md](POSX_System_Specification_v1.0.4_RLS_Production.md)** - RLS 规范

---

## 🎉 设置完成！

现在你可以开始开发了！

**有问题？** 查看日志：`make logs`  
**需要帮助？** 查看文档或提issue

---

**POSX Framework v1.0** - 生产就绪的多站点代币预售平台 🚀
