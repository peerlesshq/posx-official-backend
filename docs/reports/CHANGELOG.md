# Changelog

All notable changes to POSX Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-07

### 🎉 首个生产版本

**Code Name**: Foundation

这是 POSX Framework 的第一个正式生产版本，标志着从内部开发版本过渡到可对外发布的稳定版本。

### ✨ 核心特性

#### 1. Row Level Security (RLS) - 完整实现
- ✅ FORCE RLS enforcement（超级用户也受限）
- ✅ UUID 比较（类型安全）
- ✅ 7 个表的策略（orders, tiers, commissions, commission_configs, commission_levels, agent_commission_configs, allocations）
- ✅ Admin 只读跨站（SELECT only）
- ✅ site_id 不可变（触发器保护）
- ✅ search_path 固定（防止函数影子化）
- ✅ 默认权限设置（ALTER DEFAULT PRIVILEGES）

#### 2. 生产级 CSP（Content Security Policy）
- ✅ 无 `unsafe-inline`（生产环境）
- ✅ 严格的白名单
- ✅ Frame ancestors 阻止嵌套
- ✅ Object/embed 禁用
- ✅ Referrer Policy 严格

#### 3. CSRF 智能豁免
- ✅ 专用中间件（CSRFExemptMiddleware）
- ✅ API endpoints 豁免
- ✅ 健康检查豁免
- ✅ Webhook 豁免

#### 4. 生产部署优化
- ✅ 正确的 WSGI 配置
- ✅ Celery autodiscover_tasks
- ✅ collectstatic 自动化
- ✅ 静态文件卷管理

#### 5. 健壮的健康检查
- ✅ /health/ - 简单健康检查
- ✅ /ready/ - 详细就绪检查（DB/Redis/迁移/RLS）
- ✅ 异常路径返回 503（不是 500）
- ✅ 正确的依赖导入

#### 6. 完整的文档
- ✅ README.md - 项目概述和快速开始
- ✅ QUICKSTART.md - 15 分钟快速设置指南
- ✅ PRODUCTION_CHECKLIST.md - 上线前 6 条核心检查
- ✅ 系统规范文档（v1.0.0 + v1.0.4）

### 🔧 技术栈

- Django 4.2+
- Django REST Framework 3.14+
- PostgreSQL 15+
- Redis 7+
- Celery 5.3+
- Gunicorn 21+

### 📦 部署支持

- ✅ Docker + Docker Compose
- ✅ 开发环境配置
- ✅ 生产环境配置
- ✅ Makefile 快捷命令

### 🔒 安全特性

- ✅ HTTPS 强制
- ✅ HSTS (1 year)
- ✅ Secure cookies
- ✅ X-Frame-Options: DENY
- ✅ JWT 认证（Auth0）
- ✅ 密钥管理（环境变量）

### 📊 监控支持

- ✅ Sentry 集成（可选）
- ✅ 健康检查端点
- ✅ 结构化日志（JSON）

---

## [Unreleased]

### 计划中的功能

- [ ] 完整的 Django Models 实现
- [ ] 完整的 API endpoints
- [ ] 前端集成（Next.js）
- [ ] 第三方服务集成（Stripe, Fireblocks）
- [ ] 完整的测试套件
- [ ] API 文档（Swagger/OpenAPI）

---

## 版本命名规则

从 v1.0.0 开始，我们采用语义化版本：
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向下兼容的功能新增
- **PATCH**: 向下兼容的 Bug 修复

---

## 升级指南

### 从内部版本升级到 v1.0.0

如果你使用的是内部 v3.x 版本：

1. 备份数据库
2. 解压 v1.0.0
3. 复制 `.env` 配置
4. 添加新的必需环境变量
5. 重新构建 Docker 镜像
6. 运行迁移
7. 验证健康检查

详见 [QUICKSTART.md](QUICKSTART.md)

---

## 维护者

- POSX Framework Team

---

**[1.0.0]**: https://github.com/your-org/posx-framework/releases/tag/v1.0.0
