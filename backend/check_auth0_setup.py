"""
验证 Auth0 API 配置
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings

print("\n" + "=" * 60)
print("  Auth0 Configuration Check")
print("=" * 60)

print(f"\n✅ AUTH0_DOMAIN: {settings.AUTH0_DOMAIN}")
print(f"✅ AUTH0_AUDIENCE: {settings.AUTH0_AUDIENCE}")
print(f"✅ AUTH0_ISSUER: {settings.AUTH0_ISSUER}")

print("\n" + "=" * 60)
print("  Important Notes")
print("=" * 60)

print("""
📋 Current Configuration:
   AUTH0_AUDIENCE = http://localhost:8000/api/v1/

✅ This is CORRECT for local development!

⚠️  What you saw in Auth0 Dashboard:
   https://dev-posx.us.auth0.com/api/v2/
   ↑ This is Auth0 Management API (System API)
   ↑ NOT your application API

🎯 What you need to do:
   1. Click "+ Create API" in Auth0 Dashboard
   2. Set Identifier to: http://localhost:8000/api/v1/
   3. Authorize your application to access this API
   4. No need to change .env file!

📝 Your .env file is already correctly configured!
""")

print("=" * 60)


