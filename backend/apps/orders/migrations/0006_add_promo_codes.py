# Generated manually for Promo Code feature

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_chain'),
        ('sites', '0002_chainassetconfig'),
        ('tiers', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        # 创建 PromoCode 模型
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('promo_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='促销码唯一标识'
                )),
                ('code', models.CharField(
                    max_length=50,
                    unique=True,
                    db_index=True,
                    help_text='促销码（唯一，不区分大小写）'
                )),
                ('name', models.CharField(
                    max_length=100,
                    help_text='促销码名称'
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='促销码描述'
                )),
                ('discount_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('percentage', 'Percentage Discount'),
                        ('fixed_amount', 'Fixed Amount Discount'),
                        ('bonus_tokens', 'Bonus Tokens Only'),
                        ('combo', 'Combo (Discount + Tokens)'),
                    ],
                    help_text='折扣类型'
                )),
                ('discount_value', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    default=Decimal('0'),
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    help_text='折扣值（百分比或金额，取决于类型）'
                )),
                ('bonus_tokens_value', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    default=Decimal('0'),
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    help_text='额外代币奖励'
                )),
                ('max_uses', models.IntegerField(
                    null=True,
                    blank=True,
                    validators=[django.core.validators.MinValueValidator(1)],
                    help_text='最大使用次数（null=无限制）'
                )),
                ('uses_per_user', models.IntegerField(
                    default=1,
                    validators=[django.core.validators.MinValueValidator(1)],
                    help_text='每用户最大使用次数'
                )),
                ('current_uses', models.IntegerField(
                    default=0,
                    validators=[django.core.validators.MinValueValidator(0)],
                    help_text='当前使用次数'
                )),
                ('valid_from', models.DateTimeField(
                    help_text='生效开始时间'
                )),
                ('valid_until', models.DateTimeField(
                    help_text='生效结束时间'
                )),
                ('min_order_amount', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    default=Decimal('0'),
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    help_text='最低订单金额要求（USD）'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    db_index=True,
                    help_text='是否激活'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='promo_codes',
                    to='sites.site',
                    help_text='所属站点'
                )),
                ('applicable_tiers', models.ManyToManyField(
                    blank=True,
                    related_name='promo_codes',
                    to='tiers.tier',
                    help_text='适用的档位（空=适用所有档位）'
                )),
            ],
            options={
                'db_table': 'promo_codes',
                'verbose_name': 'Promo Code',
                'verbose_name_plural': 'Promo Codes',
            },
        ),
        
        # 添加约束
        migrations.AddConstraint(
            model_name='promocode',
            constraint=models.CheckConstraint(
                check=models.Q(discount_type__in=['percentage', 'fixed_amount', 'bonus_tokens', 'combo']),
                name='chk_promo_code_discount_type'
            ),
        ),
        migrations.AddConstraint(
            model_name='promocode',
            constraint=models.CheckConstraint(
                check=models.Q(valid_from__lt=models.F('valid_until')),
                name='chk_promo_code_valid_dates'
            ),
        ),
        
        # 添加索引
        migrations.AddIndex(
            model_name='promocode',
            index=models.Index(fields=['site', 'is_active'], name='promo_codes_site_active_idx'),
        ),
        migrations.AddIndex(
            model_name='promocode',
            index=models.Index(fields=['code'], name='promo_codes_code_idx'),
        ),
        migrations.AddIndex(
            model_name='promocode',
            index=models.Index(fields=['valid_from', 'valid_until'], name='promo_codes_valid_period_idx'),
        ),
        migrations.AddIndex(
            model_name='promocode',
            index=models.Index(fields=['created_at'], name='promo_codes_created_at_idx'),
        ),
        
        # 创建 PromoCodeUsage 模型
        migrations.CreateModel(
            name='PromoCodeUsage',
            fields=[
                ('usage_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='使用记录唯一标识'
                )),
                ('discount_applied', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    help_text='实际应用的折扣金额（USD）'
                )),
                ('bonus_tokens_applied', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    help_text='实际赠送的额外代币'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('promo_code', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='usages',
                    to='orders.promocode',
                    help_text='使用的促销码'
                )),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='promo_usage',
                    to='orders.order',
                    help_text='关联的订单（一对一）'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='promo_usages',
                    to='users.user',
                    help_text='使用者'
                )),
            ],
            options={
                'db_table': 'promo_code_usages',
                'verbose_name': 'Promo Code Usage',
                'verbose_name_plural': 'Promo Code Usages',
            },
        ),
        
        # 添加约束
        migrations.AddConstraint(
            model_name='promocodeusage',
            constraint=models.UniqueConstraint(
                fields=['promo_code', 'order'],
                name='uq_promo_code_usage_promo_order'
            ),
        ),
        
        # 添加索引
        migrations.AddIndex(
            model_name='promocodeusage',
            index=models.Index(fields=['promo_code'], name='promo_usage_promo_code_idx'),
        ),
        migrations.AddIndex(
            model_name='promocodeusage',
            index=models.Index(fields=['order'], name='promo_usage_order_idx'),
        ),
        migrations.AddIndex(
            model_name='promocodeusage',
            index=models.Index(fields=['user', 'promo_code'], name='promo_usage_user_promo_idx'),
        ),
        migrations.AddIndex(
            model_name='promocodeusage',
            index=models.Index(fields=['created_at'], name='promo_usage_created_at_idx'),
        ),
    ]

