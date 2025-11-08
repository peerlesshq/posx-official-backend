"""
Auth0 JWT Token 测试脚本
测试从 Auth0 获取的 token 是否能正常访问 POSX API
"""
import http.client
import json

# Auth0 Token (从 Auth0 Dashboard 获取)
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVZelNZWnZkU21fRi1ueUNCUjJHNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1wb3N4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJqb0ljVWdiMUZBcVNiY3p0TEVKdERwclA3SWZ2WkZvWUBjbGllbnRzIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2FwaS92MS8iLCJpYXQiOjE3NjI2MjczNzUsImV4cCI6MTc2MjcxMzc3NSwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiam9JY1VnYjFGQXFTYmN6dExFSnREcHJQN0lmdlpGb1kifQ.BPCNcS8XcXqisE3qnVt3Dw8oPZ_pdTd3VsUaKM3GgHUwXkC49IfRLvbQCbmd99vNtZM5kNvSNb7jop3vXVSVgmudhWKZyjADJIPdGVg0sYenF03iaIfQ63t-mgRVLzDkCqdJ3kzAZF3caAeIrX7_ZODDesD6AX3IcLZo1dSPVVHYI5df6M_4fWvPRvGmA-7j31Rk-1YcD_CD_BOZGeXVdwxTZ78RnhTB7nffdwc_YJUXsuInDROlQaM-Q0esV92OPBoMsCE45uWQzkGk_aNwAjRl4vM0o6C7Nm_ZpcwEkqSRDRNKsUOT9Orsv9vOpImLi7OC8ppq3XHpe7Fcn2oJXA"

# API 基础 URL
API_BASE = "localhost:8000"

def test_health_endpoint():
    """测试健康检查端点（不需要认证）"""
    print("\n" + "=" * 60)
    print("1. Testing Health Endpoint (No Auth Required)")
    print("=" * 60)
    
    conn = http.client.HTTPConnection(API_BASE)
    conn.request("GET", "/health/")
    res = conn.getresponse()
    data = res.read()
    
    print(f"Status Code: {res.status}")
    print(f"Response: {data.decode('utf-8')}")
    
    if res.status == 200:
        print("✅ Health endpoint works!")
    else:
        print(f"❌ Health endpoint failed: {res.status}")
    
    conn.close()
    return res.status == 200

def test_protected_endpoint_without_token():
    """测试受保护端点（不带 token）"""
    print("\n" + "=" * 60)
    print("2. Testing Protected Endpoint (Without Token)")
    print("=" * 60)
    
    conn = http.client.HTTPConnection(API_BASE)
    conn.request("GET", "/api/v1/tiers/")
    res = conn.getresponse()
    data = res.read()
    
    print(f"Status Code: {res.status}")
    print(f"Response: {data.decode('utf-8')}")
    
    if res.status == 401:
        print("✅ Correctly rejected request without token!")
    else:
        print(f"⚠️  Unexpected status: {res.status}")
    
    conn.close()
    return res.status == 401

def test_protected_endpoint_with_token():
    """测试受保护端点（带 token）"""
    print("\n" + "=" * 60)
    print("3. Testing Protected Endpoint (With Auth0 Token)")
    print("=" * 60)
    
    conn = http.client.HTTPConnection(API_BASE)
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        conn.request("GET", "/api/v1/tiers/", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        print(f"Status Code: {res.status}")
        
        try:
            response_json = json.loads(data.decode('utf-8'))
            print(f"Response: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"Response: {data.decode('utf-8')}")
        
        if res.status == 200:
            print("✅ Successfully authenticated with Auth0 token!")
            print("✅ JWT authentication is working!")
            return True
        elif res.status == 401:
            print("❌ Authentication failed!")
            print("Possible reasons:")
            print("  - Token expired")
            print("  - Token signature invalid")
            print("  - Audience mismatch")
            print("  - Issuer mismatch")
            return False
        else:
            print(f"⚠️  Unexpected status: {res.status}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

def test_ready_endpoint():
    """测试就绪检查端点"""
    print("\n" + "=" * 60)
    print("4. Testing Ready Endpoint")
    print("=" * 60)
    
    conn = http.client.HTTPConnection(API_BASE)
    conn.request("GET", "/ready/")
    res = conn.getresponse()
    data = res.read()
    
    print(f"Status Code: {res.status}")
    try:
        response_json = json.loads(data.decode('utf-8'))
        print(f"Response: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {data.decode('utf-8')}")
    
    conn.close()
    return res.status in [200, 503]

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Auth0 JWT Token Authentication Test")
    print("=" * 60)
    print(f"\nAPI Base: http://{API_BASE}")
    print(f"Token: {ACCESS_TOKEN[:50]}...")
    
    results = {
        'Health Endpoint': test_health_endpoint(),
        'Protected Endpoint (No Token)': test_protected_endpoint_without_token(),
        'Protected Endpoint (With Token)': test_protected_endpoint_with_token(),
        'Ready Endpoint': test_ready_endpoint(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if results['Protected Endpoint (With Token)']:
        print("\n🎉 Auth0 JWT Authentication is working correctly!")
    else:
        print("\n⚠️  Auth0 JWT Authentication needs attention.")
        print("Please check:")
        print("  1. Django server is running")
        print("  2. Token is not expired")
        print("  3. Auth0 configuration matches")

if __name__ == '__main__':
    main()


