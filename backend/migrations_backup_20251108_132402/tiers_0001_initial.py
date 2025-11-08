"""
Tiers app初始迁移
包含Tier模型（受RLS保护）
依赖: sites
"""
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tier',
            fields=[
                ('tier_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='档位唯一标识', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='档位名称', max_length=100)),
                ('description', models.TextField(blank=True, help_text='档位描述')),
                ('list_price_usd', models.DecimalField(decimal_places=6, help_text='单价（USD）', max_digits=18, validators=[MinValueValidator(Decimal('0.000001'))])),
                ('tokens_per_unit', models.DecimalField(decimal_places=6, help_text='单位代币数量', max_digits=18, validators=[MinValueValidator(Decimal('0.000001'))])),
                ('total_units', models.IntegerField(help_text='总库存', validators=[MinValueValidator(1)])),
                ('sold_units', models.IntegerField(default=0, help_text='已售数量', validators=[MinValueValidator(0)])),
                ('available_units', models.IntegerField(help_text='可用库存（计算字段）', validators=[MinValueValidator(0)])),
                ('display_order', models.IntegerField(default=0, help_text='展示顺序')),
                ('version', models.IntegerField(default=0, help_text='乐观锁版本号')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='档位激活状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(help_text='所属站点', on_delete=models.deletion.PROTECT, related_name='tiers', to='sites.site')),
            ],
            options={
                'verbose_name': 'Tier',
                'verbose_name_plural': 'Tiers',
                'db_table': 'tiers',
            },
        ),
        migrations.AddIndex(
            model_name='tier',
            index=models.Index(fields=['site', 'display_order'], name='tiers_site_id_4b8c91_idx'),
        ),
        migrations.AddIndex(
            model_name='tier',
            index=models.Index(fields=['site', 'is_active'], name='tiers_site_id_12e3a7_idx'),
        ),
        migrations.AddIndex(
            model_name='tier',
            index=models.Index(fields=['is_active', 'created_at'], name='tiers_is_acti_5f7b28_idx'),
        ),
    ]


