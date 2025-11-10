"""
添加 Order.chain 字段（多链支持）
用于 Vesting 和 Retool 对接
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_remove_order_unique_site_idempotency_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='chain',
            field=models.CharField(
                choices=[
                    ('ETH', 'Ethereum'),
                    ('POLYGON', 'Polygon'),
                    ('BSC', 'BSC'),
                    ('TRON', 'TRON')
                ],
                db_index=True,
                default='ETH',
                help_text='订单所在链（多链支持）',
                max_length=20
            ),
        ),
    ]

