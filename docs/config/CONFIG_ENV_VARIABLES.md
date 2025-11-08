# 环境变量配置文档

## Auth0 JWT 认证配置

以下环境变量用于 Auth0 JWT 认证和 JWKS 验证：

### 必需变量

```bash
# Auth0 域名（不含 https://）
AUTH0_DOMAIN=your-tenant.auth0.com

# Auth0 API 标识符（Audience）
AUTH0_AUDIENCE=https://api.posx.io

# Auth0 Issuer URL（完整 URL）
AUTH0_ISSUER=https://your-tenant.auth0.com/
```

### 可选变量（已有默认值）

```bash
# JWKS 缓存 TTL（秒）
# 默认：3600（1小时）
AUTH0_JWKS_CACHE_TTL=3600

# JWT 时间容差（秒）
# 默认：10（允许10秒时钟偏差）
AUTH0_JWT_LEEWAY=10
```

## 如何获取 Auth0 配置

1. **登录 Auth0 Dashboard**: https://manage.auth0.com/

2. **获取 AUTH0_DOMAIN**:
   - 在左侧菜单选择 "Settings"
   - 复制 "Domain" 字段（如 `your-tenant.auth0.com`）

3. **获取 AUTH0_AUDIENCE 和 AUTH0_ISSUER**:
   - 在左侧菜单选择 "Applications" → "APIs"
   - 选择你的 API（或创建新 API）
   - 复制 "Identifier"（作为 `AUTH0_AUDIENCE`）
   - `AUTH0_ISSUER` 格式为：`https://{AUTH0_DOMAIN}/`

## 示例配置

```bash
# 开发环境示例
AUTH0_DOMAIN=posx-dev.us.auth0.com
AUTH0_AUDIENCE=https://api.posx.dev
AUTH0_ISSUER=https://posx-dev.us.auth0.com/

# 生产环境示例
AUTH0_DOMAIN=posx.auth0.com
AUTH0_AUDIENCE=https://api.posx.io
AUTH0_ISSUER=https://posx.auth0.com/
```

## 验证配置

运行以下命令验证 Auth0 配置是否正确：

```bash
# 测试 JWKS 端点
curl https://{AUTH0_DOMAIN}/.well-known/jwks.json

# 应该返回 JSON 格式的公钥列表
```

## 安全注意事项

⚠️ **生产环境**:
- 使用独立的 Auth0 租户（不要与开发环境共用）
- 定期轮换 Auth0 密钥
- 启用 Auth0 异常检测和限流
- 配置正确的回调 URL 白名单

⚠️ **JWKS 缓存**:
- 默认缓存 1 小时以减少 Auth0 请求
- 如果密钥轮换，最多延迟 1 小时生效
- 可通过重启服务强制刷新缓存



