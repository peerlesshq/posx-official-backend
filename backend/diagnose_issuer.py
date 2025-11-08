"""
Auth0 Issuer 诊断脚本
检查 issuer 匹配问题
"""
import os
import django
import jwt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

print("=" * 60)
print("Auth0 Issuer Diagnostic")
print("=" * 60)

# 解码 token
unverified = jwt.decode(token, options={"verify_signature": False})
token_issuer = unverified.get('iss')
token_audience = unverified.get('aud')

print(f"\nToken Claims:")
print(f"  iss: '{token_issuer}'")
print(f"  aud: '{token_audience}'")

print(f"\nDjango Settings:")
print(f"  AUTH0_ISSUER: '{settings.AUTH0_ISSUER}'")
print(f"  AUTH0_AUDIENCE: '{settings.AUTH0_AUDIENCE}'")

print(f"\nComparison:")
print(f"  Issuer match: {token_issuer == settings.AUTH0_ISSUER}")
print(f"  Issuer repr: {repr(token_issuer)}")
print(f"  Expected repr: {repr(settings.AUTH0_ISSUER)}")
print(f"  Issuer length: {len(token_issuer)} vs {len(settings.AUTH0_ISSUER)}")

print(f"\n  Audience match: {token_audience == settings.AUTH0_AUDIENCE}")
print(f"  Audience repr: {repr(token_audience)}")
print(f"  Expected repr: {repr(settings.AUTH0_AUDIENCE)}")

# 测试 PyJWT 验证
print(f"\n" + "=" * 60)
print("Testing PyJWT Verification")
print("=" * 60)

import requests
jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()

header = jwt.get_unverified_header(token)
kid = header.get('kid')

signing_key = None
for key in jwks.get('keys', []):
    if key.get('kid') == kid:
        signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        break

if signing_key:
    print("\nAttempting verification with PyJWT...")
    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=settings.AUTH0_ISSUER,
            leeway=settings.AUTH0_JWT_LEEWAY,
        )
        print("[SUCCESS] Token verified successfully!")
    except jwt.InvalidIssuerError as e:
        print(f"[ERROR] InvalidIssuerError: {e}")
        print(f"  This suggests issuer comparison is failing")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")


