"""
创建测试站点数据
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.sites.models import Site

print("=" * 60)
print("Creating Test Sites")
print("=" * 60)

# 创建 NA 站点
na_site, created = Site.objects.get_or_create(
    code='NA',
    defaults={
        'name': 'North America',
        'domain': 'localhost:3000',
        'is_active': True,
    }
)
print(f"{'Created' if created else 'Found'} NA site: {na_site.site_id}")

# 创建 ASIA 站点
asia_site, created = Site.objects.get_or_create(
    code='ASIA',
    defaults={
        'name': 'Asia Pacific',
        'domain': 'asia.localhost:3000',
        'is_active': True,
    }
)
print(f"{'Created' if created else 'Found'} ASIA site: {asia_site.site_id}")

print("\n" + "=" * 60)
print("Sites Summary")
print("=" * 60)

sites = Site.objects.all()
for site in sites:
    print(f"  - {site.code}: {site.name} ({site.site_id})")

print(f"\nTotal sites: {sites.count()}")
print("\n✅ Test sites created successfully!")


