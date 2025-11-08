"""
直接测试 JWT 验证
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings
import jwt
import requests

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

print("=" * 60)
print("Direct JWT Verification Test")
print("=" * 60)

print(f"\nSettings:")
print(f"  AUTH0_DOMAIN: {settings.AUTH0_DOMAIN}")
print(f"  AUTH0_ISSUER: {settings.AUTH0_ISSUER}")
print(f"  AUTH0_AUDIENCE: {settings.AUTH0_AUDIENCE}")
print(f"  AUTH0_ALGORITHMS: {settings.AUTH0_ALGORITHMS}")

# 获取 JWKS
jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
print(f"\nFetching JWKS from: {jwks_url}")

try:
    response = requests.get(jwks_url, timeout=5)
    response.raise_for_status()
    jwks = response.json()
    print(f"  [OK] JWKS fetched successfully, {len(jwks.get('keys', []))} keys found")
except Exception as e:
    print(f"  [ERROR] Failed to fetch JWKS: {e}")
    exit(1)

# 获取 kid
try:
    header = jwt.get_unverified_header(token)
    kid = header.get('kid')
    print(f"\nToken kid: {kid}")
except Exception as e:
    print(f"  [ERROR] Failed to parse token header: {e}")
    exit(1)

# 找到匹配的公钥
signing_key = None
for key in jwks.get('keys', []):
    if key.get('kid') == kid:
        signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        print(f"  [OK] Found matching signing key")
        break

if not signing_key:
    print(f"  [ERROR] No matching key found for kid: {kid}")
    exit(1)

# 尝试验证 token
print(f"\nVerifying token...")
print(f"  issuer: {settings.AUTH0_ISSUER}")
print(f"  audience: {settings.AUTH0_AUDIENCE}")

try:
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=settings.AUTH0_ALGORITHMS,
        audience=settings.AUTH0_AUDIENCE,
        issuer=settings.AUTH0_ISSUER,
        leeway=settings.AUTH0_JWT_LEEWAY,
    )
    print(f"\n[SUCCESS] Token verified successfully!")
    print(f"\nPayload:")
    import json
    print(json.dumps(payload, indent=2))
    
except jwt.ExpiredSignatureError:
    print(f"  [ERROR] Token has expired")
except jwt.InvalidAudienceError as e:
    print(f"  [ERROR] Invalid audience: {e}")
except jwt.InvalidIssuerError as e:
    print(f"  [ERROR] Invalid issuer: {e}")
    print(f"  Token issuer: {jwt.decode(token, options={'verify_signature': False}).get('iss')}")
    print(f"  Expected: {settings.AUTH0_ISSUER}")
except Exception as e:
    print(f"  [ERROR] Verification failed: {e}")


