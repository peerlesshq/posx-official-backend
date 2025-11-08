"""
添加幂等性约束

⭐ 核心改进：
- idempotency_key 唯一约束改为 (site_id, idempotency_key)
- 避免跨站点幂等键冲突
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_add_cancellation_fields'),
    ]

    operations = [
        # 移除原有的unique约束（如果存在）
        migrations.RunSQL(
            sql="""
                -- 移除 idempotency_key 的单列唯一约束（如果存在）
                ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_idempotency_key_key;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        
        # 添加复合唯一约束
        migrations.AddConstraint(
            model_name='order',
            constraint=models.UniqueConstraint(
                fields=['site', 'idempotency_key'],
                name='unique_site_idempotency_key',
                # 仅当idempotency_key不为空时生效
                condition=models.Q(idempotency_key__isnull=False)
            ),
        ),
        
        # 添加索引（提高查询性能）
        migrations.AddIndex(
            model_name='order',
            index=models.Index(
                fields=['site', 'idempotency_key'],
                name='ord_site_idem_idx'
            ),
        ),
    ]


