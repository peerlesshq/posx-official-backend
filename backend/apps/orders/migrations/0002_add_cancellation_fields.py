"""
添加订单取消相关字段

⭐ 新增字段：
- cancelled_reason: 取消原因
- cancelled_at: 取消时间
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        # 添加cancelled_reason字段
        migrations.AddField(
            model_name='order',
            name='cancelled_reason',
            field=models.CharField(
                max_length=50,
                null=True,
                blank=True,
                help_text='取消原因（TIMEOUT/USER_CANCELLED）'
            ),
        ),
        
        # 添加cancelled_at字段
        migrations.AddField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='取消时间'
            ),
        ),
        
        # 添加索引
        migrations.AddIndex(
            model_name='order',
            index=models.Index(
                fields=['status', 'expires_at'],
                name='ord_status_exp_idx'
            ),
        ),
    ]


