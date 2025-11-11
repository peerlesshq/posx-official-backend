# Generated manually for Tier promotion feature

from decimal import Decimal
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tiers', '0001_initial'),
    ]

    operations = [
        # 添加促销相关字段
        migrations.AddField(
            model_name='tier',
            name='bonus_tokens_per_unit',
            field=models.DecimalField(
                max_digits=18,
                decimal_places=6,
                default=Decimal('0'),
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                help_text='额外赠送代币（每单位）'
            ),
        ),
        migrations.AddField(
            model_name='tier',
            name='promotional_price_usd',
            field=models.DecimalField(
                max_digits=18,
                decimal_places=6,
                null=True,
                blank=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.000001'))],
                help_text='促销价（可选，null=使用原价）'
            ),
        ),
        migrations.AddField(
            model_name='tier',
            name='promotion_valid_from',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='促销生效开始时间'
            ),
        ),
        migrations.AddField(
            model_name='tier',
            name='promotion_valid_until',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='促销生效结束时间'
            ),
        ),
    ]

