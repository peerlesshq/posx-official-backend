# Auth0 JWT Token 测试指南

## 🎯 测试目标

验证从 Auth0 获取的 JWT token 能否成功访问 POSX API。

---

## 📋 前置条件

1. ✅ Auth0 API 已创建（Identifier: `http://localhost:8000/api/v1/`）
2. ✅ 应用已授权访问 API
3. ✅ 已获取 Access Token
4. ⏸️ Django 服务器需要运行

---

## 🚀 步骤 1: 启动 Django 服务器

打开新的终端窗口，运行：

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend
.\venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

等待看到：
```
Starting development server at http://0.0.0.0:8000/
```

---

## 🧪 步骤 2: 测试 Token

### 方法 A: 使用 Python 脚本（推荐）

在**另一个终端窗口**运行：

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend
.\venv\Scripts\activate
python test_auth0_simple.py
```

### 方法 B: 使用 curl（如果已安装）

```bash
# 测试不带 token（应该返回 401）
curl http://localhost:8000/api/v1/tiers/

# 测试带 token（应该返回 200）
curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA" \
     http://localhost:8000/api/v1/tiers/
```

### 方法 C: 使用 Python 交互式测试

```python
import requests

# 你的 Auth0 token
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

# 测试不带 token
print("1. Testing without token:")
response = requests.get("http://localhost:8000/api/v1/tiers/")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:200]}")

# 测试带 token
print("\n2. Testing with token:")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/tiers/", headers=headers)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:200]}")
```

---

## ✅ 预期结果

### 成功的情况

1. **不带 token 访问**:
   - Status: `401 Unauthorized`
   - 说明：正确拒绝了未认证请求 ✅

2. **带 token 访问**:
   - Status: `200 OK`
   - Response: JSON 数据（可能是空列表 `[]` 或错误信息）
   - 说明：认证成功 ✅

### 失败的情况

如果带 token 仍然返回 `401`，可能的原因：

1. **Token 过期**
   - 检查 token 的 `exp` 字段
   - 重新从 Auth0 获取新 token

2. **Audience 不匹配**
   - 确保 Auth0 API Identifier = `http://localhost:8000/api/v1/`
   - 确保 `.env` 中的 `AUTH0_AUDIENCE` 匹配

3. **Issuer 不匹配**
   - 确保 `AUTH0_ISSUER = https://dev-posx.us.auth0.com/`

4. **JWKS 获取失败**
   - 检查网络连接
   - 检查 `AUTH0_DOMAIN` 配置

---

## 🔍 调试步骤

### 1. 检查 Django 日志

查看服务器终端的输出，查找：
- `AUTH.JWKS_FETCH_FAILED` - JWKS 获取失败
- `JWT verification failed` - JWT 验证失败
- `Invalid token` - Token 无效

### 2. 验证 Token 内容

访问 https://jwt.io/ 解码你的 token，检查：
- `iss` (issuer): 应该是 `https://dev-posx.us.auth0.com/`
- `aud` (audience): 应该是 `http://localhost:8000/api/v1/`
- `exp` (expiration): 检查是否过期

### 3. 测试健康检查端点

```bash
curl http://localhost:8000/health/
```

应该返回：
```json
{
  "status": "healthy",
  "timestamp": "..."
}
```

---

## 📝 快速测试命令

**一键测试脚本**（确保服务器运行后）：

```powershell
cd backend
python test_auth0_simple.py
```

---

## 🎉 成功标志

如果看到以下输出，说明认证成功：

```
✅ Protected endpoint (with token): PASS
🎉 Auth0 JWT Authentication is working correctly!
```

---

## 📞 需要帮助？

如果遇到问题，检查：
1. Django 服务器是否运行
2. Token 是否过期
3. Auth0 配置是否正确
4. 查看服务器日志输出


