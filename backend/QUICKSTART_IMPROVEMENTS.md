# Phase B 补充改进快速上手

## 🎯 新增功能一览

### 1. 更安全的 Auth0 配置
- ✅ 启动时自动检查配置
- ✅ JWKS 失败快速返回 401
- ✅ 友好的错误日志

### 2. 更严格的数据校验
- ✅ `level` 必须 1-10
- ✅ `mode='level'` 时禁止差额奖励
- ✅ 时间范围必须合法

### 3. 更可靠的并发处理
- ✅ 激活版本原子操作
- ✅ 同站点同名仅一个激活

### 4. 更友好的错误提示
- ✅ 统一错误格式（code + request_id）
- ✅ scope=all 必须分页
- ✅ 详细的验证错误信息

### 5. 更完善的测试覆盖
- ✅ RLS 跨站隔离测试
- ✅ SET LOCAL 事务隔离测试
- ✅ 并发场景测试

---

## 📝 开发者需知

### 错误响应格式变更

**旧格式**:
```json
{
  "error": true,
  "message": "Invalid input",
  "detail": {...}
}
```

**新格式**:
```json
{
  "code": "VALIDATION.INVALID_INPUT",
  "message": "Invalid input",
  "detail": {...},
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**前端适配建议**:
```typescript
// 兼容新旧格式
interface ErrorResponse {
  code?: string;           // 新增
  error?: boolean;         // 向后兼容
  message: string;
  detail: any;
  request_id?: string;     // 新增
}

// 使用 code 判断错误类型
if (error.code === 'AUTH.UNAUTHORIZED') {
  // 跳转登录
} else if (error.code?.startsWith('VALIDATION.')) {
  // 显示验证错误
}
```

---

### CommissionPlan API 变更

#### 创建计划时的新校验

```typescript
// ❌ 错误：mode='level' 但启用差额奖励
{
  name: 'Plan A',
  mode: 'level',
  diff_reward_enabled: true  // 会被拒绝
}

// ✅ 正确
{
  name: 'Plan A',
  mode: 'level',
  diff_reward_enabled: false
}

// 或者
{
  name: 'Plan B',
  mode: 'solar_diff',
  diff_reward_enabled: true  // OK
}
```

#### 创建层级时的新校验

```typescript
// ❌ 错误：mode='level' 但设置 diff_cap_percent
{
  tiers: [
    {level: 1, rate_percent: '12.00', diff_cap_percent: '10.00'}  // 会被拒绝
  ]
}

// ✅ 正确：mode='level' 时不设置 diff_cap_percent
{
  tiers: [
    {level: 1, rate_percent: '12.00'}
  ]
}

// 或者 mode='solar_diff' 时可以设置
{
  tiers: [
    {level: 1, rate_percent: '12.00', diff_cap_percent: '10.00'}  // OK
  ]
}
```

---

### Agents API 变更

#### scope=all 必须分页

```typescript
// ❌ 错误：scope='all' 但没有分页
GET /api/v1/agents/me/customers?scope=all

// Response: 400
{
  "code": "VALIDATION.PAGINATION_REQUIRED",
  "message": "scope=\"all\" 时必须提供 page 和 size 参数",
  "hint": "例如：?scope=all&page=1&size=20"
}

// ✅ 正确：提供分页参数
GET /api/v1/agents/me/customers?scope=all&page=1&size=20
```

---

## 🔧 运维指南

### 启动检查清单

1. **检查 Auth0 配置**

```bash
# 启动服务时查看日志
python manage.py runserver

# ✅ 正常输出：
✅ Auth0 配置已加载: Domain=posx-dev.***, Audience=https://api...., JWKS_TTL=3600s

# ⚠️ 警告输出：
⚠️ Auth0 配置缺失: AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_ISSUER. JWT 认证将失败，请检查环境变量。
```

2. **运行 RLS 测试**

```bash
# 快速验证 RLS 隔离
python manage.py test apps.commission_plans.tests_rls

# 应该全部通过
```

3. **检查中间件顺序**

```bash
# 查看中间件配置
grep -A 15 "^MIDDLEWARE = " backend/config/settings/base.py

# 确认 SiteContextMiddleware 在 AuthenticationMiddleware 之后
```

---

### 常见问题排查

#### 问题 1：Auth0 认证失败

```bash
# 查看日志
tail -f logs/django.log | grep "AUTH.JWKS_FETCH_FAILED"

# 检查配置
python manage.py shell
>>> from django.conf import settings
>>> settings.AUTH0_DOMAIN
>>> settings.AUTH0_AUDIENCE
```

#### 问题 2：RLS 隔离不生效

```bash
# 检查 RLS 状态
psql -U posx_app -d posx_local -c "
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'commission_plans';
"

# 应该显示 rowsecurity=t
```

#### 问题 3：并发激活出现多个激活版本

```bash
# 查询激活计划
psql -U posx_app -d posx_local -c "
SELECT plan_id, site_id, name, version, is_active
FROM commission_plans
WHERE is_active = true
ORDER BY name, version;
"

# 同站点同名应该只有一个激活版本

# 如果发现多个，手动修复：
python manage.py shell
>>> from apps.commission_plans.models import CommissionPlan
>>> # 保留最新版本，停用其他
>>> CommissionPlan.objects.filter(
...     site_id='...',
...     name='Plan A',
...     is_active=True
... ).exclude(version=2).update(is_active=False)
```

---

## 📚 相关文档

- **IMPROVEMENTS_SUMMARY.md** - 改进详细说明
- **PHASE_B_IMPROVEMENTS_CHECKLIST.md** - 验收清单（10分钟）
- **ACCEPTANCE_TESTING.md** - 完整验收测试
- **IMPLEMENTATION_SUMMARY.md** - Phase B 实施总结

---

**更新日期**: 2025-11-08  
**适用版本**: Phase B + 补充改进



