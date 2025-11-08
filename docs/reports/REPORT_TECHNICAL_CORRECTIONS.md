# POSX 技术建议分析与修正

## ✅ 全部采纳（8/8）

评审者继续发现了我之前分析中的技术错误，这些建议全部有效且关键。

---

## 1. Axios 拦截器 Hook 使用错误 ✅✅✅

**严重性：P0（运行时错误）**

### 问题分析

我之前的代码：
```typescript
// ❌ 错误：Hook 不能在拦截器中调用
apiClient.interceptors.request.use(
  async (config) => {
    const { getAccessTokenSilently } = useAuth(); // ❌ 这会报错！
    // ...
  }
);
```

**错误原因**：
- React Hook 只能在函数组件或自定义 Hook 中调用
- 拦截器是普通函数，不是 React 组件
- 运行时会报错：`Invalid hook call`

### 正确实现

#### 方案1：Provider 注入（推荐）

```typescript
// lib/api/client.ts

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// 全局 token getter（由 Provider 设置）
let getAccessToken: (() => Promise<string | null>) | null = null;

// 设置 token getter（在 Provider 中调用）
export function setTokenGetter(getter: () => Promise<string | null>) {
  getAccessToken = getter;
}

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use(
  async (config) => {
    // 1. 注入请求 ID
    config.headers['X-Request-Id'] = crypto.randomUUID();
    
    // 2. 注入站点代码
    config.headers['X-Site-Code'] = getSiteCode();
    
    // 3. 获取 Token（通过注入的 getter）
    if (getAccessToken) {
      try {
        const token = await getAccessToken();
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
      } catch (error) {
        console.warn('Failed to get access token:', error);
      }
    }
    
    return config;
  }
);

export default apiClient;


// components/providers/AuthProvider.tsx

'use client';

import { useAuth } from '@auth0/nextjs-auth0/client';
import { useEffect } from 'react';
import { setTokenGetter } from '@/lib/api/client';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { getAccessTokenSilently } = useAuth();
  
  // ✅ 在组件中注入 token getter
  useEffect(() => {
    setTokenGetter(async () => {
      try {
        return await getAccessTokenSilently();
      } catch {
        return null;
      }
    });
  }, [getAccessTokenSilently]);
  
  return <>{children}</>;
}
```

#### 方案2：Server Component / Route Handler

```typescript
// app/api/proxy/[...path]/route.ts

import { getAccessToken } from '@auth0/nextjs-auth0';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // 在服务端获取 token
  const { accessToken } = await getAccessToken();
  
  // 转发请求到后端 API
  const response = await fetch(
    `${process.env.API_URL}${request.nextUrl.pathname}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Site-Code': getSiteCode(request),
      },
    }
  );
  
  return NextResponse.json(await response.json());
}
```

---

## 2. CSRF 与认证方式对齐 ✅

**严重性：P1（安全配置混乱）**

### 问题分析

如果后端**纯 JWT 认证**：
- 不需要 Session Cookie
- 不需要 CSRF Protection（JWT 本身防 CSRF）
- `CSRF_COOKIE_HTTPONLY=True` 会让前端拿不到 token

### 正确配置

```python
# config/settings/base.py

# 认证策略：纯 JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.core.auth.Auth0JWTAuthentication',  # 仅 JWT
    ],
    # 不需要 SessionAuthentication
}

# CSRF 配置（API 不需要）
CSRF_COOKIE_HTTPONLY = False  # API 不使用 CSRF
CSRF_USE_SESSIONS = False

# 禁用 CSRF 中间件（API-only 项目）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ❌ 移除：'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...
]

# Webhook 路由自动豁免（无需 @csrf_exempt）
```

**如果混合使用 Session + JWT**：
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # Session（Web）
        'apps.core.auth.Auth0JWTAuthentication',  # JWT（API）
    ],
}

# 保留 CSRF 中间件
MIDDLEWARE = [
    # ...
    'django.middleware.csrf.CsrfViewMiddleware',
    # ...
]

# Webhook 显式豁免
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    # ...
```

---

## 3. CSP 中间件与白名单 ✅

**严重性：P1（安全策略不生效）**

### 问题分析

设置了 `CSP_*` 变量，但**没有启用中间件**，CSP 不会生效。

### 正确实现

**安装依赖：**
```bash
pip install django-csp
```

**配置：**
```python
# requirements/base.txt
django-csp==3.8


# config/settings/base.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',  # ⭐ 添加 CSP 中间件
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

# CSP 配置（收紧版）
CSP_DEFAULT_SRC = ("'self'",)

CSP_SCRIPT_SRC = (
    "'self'",
    "https://js.stripe.com",  # Stripe
    "https://verify.walletconnect.com",  # WalletConnect
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Tailwind 需要（生产可用 nonce）
)

CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",  # CDN 图片
)

CSP_CONNECT_SRC = (
    "'self'",
    "https://api.stripe.com",
    "https://api.fireblocks.io",
    "https://sandbox-api.fireblocks.io",
    "https://*.auth0.com",
    "https://relay.walletconnect.com",
    process.env.NEXT_PUBLIC_API_URL,
)

CSP_FRAME_SRC = (
    "https://js.stripe.com",  # Stripe Elements
    "https://verify.walletconnect.com",
)

CSP_FONT_SRC = (
    "'self'",
    "data:",
)

# 报告地址（可选）
CSP_REPORT_URI = "/api/csp-report/"

# 开发环境宽松
if DEBUG:
    CSP_SCRIPT_SRC += ("'unsafe-eval'",)  # HMR
```

**移除废弃配置：**
```python
# ❌ 删除：SECURE_BROWSER_XSS_FILTER（已废弃）
```

---

## 4. DRF 渲染/解析器环境区分 ✅

**严重性：P2（性能优化）**

### 正确配置

```python
# config/settings/base.py

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    # ...
}


# config/settings/local.py

from .base import *

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # 开发可浏览
]

DEBUG = True
```

---

## 5. Auth0 JWT 校验细节 ✅

**严重性：P0（安全关键）**

### 正确实现

```python
# apps/core/auth.py

import jwt
from jwt import PyJWKClient
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import time

class Auth0JWTAuthentication(BaseAuthentication):
    """
    Auth0 JWT 认证
    
    安全措施：
    1. JWKS 缓存（避免每次请求获取公钥）
    2. Leeway 时钟偏移容忍
    3. 严格校验 iss/aud
    """
    
    # ⭐ JWKS 客户端（缓存公钥）
    jwks_client = None
    
    def __init__(self):
        if not self.jwks_client:
            self.__class__.jwks_client = PyJWKClient(
                f"{settings.AUTH0_DOMAIN}/.well-known/jwks.json",
                cache_keys=True,  # ⭐ 启用缓存
                max_cached_keys=10,
                cache_jwk_set_ttl=3600,  # 缓存 1 小时
            )
    
    def authenticate(self, request):
        """认证请求"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # 获取签名密钥
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # 解码并验证 JWT
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=settings.AUTH0_AUDIENCE,  # ⭐ 验证受众
                issuer=settings.AUTH0_ISSUER,  # ⭐ 验证签发者
                leeway=60,  # ⭐ 容忍 60 秒时钟偏移
            )
            
            # 获取或创建用户
            user = self.get_or_create_user(payload)
            
            return (user, payload)
        
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidAudienceError:
            raise AuthenticationFailed('Invalid audience')
        except jwt.InvalidIssuerError:
            raise AuthenticationFailed('Invalid issuer')
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
    
    def get_or_create_user(self, payload):
        """根据 JWT payload 获取或创建用户"""
        from apps.users.models import User
        
        auth0_sub = payload.get('sub')
        email = payload.get('email')
        
        user, created = User.objects.get_or_create(
            auth0_sub=auth0_sub,
            defaults={
                'email': email,
                'auth_type': 'auth0',
            }
        )
        
        return user


# config/settings/base.py

AUTH0_DOMAIN = env('AUTH0_DOMAIN')  # https://your-tenant.auth0.com
AUTH0_AUDIENCE = env('AUTH0_AUDIENCE')  # https://api.posx.io
AUTH0_ISSUER = env('AUTH0_ISSUER')  # https://your-tenant.auth0.com/
```

---

## 6. Stripe Webhook 多端点密钥 ✅

**严重性：P1（环境隔离）**

### 正确实现

```python
# config/settings/base.py

# Demo 环境
STRIPE_WEBHOOK_SECRET_DEMO = env('STRIPE_WEBHOOK_SECRET_DEMO', default='')

# Production 环境
STRIPE_WEBHOOK_SECRET_PROD = env('STRIPE_WEBHOOK_SECRET_PROD', default='')


# apps/webhooks/views.py

from django.conf import settings

class StripeWebhookView(APIView):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # ⭐ 根据环境或 Host 选择密钥
        webhook_secret = self.get_webhook_secret(request)
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            return Response({'error': 'Invalid signature'}, status=403)
        
        # ...
    
    def get_webhook_secret(self, request):
        """根据环境选择 Webhook Secret"""
        env = settings.DJANGO_ENV
        
        if env == 'production':
            return settings.STRIPE_WEBHOOK_SECRET_PROD
        elif env == 'demo':
            return settings.STRIPE_WEBHOOK_SECRET_DEMO
        else:
            # 本地开发
            return settings.STRIPE_WEBHOOK_SECRET
        
        # 也可以根据 Host 判断
        # host = request.get_host()
        # if 'demo' in host:
        #     return settings.STRIPE_WEBHOOK_SECRET_DEMO
        # return settings.STRIPE_WEBHOOK_SECRET_PROD
```

---

## 7. 站点 Cookie 与跨域 ✅

**严重性：P2（纯 JWT 不需要）**

### 分析

**纯 JWT 策略（推荐）：**
- 不依赖 Cookie
- Token 在 `Authorization` header 中
- 无需设置 Cookie 属性

**如果需要 Cookie（Session）：**
```python
# 跨域 Cookie（前端域 ≠ API 域）
SESSION_COOKIE_SAMESITE = 'None'  # 允许跨站
SESSION_COOKIE_SECURE = True  # 必须 HTTPS

# 同域 Cookie（推荐）
SESSION_COOKIE_SAMESITE = 'Lax'  # 更安全
SESSION_COOKIE_SECURE = True
```

**当前项目采用纯 JWT，无需 Cookie 配置。**

---

## 8. Postgres 函数索引并发创建 ✅

**严重性：P1（迁移锁表风险）**

### 问题分析

Django 的 `UniqueConstraint(Lower('address'))` 会生成：
```sql
ALTER TABLE wallets ADD CONSTRAINT uq_wallet_address_lower 
  UNIQUE (LOWER(address));
```

这会**锁表**，生产环境危险。

### 正确实现

```python
# apps/users/migrations/0003_add_wallet_constraints.py

from django.db import migrations

class Migration(migrations.Migration):
    atomic = False  # ⭐ 关闭事务（CONCURRENTLY 需要）
    
    dependencies = [
        ('users', '0002_add_nonce_table'),
    ]
    
    operations = [
        # 1. ⭐ 先创建并发索引
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_wallet_address_lower
                ON wallets (LOWER(address));
            """,
            reverse_sql="""
                DROP INDEX CONCURRENTLY IF EXISTS uq_wallet_address_lower;
            """
        ),
        
        # 2. 然后添加约束（使用已有索引，不锁表）
        migrations.RunSQL(
            sql="""
                ALTER TABLE wallets 
                ADD CONSTRAINT uq_wallet_address_lower_constraint
                UNIQUE USING INDEX uq_wallet_address_lower;
            """,
            reverse_sql="""
                ALTER TABLE wallets 
                DROP CONSTRAINT IF EXISTS uq_wallet_address_lower_constraint;
            """
        ),
    ]
```

或者纯 SQL 索引（不用约束）：
```python
class Migration(migrations.Migration):
    atomic = False
    
    operations = [
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_wallet_address_lower
                ON wallets (LOWER(address));
            """,
            reverse_sql="""
                DROP INDEX CONCURRENTLY IF EXISTS idx_wallet_address_lower;
            """
        ),
    ]
```

---

## 📊 修正总结

| 问题 | 严重性 | 状态 |
|------|--------|------|
| Axios Hook 使用错误 | P0 | ✅ 已修正 |
| CSRF 与 JWT 混乱 | P1 | ✅ 已修正 |
| CSP 中间件缺失 | P1 | ✅ 已修正 |
| DRF 渲染器冗余 | P2 | ✅ 已优化 |
| JWT 校验不严格 | P0 | ✅ 已加固 |
| Webhook 密钥混用 | P1 | ✅ 已隔离 |
| Cookie 配置冗余 | P2 | ✅ 已简化 |
| 函数索引锁表 | P1 | ✅ 已修正 |

---

## 🎯 下一步

基于这些修正，重新生成完整的项目骨架，包含：
1. 所有修正后的配置文件
2. 正确的认证实现
3. 安全的迁移脚本
4. 完整的目录结构
