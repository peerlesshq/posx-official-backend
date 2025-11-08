#!/usr/bin/env python
"""
环境变量配置检查脚本

使用方法：
    python check_env.py
"""
import os
import sys
from pathlib import Path

# 颜色定义
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(text):
    """打印标题"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{GREEN}✅ {text}{NC}")


def print_error(text):
    """打印错误信息"""
    print(f"{RED}❌ {text}{NC}")


def print_warning(text):
    """打印警告信息"""
    print(f"{YELLOW}⚠️  {text}{NC}")


def check_env_file():
    """检查.env文件是否存在"""
    print_header("1. 检查 .env 文件")
    
    env_path = Path(__file__).parent.parent / '.env'
    
    if env_path.exists():
        print_success(f".env 文件存在: {env_path}")
        return True
    else:
        print_error(f".env 文件不存在: {env_path}")
        print(f"\n{YELLOW}请创建 .env 文件：{NC}")
        print(f"  cd {env_path.parent}")
        print(f"  copy .env.template .env")
        print(f"  # 或者")
        print(f"  touch .env")
        return False


def load_env():
    """加载环境变量"""
    try:
        import environ
        env = environ.Env()
        env_path = Path(__file__).parent.parent / '.env'
        environ.Env.read_env(str(env_path))
        return env
    except Exception as e:
        print_error(f"加载 .env 失败: {e}")
        return None


def check_p0_configs(env):
    """检查P0（必须）配置"""
    print_header("2. 检查 P0 配置（必须）")
    
    configs = {
        'SECRET_KEY': {
            'required': True,
            'check': lambda v: v and len(v) > 20 and 'change' not in v.lower()
        },
        'DEBUG': {
            'required': True,
            'check': lambda v: v in ['true', 'false', 'True', 'False']
        },
        'DB_NAME': {
            'required': True,
            'check': lambda v: bool(v)
        },
        'DB_USER': {
            'required': True,
            'check': lambda v: bool(v)
        },
        'DB_PASSWORD': {
            'required': True,
            'check': lambda v: bool(v)
        },
        'DB_HOST': {
            'required': True,
            'check': lambda v: bool(v)
        },
        'REDIS_URL': {
            'required': True,
            'check': lambda v: v and 'redis://' in v
        },
        'SIWE_DOMAIN': {
            'required': True,
            'check': lambda v: bool(v)
        },
        'SIWE_CHAIN_ID': {
            'required': True,
            'check': lambda v: v and str(v).isdigit()
        },
        'SIWE_URI': {
            'required': True,
            'check': lambda v: v and ('http://' in v or 'https://' in v)
        },
    }
    
    all_passed = True
    
    for key, config in configs.items():
        value = env(key, default='')
        
        if not value:
            print_error(f"{key} 未配置")
            all_passed = False
        elif not config['check'](value):
            print_warning(f"{key} 配置可能有问题: {value[:20]}...")
            all_passed = False
        else:
            # 脱敏显示
            if 'SECRET' in key or 'PASSWORD' in key or 'KEY' in key:
                display_value = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display_value = value
            
            print_success(f"{key} = {display_value}")
    
    return all_passed


def check_p1_configs(env):
    """检查P1（重要）配置"""
    print_header("3. 检查 P1 配置（重要）")
    
    # Auth0
    auth0_domain = env('AUTH0_DOMAIN', default='')
    auth0_audience = env('AUTH0_AUDIENCE', default='')
    auth0_issuer = env('AUTH0_ISSUER', default='')
    
    if auth0_domain and auth0_audience and auth0_issuer:
        print_success("Auth0 配置完整")
        print(f"  Domain: {auth0_domain}")
        print(f"  Audience: {auth0_audience[:30]}...")
    else:
        print_warning("Auth0 未配置（如不使用Auth0 JWT认证，可忽略）")
    
    # Stripe
    stripe_key = env('STRIPE_SECRET_KEY', default='')
    mock_stripe = env('MOCK_STRIPE', default='true')
    
    if mock_stripe.lower() == 'true':
        print_warning("MOCK_STRIPE=true，Stripe将使用Mock模式")
        print("  提示：开发阶段这是正常的")
    elif stripe_key:
        print_success(f"Stripe Secret Key: {stripe_key[:10]}...")
    else:
        print_error("Stripe Secret Key 未配置，且未启用Mock模式")
    
    # 环境标识
    env_name = env('ENV', default='dev')
    print_success(f"环境标识: {env_name}")


def check_database_connection(env):
    """检查数据库连接"""
    print_header("4. 检查数据库连接")
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            dbname=env('DB_NAME', default='posx_local'),
            user=env('DB_USER', default='posx_app'),
            password=env('DB_PASSWORD', default='posx'),
            host=env('DB_HOST', default='localhost'),
            port=env('DB_PORT', default='5432')
        )
        conn.close()
        
        print_success("数据库连接成功")
        return True
        
    except Exception as e:
        print_error(f"数据库连接失败: {e}")
        print(f"\n{YELLOW}请检查：{NC}")
        print("  1. PostgreSQL 服务是否运行")
        print("  2. 数据库是否已创建")
        print("  3. 用户名和密码是否正确")
        return False


def check_redis_connection(env):
    """检查Redis连接"""
    print_header("5. 检查 Redis 连接")
    
    try:
        import redis
        
        redis_url = env('REDIS_URL', default='redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        
        print_success("Redis 连接成功")
        return True
        
    except Exception as e:
        print_error(f"Redis 连接失败: {e}")
        print(f"\n{YELLOW}请检查：{NC}")
        print("  1. Redis 服务是否运行")
        print("  2. REDIS_URL 配置是否正确")
        return False


def check_required_packages():
    """检查必需的Python包"""
    print_header("6. 检查 Python 依赖")
    
    required = {
        'django': 'Django',
        'rest_framework': 'djangorestframework',
        'siwe': 'siwe',
        'eth_account': 'eth-account',
        'stripe': 'stripe',
    }
    
    all_installed = True
    
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
            print_success(f"{package_name} 已安装")
        except ImportError:
            print_error(f"{package_name} 未安装")
            all_installed = False
    
    if not all_installed:
        print(f"\n{YELLOW}请安装缺失的依赖：{NC}")
        print("  pip install -r requirements/production.txt")
    
    return all_installed


def print_summary(results):
    """打印总结"""
    print_header("配置检查总结")
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
    
    print("\n" + "="*60)
    
    if all_passed:
        print(f"{GREEN}🎉 所有检查通过！您可以开始使用POSX了。{NC}\n")
        print(f"{BLUE}下一步：{NC}")
        print("  1. python manage.py migrate")
        print("  2. python manage.py loaddata fixtures/seed_sites.json")
        print("  3. python manage.py runserver")
    else:
        print(f"{RED}⚠️ 部分检查未通过，请修复后重试。{NC}\n")
        print(f"{BLUE}参考文档：{NC}")
        print("  - ENVIRONMENT_SETUP_GUIDE.md")
    
    print("="*60 + "\n")
    
    return all_passed


def main():
    """主函数"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}POSX 环境变量配置检查工具{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    
    # 检查.env文件
    if not check_env_file():
        sys.exit(1)
    
    # 加载环境变量
    env = load_env()
    if env is None:
        sys.exit(1)
    
    # 执行检查
    results = {
        'P0配置完整': check_p0_configs(env),
        'Python依赖安装': check_required_packages(),
        '数据库连接': check_database_connection(env),
        'Redis连接': check_redis_connection(env),
    }
    
    # P1配置（不影响结果）
    check_p1_configs(env)
    
    # 打印总结
    all_passed = print_summary(results)
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()


