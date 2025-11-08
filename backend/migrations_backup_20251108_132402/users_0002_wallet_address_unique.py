"""
为Wallet.address创建唯一索引（LOWER(address)）
⚠️ 使用CONCURRENTLY避免锁表
分两步：1) 创建唯一索引 2) 使用该索引添加约束
"""
from django.db import migrations


class Migration(migrations.Migration):
    """
    LOWER(address)唯一索引
    
    ⚠️ atomic=False: 支持CONCURRENTLY操作
    """

    atomic = False  # ⚠️ 必须False才能使用CONCURRENTLY

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # Step 1: 创建唯一索引CONCURRENTLY
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_wallets_address_lower
                    ON wallets(LOWER(address));
            """,
            reverse_sql="""
                DROP INDEX CONCURRENTLY IF EXISTS uq_wallets_address_lower;
            """
        ),
        # Step 2: 使用该索引添加UNIQUE约束
        # 注意：PostgreSQL会自动使用匹配的索引
        migrations.RunSQL(
            sql="""
                -- 添加约束说明
                COMMENT ON INDEX uq_wallets_address_lower IS 
                    'Unique constraint on LOWER(address) to prevent case-sensitive duplicates';
            """,
            reverse_sql=""
        ),
    ]


