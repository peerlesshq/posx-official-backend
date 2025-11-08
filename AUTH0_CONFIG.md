# ✅ Auth0 配置完成

**配置时间**: 2025-11-08  
**状态**: ✅ 配置成功并验证通过

---

## 📋 配置信息

### Auth0 凭证

- **Domain**: `dev-posx.us.auth0.com`
- **Client ID**: `QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK`
- **Client Secret**: `cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP`
- **Issuer**: `https://dev-posx.us.auth0.com/`
- **Audience**: `http://localhost:8000/api/v1/` ⭐ (本地测试 URL)

---

## ✅ 配置验证

所有 Auth0 配置已成功加载：

```
✅ AUTH0_DOMAIN: dev-posx.us.auth0.com
✅ AUTH0_AUDIENCE: http://localhost:8000/api/v1/
✅ AUTH0_ISSUER: https://dev-posx.us.auth0.com/
✅ AUTH0_CLIENT_ID: QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
✅ AUTH0_CLIENT_SECRET: 已配置
```

---

## ⚠️ 重要提示：AUTH0_AUDIENCE 配置

### 当前配置

**AUTH0_AUDIENCE**: `http://localhost:8000/api/v1/`

这是一个**本地测试 URL**，用于开发环境测试。

### 在 Auth0 Dashboard 中配置

**重要**: `AUTH0_AUDIENCE` 必须与 Auth0 Dashboard 中创建的 **API 标识符（Identifier）** 完全匹配！

#### 步骤 1: 登录 Auth0 Dashboard

访问: https://manage.auth0.com/

#### 步骤 2: 创建或配置 API

1. 进入 **Applications** → **APIs**
2. 创建新 API 或编辑现有 API
3. 设置 **Identifier** 为: `http://localhost:8000/api/v1/`
   - 或者使用其他标识符，但需要同步更新 `.env` 文件

#### 步骤 3: 配置 Machine to Machine Application

1. 进入 **Applications** → **Applications**
2. 找到你的应用（Client ID: `QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK`）
3. 在 **APIs** 标签页中，授权该应用访问你创建的 API
4. 确保有正确的权限（scopes）

---

## 🔧 环境变量配置

配置已保存在 `.env` 文件中：

```env
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/
AUTH0_CLIENT_ID=QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK
AUTH0_CLIENT_SECRET=cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP
```

---

## 🧪 测试 Auth0 认证

### 1. 获取 Access Token

使用 Auth0 的测试工具或 API：

```bash
curl -X POST https://dev-posx.us.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "QymLIQ48gPrLRLdncOpN3xFtD5xjjpYK",
    "client_secret": "cRiS6RB4sfM_QvNsPgcjUP_PRXmRJ6LbZmhLCp0jSXzxpfFMNUtj6x_CJFIh9nNP",
    "audience": "http://localhost:8000/api/v1/",
    "grant_type": "client_credentials"
  }'
```

### 2. 使用 Token 访问 API

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/v1/tiers/
```

### 3. 测试用户登录流程

对于用户登录，需要使用 **Authorization Code Flow** 或 **Password Grant**（仅开发环境）。

---

## 📝 代码中的使用

### JWT 认证类

位置: `backend/apps/core/authentication.py`

```python
from apps.core.authentication import Auth0JWTAuthentication

# 在 ViewSet 中使用
class TierViewSet(viewsets.ModelViewSet):
    authentication_classes = [Auth0JWTAuthentication]
    permission_classes = [IsAuthenticated]
    # ...
```

### 自动用户创建

当用户首次通过 Auth0 登录时，系统会：
1. 验证 JWT token
2. 提取 `sub` (Auth0 Subject ID)
3. 自动创建本地用户（如果不存在）
4. 返回用户对象

---

## 🔍 验证配置

运行测试脚本：

```bash
cd backend
python test_auth0_config.py
```

或使用 Django shell：

```bash
python manage.py shell
```

```python
from django.conf import settings
print(settings.AUTH0_DOMAIN)
print(settings.AUTH0_AUDIENCE)
print(settings.AUTH0_ISSUER)
```

---

## 🚨 常见问题

### 1. "Invalid audience" 错误

**原因**: `AUTH0_AUDIENCE` 与 Auth0 Dashboard 中的 API Identifier 不匹配

**解决**: 
- 检查 Auth0 Dashboard 中的 API Identifier
- 更新 `.env` 文件中的 `AUTH0_AUDIENCE`
- 重启 Django 服务器

### 2. "Invalid issuer" 错误

**原因**: Issuer URL 不正确

**解决**: 
- 确保 `AUTH0_ISSUER` 格式为: `https://{domain}/`
- 注意末尾的斜杠

### 3. "Unable to verify token signature" 错误

**原因**: 无法从 Auth0 获取 JWKS

**解决**:
- 检查网络连接
- 验证 `AUTH0_DOMAIN` 是否正确
- 检查 Auth0 Dashboard 中的 API 配置

---

## 📚 相关文档

- **Auth0 Dashboard**: https://manage.auth0.com/
- **Auth0 API 文档**: https://auth0.com/docs/api
- **JWT 认证实现**: `backend/apps/core/authentication.py`
- **Django 设置**: `backend/config/settings/base.py`

---

## ✨ 下一步

1. ✅ Auth0 配置已完成
2. 📋 在 Auth0 Dashboard 中创建/配置 API
3. 🧪 测试 JWT 认证流程
4. 🔐 实现用户登录端点
5. 🚀 开始 Phase B 开发

---

**配置完成！可以开始测试 Auth0 认证了！** 🎉


