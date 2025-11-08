"""
查询数据库表结构
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    
    print("=" * 60)
    print("Users Table Structure")
    print("=" * 60)
    print(f"{'Column':<30} {'Type':<20} {'Max Length':<10}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        col_name, data_type, max_len = row
        max_len_str = str(max_len) if max_len else '-'
        print(f"{col_name:<30} {data_type:<20} {max_len_str:<10}")


