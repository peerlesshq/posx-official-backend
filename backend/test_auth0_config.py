"""
Auth0 Configuration Test Script
验证 Auth0 配置是否正确加载
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings

print("\n" + "=" * 60)
print("  Auth0 Configuration Check")
print("=" * 60)

# 检查配置
configs = {
    'AUTH0_DOMAIN': getattr(settings, 'AUTH0_DOMAIN', None),
    'AUTH0_AUDIENCE': getattr(settings, 'AUTH0_AUDIENCE', None),
    'AUTH0_ISSUER': getattr(settings, 'AUTH0_ISSUER', None),
}

print("\nConfiguration Values:")
for key, value in configs.items():
    if value:
        # 隐藏敏感信息的部分
        display_value = value
        if 'SECRET' in key or 'SECRET' in str(value):
            display_value = '*' * len(str(value))
        print(f"  ✅ {key}: {display_value}")
    else:
        print(f"  ❌ {key}: Not configured")

# 检查环境变量
print("\nEnvironment Variables:")
env_vars = ['AUTH0_DOMAIN', 'AUTH0_AUDIENCE', 'AUTH0_ISSUER', 'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET']
for var in env_vars:
    value = os.environ.get(var, None)
    if value:
        if 'SECRET' in var:
            display_value = '*' * len(value)
        else:
            display_value = value
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ⚠️  {var}: Not set")

# 验证配置完整性
print("\n" + "=" * 60)
print("  Validation")
print("=" * 60)

all_configured = all([
    settings.AUTH0_DOMAIN,
    settings.AUTH0_AUDIENCE,
    settings.AUTH0_ISSUER,
])

if all_configured:
    print("\n✅ All required Auth0 settings are configured!")
    print("\nNext steps:")
    print("  1. Verify AUTH0_AUDIENCE matches your Auth0 API Identifier")
    print("  2. Test JWT authentication with a valid token")
    print("  3. Check Auth0 Dashboard for API settings")
else:
    print("\n⚠️  Some Auth0 settings are missing!")
    print("Please check your .env file and ensure all values are set.")

print("\n" + "=" * 60)


