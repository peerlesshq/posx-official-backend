"""
Production settings for POSX
✅ 核心检查点 #2: 生产 CSP 配置
"""
from .base import *

# ============================================
# 核心设置
# ============================================
DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

SECRET_KEY = env('SECRET_KEY')

# ============================================
# 核心检查点 #2: 生产级 CSP（无 unsafe-inline）⭐
# ============================================

# Content Security Policy（生产环境严格模式）
CSP_DEFAULT_SRC = ("'none'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://js.stripe.com",
    "https://unpkg.com",  # 如果需要
)
CSP_STYLE_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",  # 允许 HTTPS 图片
)
CSP_FONT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.stripe.com",
)
CSP_FRAME_SRC = (
    "'self'",
    "https://js.stripe.com",
)

# ⭐ 额外安全头（核心检查点 #2）
CSP_FRAME_ANCESTORS = ("'none'",)  # 防止被嵌套
CSP_OBJECT_SRC = ("'none'",)  # 禁止 object/embed
CSP_BASE_URI = ("'self'",)  # 限制 base 标签
CSP_FORM_ACTION = ("'self'",)  # 限制表单提交

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ============================================
# HTTPS / Security Headers
# ============================================
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ============================================
# CORS
# ============================================
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['https://posx.io', 'https://www.posx.io']
)
CORS_ALLOW_CREDENTIALS = True

# ============================================
# Database
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER', default='posx_app'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c search_path=public',
        },
    }
}

# ============================================
# Static Files & Media（核心检查点 #5）
# ============================================
STATIC_ROOT = '/var/www/static/'
MEDIA_ROOT = '/var/www/media/'

# 如果使用 S3/CloudFront
if env.bool('USE_S3', default=False):
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# ============================================
# Caching
# ============================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

# ============================================
# Logging（生产级）
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/posx/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
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
    },
}

# ============================================
# Sentry（可选但推荐）
# ============================================
if env('SENTRY_DSN', default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
        send_default_pii=False,
        environment='production',
    )

# ============================================
# Celery（生产配置）
# ============================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 4

# ============================================
# Email（生产）
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@posx.io')

# ============================================
# Auth0（生产）
# ============================================
AUTH0_DOMAIN = env('AUTH0_DOMAIN')
AUTH0_AUDIENCE = env('AUTH0_AUDIENCE')
AUTH0_ISSUER = env('AUTH0_ISSUER')

# ============================================
# 第三方服务（生产密钥）
# ============================================
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')  # sk_live_xxx
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')  # pk_live_xxx
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')  # whsec_xxx

FIREBLOCKS_API_KEY = env('FIREBLOCKS_API_KEY')
FIREBLOCKS_PRIVATE_KEY = env('FIREBLOCKS_PRIVATE_KEY')
FIREBLOCKS_BASE_URL = 'https://api.fireblocks.io'
FIREBLOCKS_VAULT_ACCOUNT_ID = env('FIREBLOCKS_VAULT_ACCOUNT_ID')

# ============================================
# 应用特定配置
# ============================================
FRONTEND_URL = env('FRONTEND_URL', default='https://posx.io')
ALLOWED_SITE_CODES = env.list('ALLOWED_SITE_CODES', default=['NA', 'ASIA'])
