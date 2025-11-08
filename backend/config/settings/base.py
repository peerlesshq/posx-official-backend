"""
Base settings for POSX
Shared across all environments
"""
import os
from pathlib import Path
import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# ============================================
# 核心检查点 #3: CSRF 与 API 路由一致性 ⭐
# ============================================

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'corsheaders',
    'csp',
    'django_filters',
    
    # Local apps
    'apps.core',
    'apps.users',
    'apps.sites',
    'apps.tiers',
    'apps.orders',
    'apps.allocations',
    'apps.commissions',
    'apps.webhooks',
    'apps.admin',
    'apps.commission_plans',
    'apps.agents',
    'apps.orders_snapshots',
]

# ============================================
# 核心检查点 #3: CSRF 智能豁免中间件 ⭐
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    # ⭐ CSRF 豁免中间件（在 CsrfViewMiddleware 之前）
    'config.middleware.csrf_exempt.CSRFExemptMiddleware',
    
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # CSP middleware
    'csp.middleware.CSPMiddleware',
    
    # Custom middleware
    'apps.core.middleware.site_context.SiteContextMiddleware',
    'apps.core.middleware.request_id.RequestIDMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================
# 核心检查点 #4: WSGI/ASGI 配置 ⭐
# ============================================
# 使用 WSGI（标准 Django + Gunicorn）
WSGI_APPLICATION = 'config.wsgi.application'

# 如果需要 WebSocket/异步，使用 ASGI：
# ASGI_APPLICATION = 'config.asgi.application'

# ============================================
# Database (base config, override in env-specific)
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='posx_local'),
        'USER': env('DB_USER', default='posx_app'),
        'PASSWORD': env('DB_PASSWORD', default='posx'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# ============================================
# Password validation
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================
# Internationalization
# ============================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ============================================
# Static files
# ============================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================
# Default primary key field type
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# REST Framework
# ============================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.core.authentication.Auth0JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ============================================
# Celery Configuration
# ============================================
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# ============================================
# Auth0 Configuration
# ============================================
AUTH0_DOMAIN = env('AUTH0_DOMAIN', default='')
AUTH0_AUDIENCE = env('AUTH0_AUDIENCE', default='')
AUTH0_ISSUER = env('AUTH0_ISSUER', default='')
AUTH0_ALGORITHMS = ['RS256']

# JWKS Caching（核心检查点 #6 相关）
AUTH0_JWKS_CACHE_TTL = 3600  # 1 hour
AUTH0_JWT_LEEWAY = 10  # 10 seconds tolerance

# ⚠️ 启动时校验 Auth0 配置（见 apps/core/apps.py）
AUTH0_REQUIRED_SETTINGS = ['AUTH0_DOMAIN', 'AUTH0_AUDIENCE', 'AUTH0_ISSUER']

# ============================================
# SIWE (Sign-In with Ethereum) Configuration
# ============================================
SIWE_DOMAIN = env('SIWE_DOMAIN', default='posx.io')
SIWE_CHAIN_ID = env.int('SIWE_CHAIN_ID', default=1)  # 1=Ethereum Mainnet
SIWE_URI = env('SIWE_URI', default='https://posx.io')

# ============================================
# Application Configuration
# ============================================
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')
ALLOWED_SITE_CODES = env.list('ALLOWED_SITE_CODES', default=['NA', 'ASIA'])

# Nonce configuration
NONCE_TTL_SECONDS = env.int('NONCE_TTL_SECONDS', default=300)  # 5 minutes

# Idempotency key retention
IDEMPOTENCY_KEY_RETENTION_HOURS = env.int('IDEMPOTENCY_KEY_RETENTION_HOURS', default=48)

# Order timeout
ORDER_EXPIRE_MINUTES = env.int('ORDER_EXPIRE_MINUTES', default=15)

# Order quantity limits
MAX_QUANTITY_PER_ORDER = env.int('MAX_QUANTITY_PER_ORDER', default=1000)

# Commission hold period
COMMISSION_HOLD_DAYS = env.int('COMMISSION_HOLD_DAYS', default=7)

# Environment (for Redis keys)
ENV = env('ENV', default='dev')  # prod, dev, test

# ============================================
# Stripe Configuration
# ============================================
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

# Stripe Mock Mode (development/testing)
MOCK_STRIPE = env.bool('MOCK_STRIPE', default=False)

# ============================================
# Fireblocks Configuration
# ============================================
FIREBLOCKS_API_KEY = env('FIREBLOCKS_API_KEY', default='')
FIREBLOCKS_PRIVATE_KEY = env('FIREBLOCKS_PRIVATE_KEY', default='')
FIREBLOCKS_BASE_URL = env('FIREBLOCKS_BASE_URL', default='https://sandbox-api.fireblocks.io')
FIREBLOCKS_VAULT_ACCOUNT_ID = env('FIREBLOCKS_VAULT_ACCOUNT_ID', default='0')
FIREBLOCKS_ASSET_ID = env('FIREBLOCKS_ASSET_ID', default='ETH_TEST')
FIREBLOCKS_WEBHOOK_PUBLIC_KEY = env('FIREBLOCKS_WEBHOOK_PUBLIC_KEY', default='')

# ============================================
# 核心检查点 #3: CSRF 豁免路径配置 ⭐
# ============================================
CSRF_EXEMPT_PATHS = [
    '/api/v1/',
    '/health/',
    '/ready/',
    '/version/',
    '/api/v1/webhooks/',  # Webhook endpoints
]
