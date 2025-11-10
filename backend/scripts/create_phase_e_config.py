"""
Phase E 初始化脚本
创建资产配置和测试策略
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from decimal import Decimal
from apps.sites.models import Site, ChainAssetConfig
from apps.vesting.models import VestingPolicy


def create_asset_configs():
    """创建资产配置"""
    print("\n=== 创建资产配置 ===\n")
    
    sites = Site.objects.all()
    
    if not sites.exists():
        print("❌ 没有找到站点，请先创建站点")
        return
    
    created_count = 0
    
    for site in sites:
        # ETH - POSX (18 decimals)
        config, created = ChainAssetConfig.objects.get_or_create(
            site=site,
            chain='ETH',
            token_symbol='POSX',
            defaults={
                'token_decimals': 18,
                'fireblocks_asset_id': 'POSX_ETH',
                'fireblocks_vault_id': '0',
                'address_type': 'EVM',
                'is_active': True
            }
        )
        
        if created:
            print(f"[OK] 创建: {site.code} - ETH POSX (18 decimals)")
            created_count += 1
        else:
            print(f"[SKIP] 已存在: {site.code} - ETH POSX")
        
        # POLYGON - POSX (18 decimals)
        config, created = ChainAssetConfig.objects.get_or_create(
            site=site,
            chain='POLYGON',
            token_symbol='POSX',
            defaults={
                'token_decimals': 18,
                'fireblocks_asset_id': 'POSX_POLYGON',
                'fireblocks_vault_id': '0',
                'address_type': 'EVM',
                'is_active': True
            }
        )
        
        if created:
            print(f"[OK] 创建: {site.code} - POLYGON POSX (18 decimals)")
            created_count += 1
        else:
            print(f"[SKIP] 已存在: {site.code} - POLYGON POSX")
    
    print(f"\n[OK] 资产配置创建完成: {created_count} 个新配置\n")


def create_vesting_policies():
    """创建默认 Vesting 策略"""
    print("\n=== 创建 Vesting 策略 ===\n")
    
    sites = Site.objects.all()
    
    if not sites.exists():
        print("[ERROR] 没有找到站点")
        return
    
    created_count = 0
    
    for site in sites:
        # 策略 1: 10% TGE + 12个月线性
        policy, created = VestingPolicy.objects.get_or_create(
            site=site,
            name='10% TGE + 12 Months Linear',
            defaults={
                'description': '10% TGE立即释放，剩余90%分12个月线性释放',
                'tge_percent': Decimal('10.00'),
                'cliff_months': 0,
                'linear_periods': 12,
                'period_unit': 'month',
                'is_active': True
            }
        )
        
        if created:
            print(f"[OK] 创建: {site.code} - 10% TGE + 12 Months")
            created_count += 1
        else:
            print(f"[SKIP] 已存在: {site.code} - 10% TGE + 12 Months")
        
        # 策略 2: 20% TGE + 6个月线性
        policy, created = VestingPolicy.objects.get_or_create(
            site=site,
            name='20% TGE + 6 Months Linear',
            defaults={
                'description': '20% TGE立即释放，剩余80%分6个月线性释放',
                'tge_percent': Decimal('20.00'),
                'cliff_months': 0,
                'linear_periods': 6,
                'period_unit': 'month',
                'is_active': True
            }
        )
        
        if created:
            print(f"[OK] 创建: {site.code} - 20% TGE + 6 Months")
            created_count += 1
        else:
            print(f"[SKIP] 已存在: {site.code} - 20% TGE + 6 Months")
    
    print(f"\n[OK] Vesting 策略创建完成: {created_count} 个新策略\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Phase E 配置初始化")
    print("=" * 60)
    
    try:
        create_asset_configs()
        create_vesting_policies()
        
        print("\n" + "=" * 60)
        print("[OK] Phase E 配置初始化完成！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 启动 Django: python manage.py runserver")
        print("2. 启动 Celery Worker: celery -A config worker -l info")
        print("3. 启动 Celery Beat: celery -A config beat -l info")
        print("4. 访问 Admin: http://localhost:8000/admin/vesting/vestingrelease/")
        print("\n")
        
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()

