"""
测试 Auth0 认证（完整流程）
"""
import requests
import json

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

print("=" * 60)
print("Auth0 Authentication Test")
print("=" * 60)

headers = {
    'X-Site-Code': 'NA',
    'Authorization': f'Bearer {token}'
}

# 测试受保护端点
print("\nTesting protected endpoint with Auth0 token...")
print(f"URL: http://localhost:8000/api/v1/test/protected/")
print(f"Headers: X-Site-Code=NA, Authorization=Bearer ...")

try:
    response = requests.get(
        'http://localhost:8000/api/v1/test/protected/',
        headers=headers,
        timeout=10
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n[SUCCESS] Auth0 Authentication Working!")
        print("\n" + "=" * 60)
        print("Authentication Result")
        print("=" * 60)
        print(f"Message: {result.get('message')}")
        print(f"User ID: {result.get('user_id')}")
        print(f"Auth0 Sub: {result.get('auth0_sub')}")
        print(f"Email: {result.get('email')}")
        print(f"Site Code: {result.get('site_code')}")
        print(f"Timestamp: {result.get('timestamp')}")
        print("\n" + "=" * 60)
        print("Full Response:")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n[FAILED] Status: {response.status_code}")
        try:
            error = response.json()
            print(f"Error Code: {error.get('code')}")
            print(f"Message: {error.get('message')}")
            if 'detail' in error:
                print(f"Detail: {error.get('detail')}")
        except:
            print(f"Response: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Cannot connect to server")
    print("Please make sure Django server is running on http://localhost:8000")
except Exception as e:
    print(f"\n[ERROR] {e}")


