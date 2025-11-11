#!/usr/bin/env python
"""
Load Error Codes from JSON files

⭐ 用途：
- 从 seed/error_codes.json 加载错误码到数据库
- 支持幂等操作（可重复执行）
- 不会修改已存在的错误码

Usage:
    python scripts/load_error_codes.py
"""
import os
import sys
import json
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.errors.models import ErrorCode


def load_error_codes():
    """Load error codes from JSON file"""
    
    # Read error_codes.json
    json_path = os.path.join(os.path.dirname(__file__), '..', 'seed', 'error_codes.json')
    
    if not os.path.exists(json_path):
        print(f"❌ Error codes file not found: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        error_codes_data = json.load(f)
    
    print(f"📄 Found {len(error_codes_data)} error codes in JSON")
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for item in error_codes_data:
        code = item['code']
        
        # Check if error code already exists
        existing = ErrorCode.objects.filter(code=code).first()
        
        if existing:
            # Don't modify existing error codes
            print(f"⏭️  Skipped: {code} (already exists)")
            skipped_count += 1
            continue
        
        # Create new error code
        try:
            error_code = ErrorCode.objects.create(
                code=item['code'],
                domain=item['domain'],
                http_status=item['http_status'],
                severity=item['severity'],
                ui_type=item['ui_type'],
                retryable=item['retryable'],
                default_msg_key=item['default_msg_key'],
                default_actions=item.get('default_actions', []),
                owner_team=item.get('owner_team', ''),
                runbook_url=item.get('runbook_url', ''),
                is_active=True
            )
            print(f"✅ Created: {code} ({item['domain']} - {item['severity']})")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Failed to create {code}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total:   {len(error_codes_data)}")
    
    if created_count > 0:
        print(f"\n✅ Successfully loaded {created_count} error codes")
    else:
        print(f"\n⚠️  No new error codes to load")


if __name__ == '__main__':
    load_error_codes()

