"""
Demo/Staging Environment Settings for POSX
继承 production.py,使用测试网与测试密钥
"""
from .production import *  # noqa

# ============================================
# 环境标识
# ============================================
ENV = "demo"

# ============================================
# 域名配置
# ============================================
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['demo.posx.io'])

# ⭐ CSRF Trusted Origins (与前端域名一致)
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['https://demo.posx.io']
)

# ============================================
# 区块链配置(测试网)
# ============================================
SIWE_CHAIN_ID = 11155111  # Sepolia 测试网

# ============================================
# Stripe(测试密钥)
# ============================================
# 从 .env 读取,确保使用 sk_test_* 开头的密钥
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')  # sk_test_xxx
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')  # pk_test_xxx
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')  # whsec_xxx

# ============================================
# Fireblocks(Sandbox API)
# ============================================
FIREBLOCKS_BASE_URL = 'https://sandbox-api.fireblocks.io'

# ============================================
# Sentry(Demo 环境)
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
        environment='demo',  # ⭐ Demo 环境标识
    )

# ============================================
# CORS(Demo 前端)
# ============================================
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['https://demo.posx.io']
)

# ============================================
# 其余配置继承 production.py
# ============================================
# - 安全头(SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE 等)
# - CSP 策略(无 unsafe-inline)
# - Auth0 配置(从 .env 读取 staging tenant)
# - 数据库/Redis 配置

