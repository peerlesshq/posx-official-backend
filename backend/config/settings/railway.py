"""
Railway Demo Environment Settings for POSX
针对 Railway 平台优化的配置

⭐ 关键特性：
- 移除 AWS S3 依赖（使用本地静态文件）
- 使用 Railway 提供的 DATABASE_URL 和 REDIS_URL
- 简化日志配置（仅 console）
- Mock 模式支付和区块链服务
- 自动 HTTPS 和域名配置
"""
from .base import *  # noqa
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# ============================================
# 环境标识
# ============================================
ENV = "railway-demo"

# ============================================
# 安全配置
# ============================================
DEBUG = False
SECRET_KEY = env('SECRET_KEY')

# Railway 自动提供域名，支持多域名
ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=['*.up.railway.app', 'localhost', '127.0.0.1']
)

# ⭐ CSRF Trusted Origins（必须配置前端域名）
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[]
)

# ============================================
# 数据库配置（Railway PostgreSQL）
# ============================================
# Railway 自动提供 DATABASE_URL
database_url = env('DATABASE_URL', default=None)

# 检查 DATABASE_URL 是否有效（不是 None 也不是空字符串）
if database_url and database_url.strip():
    # 使用 Railway 提供的 DATABASE_URL
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Fallback: 如果 DATABASE_URL 未设置，抛出清晰的错误
    import sys
    import os
    
    print("=" * 80, file=sys.stderr)
    print("❌ DATABASE_URL 环境变量未设置！", file=sys.stderr)
    print("", file=sys.stderr)
    print("请检查 Railway 配置：", file=sys.stderr)
    print("1. Postgres Service 是否已创建并运行？", file=sys.stderr)
    print("2. Postgres 变量是否已引用到此 Service？", file=sys.stderr)
    print("   进入 Backend Service → Variables", file=sys.stderr)
    print("   添加: DATABASE_URL=${{Postgres-FHHx.DATABASE_URL}}", file=sys.stderr)
    print("", file=sys.stderr)
    print("当前环境变量:", file=sys.stderr)
    for key in sorted(os.environ.keys()):
        if 'PG' in key or 'DATA' in key or 'RAILWAY' in key:
            value = os.environ[key]
            # 隐藏密码
            if 'PASSWORD' in key or 'SECRET' in key:
                value = '*' * 8
            print(f"  {key} = {value[:50]}...", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    
    raise ImproperlyConfigured(
        "DATABASE_URL is required. Please connect Postgres service to this Railway service."
    )

# ============================================
# Redis & Celery（Railway Redis）
# ============================================
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,  # Railway 资源限制
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_TASK_ALWAYS_EAGER = False

# ============================================
# 静态文件（本地存储，不使用 S3）⭐
# ============================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# 覆盖 base.py 中的 STATICFILES_DIRS（Railway 环境中该目录不存在）
STATICFILES_DIRS = []

# WhiteNoise for static files serving
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================
# HTTPS & Security Headers
# ============================================
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Railway 自动处理 HSTS，保守配置
SECURE_HSTS_SECONDS = 0  # 由 Railway 处理
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ============================================
# CSP（生产级严格模式）⭐
# ============================================
CSP_DEFAULT_SRC = ("'none'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://js.stripe.com",
)
CSP_STYLE_SRC = (
    "'self'",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)
CSP_FONT_SRC = (
    "'self'",
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.stripe.com",
)
CSP_FRAME_SRC = (
    "'self'",
    "https://js.stripe.com",
)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# ============================================
# CORS
# ============================================
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['https://posx.retool.com']
)
CORS_ALLOW_CREDENTIALS = True

# ============================================
# 日志配置（Railway 专用）⭐
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
        'simple': {
            'format': '[{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================
# Auth0
# ============================================
AUTH0_DOMAIN = env('AUTH0_DOMAIN')
AUTH0_AUDIENCE = env('AUTH0_AUDIENCE')
AUTH0_ISSUER = env('AUTH0_ISSUER')
AUTH0_ALGORITHMS = ['RS256']
AUTH0_JWT_LEEWAY = 60

# ============================================
# SIWE（测试网）
# ============================================
SIWE_DOMAIN = env('SIWE_DOMAIN', default='posx.io')
SIWE_CHAIN_ID = env.int('SIWE_CHAIN_ID', default=8453)  # Base 主网
SIWE_URI = env('SIWE_URI')

# ============================================
# Stripe（Mock 或测试密钥）⭐
# ============================================
MOCK_STRIPE = env.bool('MOCK_STRIPE', default=True)
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='sk_test_placeholder')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='pk_test_placeholder')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='whsec_placeholder')

# ============================================
# Fireblocks（Mock 模式）⭐
# ============================================
FIREBLOCKS_MODE = env('FIREBLOCKS_MODE', default='MOCK')
ALLOW_PROD_TX = False
FIREBLOCKS_BASE_URL = env(
    'FIREBLOCKS_BASE_URL',
    default='https://sandbox-api.fireblocks.io'
)
FIREBLOCKS_API_KEY = env('FIREBLOCKS_API_KEY', default='mock_api_key')
FIREBLOCKS_PRIVATE_KEY = env('FIREBLOCKS_PRIVATE_KEY', default='mock_private_key')
FIREBLOCKS_VAULT_ACCOUNT_ID = env('FIREBLOCKS_VAULT_ACCOUNT_ID', default='0')
FIREBLOCKS_ASSET_ID = env('FIREBLOCKS_ASSET_ID', default='ETH_TEST')
FIREBLOCKS_WEBHOOK_PUBLIC_KEY = env('FIREBLOCKS_WEBHOOK_PUBLIC_KEY', default='')

# ============================================
# Email（Console 后端）⭐
# ============================================
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@posx.io')

# ============================================
# Sentry（可选）
# ============================================
SENTRY_DSN = env('SENTRY_DSN', default=None)
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
        send_default_pii=False,
        environment='railway-demo',
    )

# ============================================
# 应用配置
# ============================================
FRONTEND_URL = env('FRONTEND_URL', default='https://adminhq.posx.io')
API_EXTERNAL_URL = env('API_EXTERNAL_URL', default='')  # Railway 自动生成
ALLOWED_SITE_CODES = env.list('ALLOWED_SITE_CODES', default=['NA', 'ASIA'])

# 业务配置
NONCE_TTL_SECONDS = env.int('NONCE_TTL_SECONDS', default=300)
ORDER_EXPIRE_MINUTES = env.int('ORDER_EXPIRE_MINUTES', default=15)
MAX_QUANTITY_PER_ORDER = env.int('MAX_QUANTITY_PER_ORDER', default=1000)
IDEMPOTENCY_KEY_RETENTION_HOURS = env.int('IDEMPOTENCY_KEY_RETENTION_HOURS', default=48)
COMMISSION_HOLD_DAYS = env.int('COMMISSION_HOLD_DAYS', default=7)

# ============================================
# Railway 特定配置
# ============================================
# Railway 自动注入 PORT 环境变量
PORT = env.int('PORT', default=8000)

# 禁用某些生产功能（Demo 环境）
SECURE_SSL_REDIRECT = False  # Railway 在负载均衡层处理
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

