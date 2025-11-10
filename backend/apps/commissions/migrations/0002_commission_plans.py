"""
Phase F: 多层级佣金方案（CommissionPlan, CommissionPlanTier）
支持配置化的 2-10 级佣金体系
"""
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0001_initial'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommissionPlan',
            fields=[
                ('plan_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='方案唯一标识', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='方案名称（标准/高级/VIP）', max_length=100)),
                ('description', models.TextField(blank=True, help_text='方案描述')),
                ('max_levels', models.PositiveSmallIntegerField(default=2, help_text='最大层级数（1-10）', validators=[MinValueValidator(1), MaxValueValidator(10)])),
                ('is_default', models.BooleanField(db_index=True, default=False, help_text='是否为默认方案')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='方案激活状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(help_text='所属站点（RLS隔离）', on_delete=models.deletion.PROTECT, related_name='commission_plans', to='sites.site')),
            ],
            options={
                'verbose_name': 'Commission Plan',
                'verbose_name_plural': 'Commission Plans',
                'db_table': 'commission_plans',
            },
        ),
        migrations.CreateModel(
            name='CommissionPlanTier',
            fields=[
                ('tier_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='层级唯一标识', primary_key=True, serialize=False)),
                ('level', models.PositiveSmallIntegerField(help_text='层级编号（1-10）', validators=[MinValueValidator(1), MaxValueValidator(10)])),
                ('rate_percent', models.DecimalField(decimal_places=2, help_text='佣金比例（%）', max_digits=5, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])),
                ('hold_days', models.PositiveIntegerField(default=7, help_text='持有天数', validators=[MinValueValidator(0)])),
                ('min_order_amount', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='最小订单金额（USD，可选条件）', max_digits=18)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plan', models.ForeignKey(help_text='所属方案', on_delete=models.deletion.CASCADE, related_name='tiers', to='commissions.commissionplan')),
            ],
            options={
                'verbose_name': 'Commission Plan Tier',
                'verbose_name_plural': 'Commission Plan Tiers',
                'db_table': 'commission_plan_tiers',
                'ordering': ['plan', 'level'],
            },
        ),
        migrations.AddConstraint(
            model_name='commissionplan',
            constraint=models.UniqueConstraint(fields=('site', 'name'), name='uq_commission_plan_site_name'),
        ),
        migrations.AddIndex(
            model_name='commissionplan',
            index=models.Index(fields=['site', 'is_default'], name='commission_plans_site_id_7f8d42_idx'),
        ),
        migrations.AddIndex(
            model_name='commissionplan',
            index=models.Index(fields=['site', 'is_active'], name='commission_plans_site_id_8e7c31_idx'),
        ),
        migrations.AddConstraint(
            model_name='commissionplantier',
            constraint=models.UniqueConstraint(fields=('plan', 'level'), name='uq_commission_plan_tier_plan_level'),
        ),
        migrations.AddIndex(
            model_name='commissionplantier',
            index=models.Index(fields=['plan', 'level'], name='commission_plan_tiers_plan_id_9f6d52_idx'),
        ),
    ]

