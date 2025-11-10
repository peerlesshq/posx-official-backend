"""
Phase F 补充: 对账单余额字段
新增期初/期末余额、本期提现字段
"""
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0002_agent_extensions'),
    ]

    operations = [
        migrations.AddField(
            model_name='commissionstatement',
            name='balance_start_of_period',
            field=models.DecimalField(
                decimal_places=6,
                default=Decimal('0'),
                help_text='期初余额（USD）',
                max_digits=18
            ),
        ),
        migrations.AddField(
            model_name='commissionstatement',
            name='balance_end_of_period',
            field=models.DecimalField(
                decimal_places=6,
                default=Decimal('0'),
                help_text='期末余额（USD）',
                max_digits=18
            ),
        ),
        migrations.AddField(
            model_name='commissionstatement',
            name='withdrawals_in_period',
            field=models.DecimalField(
                decimal_places=6,
                default=Decimal('0'),
                help_text='本期提现金额（USD）',
                max_digits=18
            ),
        ),
    ]

