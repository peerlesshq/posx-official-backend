"""
Auth0 JWT Token 测试脚本（使用 requests）
更简单易用的测试方式
"""
import requests
import json
import sys

# Auth0 Token
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

API_BASE = "http://localhost:8000"

def test_endpoint(url, use_auth=False, description=""):
    """测试 API 端点"""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")
    print(f"URL: {url}")
    
    headers = {
        'X-Site-Code': 'NA'  # 添加站点代码
    }
    if use_auth:
        headers['Authorization'] = f'Bearer {ACCESS_TOKEN}'
        print(f"Using Auth0 Token: {ACCESS_TOKEN[:50]}...")
    print(f"Headers: X-Site-Code=NA")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            json_data = response.json()
            print(f"Response:\n{json.dumps(json_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"Response: {response.text}")
        
        return response.status_code
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Server is not running!")
        print("Please start the Django server:")
        print("  cd backend")
        print("  python manage.py runserver 0.0.0.0:8000")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def main():
    print("\n" + "=" * 60)
    print("Auth0 JWT Token Authentication Test")
    print("=" * 60)
    
    # 测试健康检查（不需要认证）
    health_status = test_endpoint(
        f"{API_BASE}/health/",
        use_auth=False,
        description="1. Testing Health Endpoint (No Auth Required)"
    )
    
    if health_status is None:
        print("\n⚠️  Server is not running. Please start it first.")
        sys.exit(1)
    
    # 测试受保护端点（不带 token）
    no_auth_status = test_endpoint(
        f"{API_BASE}/api/v1/tiers/",
        use_auth=False,
        description="2. Testing Protected Endpoint (Without Token)"
    )
    
    # 测试受保护端点（带 token）
    auth_status = test_endpoint(
        f"{API_BASE}/api/v1/tiers/",
        use_auth=True,
        description="3. Testing Protected Endpoint (With Auth0 Token)"
    )
    
    # 总结
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if health_status == 200:
        print("✅ Health endpoint: PASS")
    else:
        print(f"❌ Health endpoint: FAIL ({health_status})")
    
    if no_auth_status == 401:
        print("✅ Protected endpoint (no token): PASS (correctly rejected)")
    else:
        print(f"⚠️  Protected endpoint (no token): {no_auth_status}")
    
    if auth_status == 200:
        print("✅ Protected endpoint (with token): PASS")
        print("\n🎉 Auth0 JWT Authentication is working correctly!")
    elif auth_status == 401:
        print("❌ Protected endpoint (with token): FAIL (authentication failed)")
        print("\nPossible issues:")
        print("  - Token expired (check 'exp' claim)")
        print("  - Token signature invalid")
        print("  - Audience mismatch")
        print("  - Issuer mismatch")
    else:
        print(f"⚠️  Protected endpoint (with token): {auth_status}")

if __name__ == '__main__':
    main()

