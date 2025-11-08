#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的 .env 文件验证脚本（不依赖Django）
"""
import os
from pathlib import Path

def check_env_file():
    """检查.env文件是否存在并读取配置"""
    print("\n" + "="*60)
    print("POSX .env 文件验证")
    print("="*60 + "\n")
    
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        print("❌ .env 文件不存在")
        return False
    
    print(f"✅ .env 文件存在: {env_path}\n")
    
    # 读取.env文件
    configs = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                configs[key.strip()] = value.strip()
    
    # 检查关键配置
    required = {
        'SECRET_KEY': 'Django密钥',
        'DEBUG': '调试模式',
        'DB_NAME': '数据库名',
        'DB_USER': '数据库用户',
        'DB_PASSWORD': '数据库密码',
        'REDIS_URL': 'Redis URL',
        'AUTH0_DOMAIN': 'Auth0域名',
        'SIWE_DOMAIN': 'SIWE域名',
        'STRIPE_SECRET_KEY': 'Stripe密钥',
        'STRIPE_WEBHOOK_SECRET': 'Stripe Webhook密钥',
    }
    
    print("检查关键配置项：\n")
    all_ok = True
    
    for key, desc in required.items():
        value = configs.get(key, '')
        if not value:
            print(f"❌ {desc} ({key}) 未配置")
            all_ok = False
        else:
            # 脱敏显示
            if 'SECRET' in key or 'PASSWORD' in key or 'KEY' in key:
                display = value[:15] + '...' if len(value) > 15 else '***'
            else:
                display = value
            print(f"✅ {desc}: {display}")
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ 所有关键配置项都已配置！")
        print("\n下一步：")
        print("  1. 安装Python依赖: pip install -r requirements/production.txt")
        print("  2. 运行数据库迁移: python manage.py migrate")
        print("  3. 启动开发服务器: python manage.py runserver")
    else:
        print("⚠️  部分配置项缺失，请检查.env文件")
    print("="*60 + "\n")
    
    return all_ok

if __name__ == '__main__':
    import sys
    sys.exit(0 if check_env_file() else 1)

