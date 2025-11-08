"""
Local Development settings for POSX
宽松的 CSP 以便开发
"""
from .base import *

# ============================================
# 核心设置
# ============================================
DEBUG = True

ALLOWED_HOSTS = ['*']  # 开发环境允许所有主机

SECRET_KEY = env('SECRET_KEY', default='dev-secret-key-change-in-production')

# ============================================
# 开发环境 CSP（包含 unsafe-inline）
# ============================================
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # ⭐ 开发环境允许 inline scripts
    "'unsafe-eval'",    # ⭐ 开发环境允许 eval（某些工具需要）
    "https://cdn.jsdelivr.net",
    "https://js.stripe.com",
    "https://unpkg.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # ⭐ 开发环境允许 inline styles
    "https://cdn.jsdelivr.net",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)
CSP_FONT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.stripe.com",
    "ws://localhost:3000",  # Next.js HMR
)
CSP_FRAME_SRC = (
    "'self'",
    "https://js.stripe.com",
)

# ============================================
# CORS（宽松）
# ============================================
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:3000', 'http://127.0.0.1:3000']
)
CORS_ALLOW_CREDENTIALS = True

# ============================================
# Database
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='posx_local'),
        'USER': env('DB_USER', default='posx_app'),
        'PASSWORD': env('DB_PASSWORD', default='posx'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            'options': '-c search_path=public',
        },
    }
}

# ============================================
# Caching（简单）
# ============================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ============================================
# Logging（开发级）
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
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
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ============================================
# Celery（开发配置）
# ============================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)

# ============================================
# Email（Console Backend）
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================
# Debug Toolbar（可选）
# ============================================
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        pass
