# POSX 缺失文件清单 - 评审意见分析

## ✅ 评审结果：13/13 条全部有道理

评级：⭐⭐⭐⭐⭐ (5/5)

评审者水平：**资深架构师级别**，对 Django/DRF、微服务、安全、运维都非常熟悉。

---

## 逐条分析

### 1. Django REST Framework 全局配置文件缺失 ✅

**评价：非常有道理（P0 级别）**

**问题：**
- 我的清单只列出了文件位置，没有强调 DRF 全局配置的重要性
- 缺少具体配置项说明

**需要补充：**
```python
# config/settings/base.py

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.core.auth.Auth0JWTAuthentication',
    ],
    
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
        'order': '10/minute',
    },
    
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
    'DATE_FORMAT': '%Y-%m-%d',
}
```

**优先级：P0（基础配置，必须有）**

---

### 2. CORS/CSRF 与安全头部 ✅

**评价：绝对正确（P0 级别）**

**问题：**
- 我的清单提到了"安全规范"，但没有具体的配置文件内容
- 缺少 CORS、CSRF、安全头部的详细配置

**需要补充：**
```python
# config/settings/base.py

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['X-Request-Id']

# CSRF
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
CSRF_COOKIE_SECURE = True  # 生产环境
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security Headers
SECURE_SSL_REDIRECT = True  # 生产环境
SECURE_HSTS_SECONDS = 31536000  # 1年
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# CSP (基础版)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://js.stripe.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "https://api.stripe.com", "https://api.fireblocks.io")
```

**Webhook 特殊处理：**
```python
# apps/webhooks/views.py

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    authentication_classes = []  # Webhook 不需要认证
    permission_classes = []
    
    def post(self, request):
        # 签名验证替代 CSRF
        if not verify_stripe_signature(request):
            return Response({'error': 'Invalid signature'}, status=403)
        # ...
```

**优先级：P0（安全基础）**

---

### 3. 数据库 Router（Admin 只读跨站）✅

**评价：完全正确（P1 级别）**

**问题：**
- v1.0.4 规范明确提到 Admin 使用独立连接
- 但我的清单没有列出 Database Router 实现
- 这是 v1.0.4 的核心安全架构

**需要补充：**
```python
# apps/admin/db_router.py

class AdminRouter:
    """
    Admin 数据库路由器（v1.0.4）
    
    规则：
    - Admin API 查询使用 'admin' 连接（绕过 RLS）
    - 其他查询使用 'default' 连接（受 RLS 限制）
    """
    
    admin_models = {'AdminQueryLog'}  # Admin 专用模型
    
    def db_for_read(self, model, **hints):
        """读取路由"""
        # 1. 显式指定 admin_query
        if hints.get('admin_query'):
            return 'admin'
        
        # 2. Admin 专用模型
        if model.__name__ in self.admin_models:
            return 'admin'
        
        # 3. 默认连接
        return 'default'
    
    def db_for_write(self, model, **hints):
        """写入路由（Admin 也走 default，除非特殊模型）"""
        if model.__name__ in self.admin_models:
            return 'admin'
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """允许所有关系（同一数据库物理实例）"""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """迁移总是在 default 上执行"""
        return db == 'default'


# config/settings/base.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER', default='posx_app'),  # ⭐ 普通应用用户
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default=5432),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    },
    'admin': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_ADMIN_USER', default='posx_admin'),  # ⭐ Admin 用户
        'PASSWORD': env('DB_ADMIN_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default=5432),
        'CONN_MAX_AGE': 60,  # 更短的连接时间
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

DATABASE_ROUTERS = ['apps.admin.db_router.AdminRouter']


# apps/admin/api/aggregation.py（使用 Router）

from django.db import connections

def get_orders_aggregation(request):
    """使用 admin 连接进行聚合查询"""
    
    # 方式1：显式使用 admin 连接
    with connections['admin'].cursor() as cursor:
        cursor.execute("SELECT ...")
        results = cursor.fetchall()
    
    # 方式2：通过 Router（推荐）
    from apps.orders.models import Order
    orders = Order.objects.using('admin').all()  # 使用 admin 连接
    
    # 方式3：通过 hint
    orders = Order.objects.db_manager(hints={'admin_query': True}).all()
    
    return Response({'data': results})
```

**优先级：P1（v1.0.4 核心架构）**

---

### 4. RLS 中间件挂载点与命名一致性 ✅

**评价：发现了我的问题（P1 级别）**

**问题：**
- 我的清单中同时出现了：
  - `middleware/site_isolation.py`
  - `apps/core/middleware.py`
- 命名不一致，容易混淆
- 中间件顺序没有明确说明

**需要统一为：**
```
apps/core/
├── middleware/
│   ├── __init__.py
│   ├── site_isolation.py      # ⭐ RLS 设置（必须在 DB 访问前）
│   ├── request_id.py           # ⭐ 请求追踪（最前）
│   ├── error_handler.py        # ⭐ 错误处理（最后）
│   └── logging.py              # ⭐ 日志记录
```

**中间件顺序：**
```python
# config/settings/base.py

MIDDLEWARE = [
    # 1. 请求 ID（最前）
    'apps.core.middleware.request_id.RequestIDMiddleware',
    
    # 2. 安全相关
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    
    # 3. Session/CSRF
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # 4. 通用中间件
    'django.middleware.common.CommonMiddleware',
    
    # 5. 认证
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # 6. ⭐ 站点隔离（在任何 DB 访问前）
    'apps.core.middleware.site_isolation.SiteIsolationMiddleware',
    
    # 7. 其他
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # 8. 错误处理（最后）
    'apps.core.middleware.error_handler.ErrorHandlerMiddleware',
]
```

**优先级：P1（架构清晰度）**

---

### 5. 约束/索引迁移需显式列出 ✅

**评价：非常细致（P0 级别）**

**问题：**
- 我的清单提到了迁移文件，但没有详细列出所有唯一约束
- v1.0.4 规范中提到的约束需要确保都存在

**需要补充迁移文件：**
```python
# apps/orders/migrations/0003_add_unique_constraints.py

from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('orders', '0002_initial_data'),
    ]
    
    operations = [
        # 1. stripe_payment_intent_id 唯一约束
        migrations.AddConstraint(
            model_name='order',
            constraint=models.UniqueConstraint(
                fields=['stripe_payment_intent_id'],
                name='uq_order_stripe_payment_intent'
            ),
        ),
        
        # 2. idempotency_key 唯一约束
        migrations.AddConstraint(
            model_name='order',
            constraint=models.UniqueConstraint(
                fields=['idempotency_key'],
                name='uq_order_idempotency_key'
            ),
        ),
    ]


# apps/allocations/migrations/0003_add_unique_constraints.py

from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('allocations', '0002_add_fireblocks_tx_index'),
    ]
    
    operations = [
        # 1. order_id 唯一约束（每单只有一条分配）
        migrations.AddConstraint(
            model_name='allocation',
            constraint=models.UniqueConstraint(
                fields=['order_id'],
                name='uq_allocation_order'
            ),
        ),
        
        # 2. fireblocks_tx_id 唯一约束（v1.0.4）
        migrations.AddConstraint(
            model_name='allocation',
            constraint=models.UniqueConstraint(
                fields=['fireblocks_tx_id'],
                name='uq_allocation_fireblocks_tx',
                condition=models.Q(fireblocks_tx_id__isnull=False)  # 允许 NULL
            ),
        ),
    ]


# apps/commissions/migrations/0003_add_unique_constraints.py

from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('commissions', '0002_initial_data'),
    ]
    
    operations = [
        # (order_id, agent_id, level) 唯一约束
        migrations.AddConstraint(
            model_name='commission',
            constraint=models.UniqueConstraint(
                fields=['order_id', 'agent_id', 'level'],
                name='uq_commission_order_agent_level'
            ),
        ),
    ]


# apps/users/migrations/0003_add_wallet_constraints.py

from django.db import migrations, models
from django.db.models.functions import Lower

class Migration(migrations.Migration):
    
    dependencies = [
        ('users', '0002_add_nonce_table'),
    ]
    
    operations = [
        # LOWER(address) 唯一索引
        migrations.AddIndex(
            model_name='wallet',
            index=models.Index(
                Lower('address'),
                name='idx_wallet_address_lower'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='wallet',
            constraint=models.UniqueConstraint(
                Lower('address'),
                name='uq_wallet_address_lower'
            ),
        ),
    ]


# apps/webhooks/migrations/0002_add_unique_constraints.py

from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('webhooks', '0001_initial'),
    ]
    
    operations = [
        # (source, external_event_id) 唯一约束（幂等性）
        migrations.AddConstraint(
            model_name='webhooklog',
            constraint=models.UniqueConstraint(
                fields=['source', 'external_event_id'],
                name='uq_webhook_source_event'
            ),
        ),
    ]
```

**优先级：P0（数据完整性）**

---

### 6. 金额精度与 Decimal 全链路 ✅

**评价：正确强调（P0 级别，财务风险）**

**问题：**
- v1.0.4 专门修正了 Stripe 金额浮点误差问题
- 需要确保整个链路都使用 Decimal

**需要确保：**

**数据库：**
```sql
-- 金额字段
list_price_usd NUMERIC(18, 2)
final_price_usd NUMERIC(18, 2)
commission_amount_usd NUMERIC(18, 2)

-- 代币数量（链上精度）
tokens_per_unit NUMERIC(38, 18)
token_amount NUMERIC(38, 18)
```

**后端模型：**
```python
# apps/orders/models.py

from decimal import Decimal

class Order(models.Model):
    list_price_usd = models.DecimalField(
        max_digits=18, 
        decimal_places=2,
        help_text='原价（美元）'
    )
    final_price_usd = models.DecimalField(
        max_digits=18, 
        decimal_places=2,
        help_text='最终价格（美元）'
    )
```

**Serializer：**
```python
# apps/orders/serializers.py

from rest_framework import serializers
from decimal import Decimal

class OrderSerializer(serializers.ModelSerializer):
    # 自动使用 DecimalField，保持精度
    list_price_usd = serializers.DecimalField(max_digits=18, decimal_places=2)
    final_price_usd = serializers.DecimalField(max_digits=18, decimal_places=2)
```

**Stripe 服务（v1.0.4）：**
```python
# apps/orders/services/stripe_service.py

from decimal import Decimal, ROUND_HALF_UP

def to_cents(amount_usd: Decimal) -> int:
    """美元转美分（精确整分）⭐"""
    if not isinstance(amount_usd, Decimal):
        amount_usd = Decimal(str(amount_usd))
    
    # 精确到 0.01 美元
    amount_rounded = amount_usd.quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )
    
    # 转为美分
    return int(amount_rounded * 100)
```

**前端：**
```typescript
// lib/utils/formatters.ts

export function formatUSD(amount: string | number): string {
  // 接收字符串，避免浮点误差
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

// API 调用时使用字符串
const orderData = {
  tier_id: tierId,
  quantity: 10,
  final_price_usd: '1000.50',  // ⭐ 字符串传输
};
```

**优先级：P0（财务安全，不能出错）**

---

### 7. Health & Readiness ✅

**评价：运维必需（P1 级别）**

**问题：**
- 我的清单提到了健康检查，但没有区分 liveness 和 readiness
- Kubernetes 需要两种不同的探针

**需要补充：**

**后端：**
```python
# apps/core/views/health.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
import redis

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    健康检查（Liveness Probe）
    检查进程是否存活
    """
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    就绪检查（Readiness Probe）
    检查服务是否准备好接受流量
    """
    checks = {}
    all_ready = True
    
    # 1. 数据库检查
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        all_ready = False
    
    # 2. Redis 检查
    try:
        cache.set('_health_check', '1', 10)
        cache.get('_health_check')
        checks['redis'] = 'ok'
    except Exception as e:
        checks['redis'] = f'error: {str(e)}'
        all_ready = False
    
    # 3. 迁移检查（可选）
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            checks['migrations'] = f'pending: {len(plan)} migrations'
            all_ready = False
        else:
            checks['migrations'] = 'ok'
    except Exception as e:
        checks['migrations'] = f'error: {str(e)}'
        all_ready = False
    
    status_code = 200 if all_ready else 503
    
    return Response({
        'status': 'ready' if all_ready else 'not_ready',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
    }, status=status_code)


# config/urls.py

urlpatterns = [
    path('health/', health_check, name='health'),
    path('ready/', readiness_check, name='ready'),
    # ...
]
```

**Celery 健康检查：**
```python
# scripts/celery_health_check.py

#!/usr/bin/env python
"""Celery Worker 健康检查脚本"""

import sys
from celery import Celery
from redis import Redis

def check_celery_worker():
    """检查 Celery Worker 是否存活"""
    try:
        # 连接 Redis
        redis_client = Redis.from_url(os.getenv('CELERY_BROKER_URL'))
        redis_client.ping()
        
        # 检查队列
        queue_length = redis_client.llen('celery')
        if queue_length > 10000:  # 队列堆积
            print(f"Queue backlog: {queue_length}")
            sys.exit(1)
        
        print("Celery worker healthy")
        sys.exit(0)
    except Exception as e:
        print(f"Celery worker unhealthy: {e}")
        sys.exit(1)

if __name__ == '__main__':
    check_celery_worker()
```

**K8s 配置：**
```yaml
# k8s/base/backend-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: posx-backend:latest
        ports:
        - containerPort: 8000
        
        # Liveness Probe（进程存活）
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness Probe（服务就绪）
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3


# k8s/base/celery-worker-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  template:
    spec:
      containers:
      - name: celery-worker
        image: posx-backend:latest
        command: ["celery", "-A", "config", "worker", "-l", "info"]
        
        # Liveness Probe（自定义脚本）
        livenessProbe:
          exec:
            command:
            - python
            - /app/scripts/celery_health_check.py
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
```

**前端：**
```typescript
// app/_health/route.ts

export async function GET() {
  return new Response(
    JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
    }),
    {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );
}
```

**优先级：P1（K8s 部署必需）**

---

### 8. Sentry/Logging 完整接入 ✅

**评价：非常重要（P1 级别）**

**问题：**
- 我的清单只列出了日志配置文件位置
- 没有给出具体的配置内容和脱敏规则

**需要补充：**

**Sentry 配置：**
```python
# config/settings/base.py

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        environment=env('DJANGO_ENV', default='production'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
        send_default_pii=False,  # 不发送 PII
        before_send=before_send_sentry,
    )


def before_send_sentry(event, hint):
    """Sentry 事件过滤（脱敏）"""
    # 脱敏钱包地址
    if 'extra' in event:
        for key, value in event['extra'].items():
            if 'wallet' in key.lower() or 'address' in key.lower():
                if isinstance(value, str) and len(value) > 10:
                    event['extra'][key] = f"{value[:6]}...{value[-4:]}"
    
    return event
```

**日志配置：**
```python
# config/logging/production.py

import logging

def get_logging_config():
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s',
            },
            'simple': {
                'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            },
        },
        'filters': {
            'request_id': {
                '()': 'apps.core.logging.RequestIDFilter',
            },
            'user_id': {
                '()': 'apps.core.logging.UserIDFilter',
            },
            'sensitive_filter': {
                '()': 'apps.core.logging.SensitiveDataFilter',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'filters': ['request_id', 'user_id', 'sensitive_filter'],
            },
            'file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/posx/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
                'filters': ['request_id', 'user_id', 'sensitive_filter'],
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'apps': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'celery': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
    }


# apps/core/logging.py

import logging
from django.utils.deprecation import MiddlewareMixin

class RequestIDFilter(logging.Filter):
    """注入请求 ID"""
    def filter(self, record):
        from apps.core.middleware.request_id import get_request_id
        record.request_id = get_request_id() or 'no-request-id'
        return True


class UserIDFilter(logging.Filter):
    """注入用户 ID"""
    def filter(self, record):
        from apps.core.middleware.request_id import get_current_user_id
        record.user_id = get_current_user_id() or 'anonymous'
        return True


class SensitiveDataFilter(logging.Filter):
    """脱敏敏感数据"""
    
    def filter(self, record):
        message = record.getMessage()
        
        # 脱敏钱包地址（0x开头的42字符）
        import re
        message = re.sub(
            r'0x[a-fA-F0-9]{40}',
            lambda m: f"{m.group()[:6]}...{m.group()[-4:]}",
            message
        )
        
        # 脱敏 IP 地址
        message = re.sub(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            lambda m: '.'.join(m.group().split('.')[:2]) + '.xxx.xxx',
            message
        )
        
        record.msg = message
        return True
```

**Admin 审计日志：**
```python
# apps/admin/api/aggregation.py

import logging

logger = logging.getLogger(__name__)

@audit_admin_query  # 装饰器
def get_orders_aggregation(request):
    # 自动写入 AdminQueryLog 表
    # 同时输出到日志（方便集中式审计）
    
    logger.info(
        'Admin aggregation query executed',
        extra={
            'event_type': 'admin_query',
            'query_type': 'orders_aggregation',
            'user_id': str(request.user.user_id),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'duration_ms': 123,
            'row_count': 45,
        }
    )
    
    # ...
```

**优先级：P1（可观测性）**

---

### 9. 依赖清单需落地 ✅

**评价：非常实用（P0 级别）**

**问题：**
- 我的清单只列出了文件位置
- 没有给出具体的依赖包列表

**需要补充：**

**后端依赖：**
```txt
# requirements/base.txt

# Django
Django==4.2.8
djangorestframework==3.14.0
django-environ==0.11.2
django-cors-headers==4.3.1

# Database
psycopg2-binary==2.9.9
dj-database-url==2.1.0

# Celery
celery==5.3.4
redis==5.0.1
django-redis==5.4.0

# Auth & Security
PyJWT==2.8.0
python-jose[cryptography]==3.3.0
cryptography==41.0.7

# Third-party integrations
stripe==7.8.0
requests==2.31.0

# Utilities
python-dotenv==1.0.0
python-dateutil==2.8.2

# API Documentation
drf-spectacular==0.27.0

# Logging
python-json-logger==2.0.7
sentry-sdk==1.39.1

# Production server
gunicorn==21.2.0
uvicorn[standard]==0.25.0

# Testing
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==20.1.0
```

```txt
# requirements/local.txt

-r base.txt

# Development tools
ipython==8.18.1
ipdb==0.13.13
django-debug-toolbar==4.2.0
django-extensions==3.2.3

# Code quality
black==23.12.1
isort==5.13.2
flake8==6.1.0
pylint==3.0.3
pylint-django==2.5.5

# Testing
pytest-xdist==3.5.0
coverage==7.3.3
```

**前端依赖：**
```json
{
  "name": "posx-frontend",
  "version": "1.0.0",
  "dependencies": {
    "next": "^14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.3.3",
    
    "@auth0/nextjs-auth0": "^3.5.0",
    "axios": "^1.6.2",
    "zod": "^3.22.4",
    "react-hook-form": "^7.49.2",
    "@hookform/resolvers": "^3.3.3",
    
    "wagmi": "^2.2.1",
    "viem": "^2.0.6",
    "@web3modal/ethereum": "^2.7.1",
    "@web3modal/react": "^2.7.1",
    
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.2.0",
    
    "date-fns": "^3.0.0",
    "next-themes": "^0.2.1",
    "zustand": "^4.4.7",
    
    "@sentry/nextjs": "^7.91.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.5",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.0.4",
    "prettier": "^3.1.1",
    "prettier-plugin-tailwindcss": "^0.5.9",
    
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

**优先级：P0（项目基础）**

---

### 10. 前端 API 客户端拦截器 ✅

**评价：架构关键（P1 级别）**

**问题：**
- 我的清单有 lib/api/client.ts
- 但没有说明具体实现（拦截器、错误处理等）

**需要补充：**

```typescript
// lib/api/client.ts

import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { v4 as uuidv4 } from 'uuid';
import * as Sentry from '@sentry/nextjs';
import { useAuth } from '@auth0/nextjs-auth0/client';

// API 客户端配置
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  async (config) => {
    // 1. 注入请求 ID
    const requestId = uuidv4();
    config.headers['X-Request-Id'] = requestId;
    
    // 2. 注入站点代码
    const siteCode = getSiteCode(); // 从 Cookie 或域名获取
    config.headers['X-Site-Code'] = siteCode;
    
    // 3. 注入 Auth0 Token
    try {
      const { getAccessTokenSilently } = useAuth();
      const token = await getAccessTokenSilently();
      config.headers['Authorization'] = `Bearer ${token}`;
    } catch (error) {
      // Token 获取失败（可能未登录）
      console.warn('Failed to get access token:', error);
    }
    
    // 4. 日志（开发环境）
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        requestId,
        siteCode,
        data: config.data,
      });
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 成功响应
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API Response] ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
    }
    return response;
  },
  async (error: AxiosError) => {
    const requestId = error.config?.headers['X-Request-Id'];
    
    // 错误处理
    if (error.response) {
      const status = error.response.status;
      
      // 401 Unauthorized - 跳转登录
      if (status === 401) {
        console.error('[API Error] Unauthorized, redirecting to login');
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      // 403 Forbidden
      if (status === 403) {
        console.error('[API Error] Forbidden');
        Sentry.captureException(error, {
          extra: { requestId, status },
        });
        return Promise.reject(error);
      }
      
      // 429 Too Many Requests - 重试
      if (status === 429) {
        const retryAfter = error.response.headers['retry-after'];
        console.warn(`[API Error] Rate limited, retry after ${retryAfter}s`);
        
        // 简单重试逻辑
        if (!error.config?._retry) {
          error.config._retry = true;
          await new Promise(resolve => 
            setTimeout(resolve, (parseInt(retryAfter) || 5) * 1000)
          );
          return apiClient(error.config);
        }
      }
      
      // 5xx Server Error - 上报 Sentry
      if (status >= 500) {
        console.error('[API Error] Server error');
        Sentry.captureException(error, {
          extra: { 
            requestId, 
            status, 
            response: error.response.data 
          },
        });
      }
    } else if (error.request) {
      // 网络错误
      console.error('[API Error] Network error', error.message);
      Sentry.captureException(error, {
        extra: { requestId },
      });
    }
    
    return Promise.reject(error);
  }
);

// 获取站点代码（SSR/Edge 兼容）
function getSiteCode(): string {
  // 1. 从 Cookie 读取（优先）
  if (typeof document !== 'undefined') {
    const match = document.cookie.match(/site_code=([^;]+)/);
    if (match) return match[1];
  }
  
  // 2. 从域名推断（备用）
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname.includes('asia')) return 'ASIA';
    if (hostname.includes('eu')) return 'EU';
  }
  
  // 3. 默认值
  return process.env.NEXT_PUBLIC_SITE_CODE || 'NA';
}

export default apiClient;


// lib/api/endpoints.ts

export const API_ENDPOINTS = {
  // 用户
  ME: '/v1/users/me',
  TOKEN_BALANCE: '/v1/users/me/token-balance',
  
  // 订单
  ORDERS: '/v1/orders',
  ORDER_DETAIL: (id: string) => `/v1/orders/${id}`,
  
  // 档位
  TIERS: '/v1/tiers',
  TIER_DETAIL: (id: string) => `/v1/tiers/${id}`,
  
  // 钱包
  WALLETS: '/v1/wallets',
  WALLET_DETAIL: (id: string) => `/v1/wallets/${id}`,
  WALLET_SET_PRIMARY: (id: string) => `/v1/wallets/${id}/set-primary`,
  
  // 认证
  AUTH_NONCE: '/v1/auth/nonce',
  AUTH_WALLET_LOGIN: '/v1/auth/wallet-login',
};
```

**优先级：P1（前端架构基础）**

---

### 11. Webhook 安全落地 ✅

**评价：安全关键（P0 级别）**

**问题：**
- 我的清单有 webhook 服务文件
- 但没有强调安全实现细节

**需要确保：**

```python
# apps/webhooks/views.py

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
import stripe
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Stripe Webhook 处理
    
    安全措施：
    1. @csrf_exempt（Webhook 不需要 CSRF）
    2. 签名验证（替代 CSRF）
    3. 幂等性（webhook_logs 表）
    4. 异步处理（快速 200）
    """
    
    authentication_classes = []  # Webhook 不需要认证
    permission_classes = []
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # 1. ⭐ 签名验证（关键安全措施）
        try:
            event = stripe.Webhook.construct_event(
                payload, 
                sig_header, 
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error('Stripe webhook: Invalid payload')
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            logger.error('Stripe webhook: Invalid signature')
            return Response({'error': 'Invalid signature'}, status=403)
        
        # 2. ⭐ 幂等性检查（防止重复处理）
        from apps.webhooks.models import WebhookLog
        
        webhook_log, created = WebhookLog.objects.get_or_create(
            source='stripe',
            external_event_id=event['id'],
            defaults={
                'event_type': event['type'],
                'payload': event,
                'status': 'received',
            }
        )
        
        if not created:
            # 已处理过
            logger.info(f'Stripe webhook: Duplicate event {event["id"]}')
            return Response({'status': 'duplicate'}, status=200)
        
        # 3. ⭐ 异步处理（快速返回 200）
        from apps.webhooks.tasks import process_stripe_webhook
        
        process_stripe_webhook.delay(event['id'], event['type'], event)
        
        logger.info(f'Stripe webhook: Queued event {event["id"]} ({event["type"]})')
        
        return Response({'status': 'received'}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class FireblocksWebhookView(APIView):
    """
    Fireblocks Webhook 处理
    
    安全措施：
    1. @csrf_exempt
    2. RSA-SHA512 签名验证
    3. 幂等性
    4. 异步处理
    """
    
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        payload = request.body
        signature = request.META.get('HTTP_X_FIREBLOCKS_SIGNATURE')
        
        # 1. ⭐ RSA-SHA512 签名验证
        if not self.verify_signature(payload, signature):
            logger.error('Fireblocks webhook: Invalid signature')
            return Response({'error': 'Invalid signature'}, status=403)
        
        # 2. 解析事件
        import json
        event = json.loads(payload)
        event_id = event.get('id')
        event_type = event.get('type')
        
        # 3. ⭐ 幂等性检查
        from apps.webhooks.models import WebhookLog
        
        webhook_log, created = WebhookLog.objects.get_or_create(
            source='fireblocks',
            external_event_id=event_id,
            defaults={
                'event_type': event_type,
                'payload': event,
                'status': 'received',
            }
        )
        
        if not created:
            logger.info(f'Fireblocks webhook: Duplicate event {event_id}')
            return Response({'status': 'duplicate'}, status=200)
        
        # 4. ⭐ 异步处理
        from apps.webhooks.tasks import process_fireblocks_webhook
        
        process_fireblocks_webhook.delay(event_id, event_type, event)
        
        logger.info(f'Fireblocks webhook: Queued event {event_id} ({event_type})')
        
        return Response({'status': 'received'}, status=200)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """验证 Fireblocks 签名（RSA-SHA512）"""
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        import base64
        
        try:
            # 加载公钥
            public_key_pem = settings.FIREBLOCKS_WEBHOOK_PUBLIC_KEY
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # 解码签名
            signature_bytes = base64.b64decode(signature)
            
            # 验证
            public_key.verify(
                signature_bytes,
                payload,
                padding.PKCS1v15(),
                hashes.SHA512()
            )
            
            return True
        except Exception as e:
            logger.error(f'Fireblocks signature verification failed: {e}')
            return False


# config/urls.py

urlpatterns = [
    path('api/v1/webhooks/stripe', StripeWebhookView.as_view()),
    path('api/v1/webhooks/fireblocks', FireblocksWebhookView.as_view()),
    # ...
]
```

**优先级：P0（安全和数据完整性）**

---

### 12. Docker & Compose 健康检查 ✅

**评价：工程细节（P1 级别）**

**问题：**
- 我的清单有 Docker 配置文件
- 但没有详细说明健康检查、等待脚本等

**需要补充：**

**docker-compose.yml：**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: posx_local
      POSTGRES_USER: posx
      POSTGRES_PASSWORD: posx
      TZ: UTC
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:  # ⭐ 健康检查
      test: ["CMD-SHELL", "pg_isready -U posx"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:  # ⭐ 健康检查
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
  
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: >
      sh -c "
        python manage.py wait_for_db &&
        python manage.py migrate &&
        gunicorn config.wsgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
      "
    environment:
      DJANGO_ENV: local
      DEBUG: "true"
      DATABASE_URL: postgresql://posx:posx@postgres:5432/posx_local
      REDIS_URL: redis://redis:6379/0
      PYTHONUNBUFFERED: "1"  # ⭐ 立即输出日志
      TZ: UTC
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy  # ⭐ 等待 postgres 健康
      redis:
        condition: service_healthy  # ⭐ 等待 redis 健康
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A config worker -l info
    environment:
      DJANGO_ENV: local
      DATABASE_URL: postgresql://posx:posx@postgres:5432/posx_local
      REDIS_URL: redis://redis:6379/0
      PYTHONUNBUFFERED: "1"
      TZ: UTC
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    command: npm run dev
    environment:
      NODE_ENV: development
      NEXT_PUBLIC_API_URL: http://localhost:8000/api
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"

volumes:
  postgres_data:
```

**等待数据库脚本：**
```python
# apps/core/management/commands/wait_for_db.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import time

class Command(BaseCommand):
    """等待数据库就绪"""
    
    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        retries = 30
        
        while retries > 0:
            try:
                db_conn = connection.cursor()
                break
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
                retries -= 1
        
        if db_conn:
            self.stdout.write(self.style.SUCCESS('Database available!'))
        else:
            self.stdout.write(self.style.ERROR('Database unavailable!'))
            raise Exception('Could not connect to database')
```

**Dockerfile（后端）：**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements/base.txt requirements/local.txt ./requirements/
RUN pip install --upgrade pip && \
    pip install -r requirements/local.txt

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 posx && \
    chown -R posx:posx /app

USER posx

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**优先级：P1（本地开发和部署基础）**

---

### 13. 建议收敛（结构/一致性）✅

**评价：架构优化（P1-P2 级别）**

**建议都非常合理：**

1. **中间件目录统一**
   - ✅ 只使用 `apps/core/middleware/`
   - 子文件：`site_isolation.py`, `request_id.py`, `error_handler.py`, `logging.py`

2. **Admin 聚合**
   - ✅ 采用 v1.0.4 的"内部 Admin API + 审计 + 限流"
   - 避免在前台进程使用特权连接

3. **文档完善**
   - ✅ `docs/DEPLOYMENT.md` 需要：
     - 数据库迁移顺序（CONCURRENT 索引 → RLS 策略）
     - 蓝绿/金丝雀部署步骤
     - 回滚脚本（温和/完全两套）

4. **Makefile 统一命令**
   ```makefile
   # Makefile
   
   .PHONY: up down migrate seed test lint deploy
   
   up:
   	docker-compose up -d
   
   down:
   	docker-compose down
   
   migrate:
   	docker-compose exec backend python manage.py migrate
   
   seed:
   	docker-compose exec backend python manage.py seed_data
   
   test:
   	docker-compose exec backend pytest
   
   lint:
   	docker-compose exec backend black . && isort . && flake8 .
   
   deploy:
   	./scripts/deploy.sh
   
   logs:
   	docker-compose logs -f
   
   shell:
   	docker-compose exec backend python manage.py shell_plus
   ```

**优先级：P1-P2（工程质量）**

---

## 📊 总评

### ⭐⭐⭐⭐⭐ (5/5)

**评审者水平：资深架构师级别**

**优点：**
1. ✅ 非常细致，发现了我清单中的多个疏漏
2. ✅ 对 Django/DRF 生态非常熟悉
3. ✅ 理解微服务架构和容器化部署
4. ✅ 关注安全细节（CSRF、签名验证、脱敏）
5. ✅ 关注工程质量（一致性、可维护性、可观测性）
6. ✅ 发现了命名不一致问题（中间件路径）
7. ✅ 强调了 v1.0.4 的核心架构（Admin Router、RLS）

**所有 13 条建议都非常有道理，应该全部采纳！**

---

## 🎯 补充后的优先级

### P0 - 立即补充（6个）
1. DRF 全局配置
2. CORS/CSRF 安全配置
3. 约束/索引迁移（完整列表）
4. Decimal 全链路（金额精度）
5. Webhook 安全实现
6. 依赖清单（具体包列表）

### P1 - 短期补充（7个）
7. Database Router（Admin 隔离）
8. 中间件统一（命名和顺序）
9. Health/Readiness 探针
10. Sentry/Logging 完整配置
11. API 客户端拦截器
12. Docker 健康检查
13. 结构收敛和文档完善

---

## 📝 下一步行动

1. **立即更新清单文档**（补充以上 13 条内容）
2. **创建详细的配置文件示例**（DRF、安全、日志等）
3. **统一中间件路径**（apps/core/middleware/）
4. **补充迁移文件**（所有唯一约束）
5. **完善文档**（DEPLOYMENT.md、迁移顺序、回滚脚本）
6. **添加 Makefile**（统一命令入口）

这些都是非常专业和实用的建议！
