"""
解码 JWT Token 查看内容
"""
import jwt
import json

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

print("=" * 60)
print("JWT Token Decoder")
print("=" * 60)

# 解码不验证（仅查看内容）
try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("\nToken Payload:")
    print(json.dumps(decoded, indent=2))
    
    print("\n" + "=" * 60)
    print("Configuration Check")
    print("=" * 60)
    
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    django.setup()
    from django.conf import settings
    
    print(f"\nToken Claims:")
    print(f"  iss (issuer): {decoded.get('iss')}")
    print(f"  aud (audience): {decoded.get('aud')}")
    print(f"  sub (subject): {decoded.get('sub')}")
    
    print(f"\nDjango Settings:")
    print(f"  AUTH0_ISSUER: {settings.AUTH0_ISSUER}")
    print(f"  AUTH0_AUDIENCE: {settings.AUTH0_AUDIENCE}")
    
    print(f"\nComparison:")
    if decoded.get('iss') == settings.AUTH0_ISSUER:
        print(f"  [OK] Issuer matches")
    else:
        print(f"  [ERROR] Issuer mismatch!")
        print(f"     Token:    '{decoded.get('iss')}'")
        print(f"     Expected: '{settings.AUTH0_ISSUER}'")
    
    if decoded.get('aud') == settings.AUTH0_AUDIENCE:
        print(f"  [OK] Audience matches")
    else:
        print(f"  [ERROR] Audience mismatch!")
        print(f"     Token:    '{decoded.get('aud')}'")
        print(f"     Expected: '{settings.AUTH0_AUDIENCE}'")
    
except Exception as e:
    print(f"Error: {e}")

