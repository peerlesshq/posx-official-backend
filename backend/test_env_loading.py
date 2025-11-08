"""
Test Auth0 Environment Variable Loading
"""
import os
from pathlib import Path
import environ

# 模拟 base.py 的路径计算
# base.py 位于: backend/config/settings/base.py
# BASE_DIR 应该是: backend/
# BASE_DIR.parent 应该是项目根目录
script_path = Path(__file__).resolve()
# 从 backend/test_env_loading.py 到 backend/
BASE_DIR = script_path.parent
# 项目根目录
project_root = BASE_DIR.parent
env_path = project_root / '.env'

print("=" * 60)
print("Environment Variable Loading Test")
print("=" * 60)
print(f"\nBASE_DIR: {BASE_DIR}")
print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    print(f"\n.env file content (first 10 lines):")
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:10]
        for line in lines:
            print(f"  {line.rstrip()}")

# 尝试加载
env = environ.Env()
try:
    env.read_env(str(env_path))
    print("\n" + "=" * 60)
    print("Loaded Environment Variables:")
    print("=" * 60)
    
    auth0_vars = [
        'AUTH0_DOMAIN',
        'AUTH0_AUDIENCE', 
        'AUTH0_ISSUER',
        'AUTH0_CLIENT_ID',
    ]
    
    for var in auth0_vars:
        value = env(var, default=None)
        if value:
            if 'SECRET' in var:
                display = '*' * len(value)
            else:
                display = value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: Not found")
            
except Exception as e:
    print(f"\n❌ Error loading .env: {e}")

print("\n" + "=" * 60)

