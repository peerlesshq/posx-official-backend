#!/usr/bin/env python
"""
POSX Framework - 环境验证脚本
快速验证所有组件是否正常工作
"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_django_config():
    """测试 Django 配置"""
    print_header("1. Django 配置")
    try:
        print(f"✅ Django 版本: {django.get_version()}")
        print(f"✅ DEBUG 模式: {settings.DEBUG}")
        print(f"✅ 数据库: {list(settings.DATABASES.keys())}")
        print(f"✅ 已安装应用数: {len(settings.INSTALLED_APPS)}")
        return True
    except Exception as e:
        print(f"❌ Django 配置错误: {e}")
        return False

def test_database():
    """测试数据库连接"""
    print_header("2. 数据库连接")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL 版本: {version.split(',')[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            count = cursor.fetchone()[0]
            print(f"✅ 已应用迁移数: {count}")
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            print(f"✅ 数据表数量: {table_count}")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_redis():
    """测试 Redis 连接"""
    print_header("3. Redis 连接")
    try:
        test_key = 'posx_verify_test'
        test_value = 'ok'
        cache.set(test_key, test_value, 10)
        result = cache.get(test_key)
        
        if result == test_value:
            print(f"✅ Redis 连接正常")
            print(f"✅ 缓存读写测试通过")
            cache.delete(test_key)
            return True
        else:
            print(f"❌ Redis 缓存验证失败")
            return False
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False

def test_migrations():
    """测试迁移状态"""
    print_header("4. 迁移状态")
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print(f"⚠️  有 {len(plan)} 个迁移待应用:")
            for migration, _ in plan[:5]:
                print(f"   - {migration}")
            if len(plan) > 5:
                print(f"   ... 还有 {len(plan) - 5} 个")
            return False
        else:
            print(f"✅ 所有迁移已应用")
            return True
    except Exception as e:
        print(f"❌ 迁移检查失败: {e}")
        return False

def test_models():
    """测试模型导入"""
    print_header("5. 模型加载")
    try:
        from apps.sites.models import Site
        from apps.users.models import User
        from apps.tiers.models import Tier
        from apps.orders.models import Order
        from apps.commissions.models import Commission
        from apps.allocations.models import Allocation
        
        models = [
            ('Site', Site),
            ('User', User),
            ('Tier', Tier),
            ('Order', Order),
            ('Commission', Commission),
            ('Allocation', Allocation),
        ]
        
        for name, model in models:
            count = model.objects.count()
            print(f"✅ {name}: {count} 条记录")
        
        return True
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return False

def test_urls():
    """测试 URL 配置"""
    print_header("6. URL 路由")
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # 测试关键端点
        key_urls = [
            ('health/', '健康检查'),
            ('ready/', '就绪检查'),
            ('admin/', '管理后台'),
            ('api/v1/', 'API 根路径'),
        ]
        
        for url, desc in key_urls:
            try:
                resolver.resolve(f'/{url}')
                print(f"✅ {desc}: /{url}")
            except:
                print(f"⚠️  {desc}: /{url} (未配置)")
        
        return True
    except Exception as e:
        print(f"❌ URL 配置检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n")
    print("POSX Framework - Environment Verification")
    print(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'Django 配置': test_django_config(),
        '数据库连接': test_database(),
        'Redis 连接': test_redis(),
        '迁移状态': test_migrations(),
        '模型加载': test_models(),
        'URL 路由': test_urls(),
    }
    
    # 输出总结
    print_header("验证总结")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n[SUCCESS] All checks passed! Environment setup complete.")
        print("[TIP] Run 'python manage.py runserver' to start development server")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} check(s) failed. Please review errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

