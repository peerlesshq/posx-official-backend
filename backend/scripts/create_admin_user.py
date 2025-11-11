#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建 Admin 超级用户脚本

使用方法：
    python scripts/create_admin_user.py
    python scripts/create_admin_user.py --username admin --password yourpassword --email admin@example.com
"""
import os
import sys
import django
from pathlib import Path

# 添加项目根目录到 Python 路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def create_superuser(username='admin', password='ashleymylove', email='admin@example.com'):
    """
    创建或更新超级用户
    
    Args:
        username: 用户名
        password: 密码
        email: 邮箱地址
    """
    try:
        # 检查用户是否已存在
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            # 新用户，设置密码
            user.set_password(password)
            user.save()
            print(f"✅ 成功创建超级用户:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        else:
            # 用户已存在，更新密码和权限
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            print(f"✅ 用户已存在，已更新密码和权限:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建超级用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='创建 Django 超级用户')
    parser.add_argument('--username', default='admin', help='用户名 (默认: admin)')
    parser.add_argument('--password', default='ashleymylove', help='密码 (默认: ashleymylove)')
    parser.add_argument('--email', default='admin@example.com', help='邮箱 (默认: admin@example.com)')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("创建 Admin 超级用户")
    print("=" * 50)
    
    success = create_superuser(
        username=args.username,
        password=args.password,
        email=args.email
    )
    
    if success:
        print("\n" + "=" * 50)
        print("✅ 完成！现在可以使用以下凭据登录 Admin:")
        print(f"   URL: http://localhost:8000/admin/")
        print(f"   Username: {args.username}")
        print(f"   Password: {args.password}")
        print("=" * 50)
        return 0
    else:
        print("\n❌ 创建失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())

