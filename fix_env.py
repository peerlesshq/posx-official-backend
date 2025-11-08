#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新生成格式正确的 .env 文件
"""

env_content = """# ============================================
# POSX 开发环境配置
# 生成日期：2025-11-08
# ============================================

# ============================================
# Django 核心配置
# ============================================
SECRET_KEY=django-insecure-Gnmt-VgUUAGxdkK8WEz5FED1E5xo8mUM3XjmHe_w7WyzY8GpJ7F0Tb41oC33G0C86x0
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.local

# ============================================
# 数据库配置
# ============================================
DB_NAME=posx_local
DB_USER=posx_app
DB_PASSWORD=posx
DB_HOST=localhost
DB_PORT=5432

# 数据库URL（作为兜底，优先级高于单独配置）
DATABASE_URL=postgresql://posx_app:posx@localhost:5432/posx_local

# ============================================
# Redis 配置（Docker）
# ============================================
REDIS_URL=redis://localhost:6379/0

# ============================================
# Auth0 配置
# ⚠️ 核对：必须与控制台 Identifier 完全一致！
# ============================================
AUTH0_DOMAIN=dev-posx.us.auth0.com
AUTH0_AUDIENCE=http://localhost:8000/api/v1/
AUTH0_ISSUER=https://dev-posx.us.auth0.com/

# ============================================
# SIWE 配置（钱包认证）
# ============================================
SIWE_DOMAIN=localhost
SIWE_CHAIN_ID=11155111
SIWE_URI=http://localhost:3000

# ============================================
# Stripe 配置
# ⚠️ 核对：每次 stripe listen 重启后检查 whsec_***
# ============================================
STRIPE_SECRET_KEY=sk_test_51S2xgKBQfsnFAkTsQMTaJB9wlnzA0s4OGFLT7KXUAyszpPKNzR5TSOBayiRHgGwd0BDuOlz2UljSTw2PRKbQB3TZ00R0aR8NRT
STRIPE_PUBLISHABLE_KEY=pk_test_51S2xgKBQfsnFAkTsV2fr6fhNXjxCpKP9K75i00iW7rFTQxct7wqZcdjnbJHtJAyCs3OjKM7SeG26jCGq9H4v3X8E00aXNPiAOC
STRIPE_WEBHOOK_SECRET=whsec_4b0b79987be979c07fe98e3df7d7353bb2a7ae5cc0227d0f01083c174120dbf9
MOCK_STRIPE=false

# ============================================
# 订单配置
# ============================================
ENV=local
NONCE_TTL_SECONDS=300
ORDER_EXPIRE_MINUTES=15
MAX_QUANTITY_PER_ORDER=1000

# ============================================
# Celery 配置
# ============================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false

# ============================================
# 前端配置
# ============================================
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_SITE_CODES=NA,ASIA
WALLETCONNECT_PROJECT_ID=cbc675a7819dd3d4bcc1c8c75bc16d86

# ============================================
# Fireblocks 配置（Phase D使用，暂时留空）
# ============================================
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=ETH_TEST
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=

# ============================================
# 其他配置
# ============================================
IDEMPOTENCY_KEY_RETENTION_HOURS=48
COMMISSION_HOLD_DAYS=7
"""

# 写入 .env 文件
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ .env 文件已重新生成（格式正确）")
print("\n关键配置项：")
print("  ✅ ENV=local")
print("  ✅ DATABASE_URL=postgresql://...")
print("  ✅ CSRF_TRUSTED_ORIGINS=http://localhost:3000,...")
print("  ✅ AUTH0_AUDIENCE=http://localhost:8000/api/v1/")
print("  ✅ STRIPE_WEBHOOK_SECRET=whsec_4b0b7998...")

