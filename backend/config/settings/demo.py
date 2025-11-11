"""
Demo/Staging Environment Settings for POSX
继承 production.py,使用测试网与测试密钥

⭐ 关键增强：
- 反向代理头配置
- Auth0 严格校验（RS256 + Clock Skew）
- HSTS 保守配置（不含子域）
- CORS 后端白名单
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
# CORS(Demo 前端) ⭐
# ============================================
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['https://posx.retool.com', 'https://adminhq.posx.io']
)
CORS_ALLOW_CREDENTIALS = True  # 允许携带 Cookie

# ============================================
# 反向代理头配置 ⭐
# ============================================
# Caddy 会设置这些头，Django 需要识别
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ============================================
# HSTS 配置（Demo 环境保守策略）⭐
# ============================================
# 覆盖 production.py 的配置
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # Demo 不包含子域
SECURE_HSTS_PRELOAD = False  # Demo 不预加载

# ============================================
# Auth0 严格校验 ⭐
# ============================================
# 确保仅使用 RS256，拒绝 HS256
AUTH0_ALGORITHMS = ['RS256']

# Clock skew 容忍度（避免时间漂移导致 401）
AUTH0_JWT_LEEWAY = 60  # 60 秒

# ============================================
# 其余配置继承 production.py
# ============================================
# - 安全头: SECURE_PROXY_SSL_HEADER, SECURE_SSL_REDIRECT
# - Cookie 安全: SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE
# - CSP 策略(无 unsafe-inline)
# - Auth0 配置(从 .env 读取 Demo tenant)
# - 数据库/Redis 配置

