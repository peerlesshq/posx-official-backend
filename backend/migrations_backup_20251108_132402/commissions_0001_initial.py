"""
Commissions app初始迁移
包含Commission和CommissionConfig模型（受RLS保护）
依赖: users, sites, orders
"""
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('sites', '0001_initial'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommissionConfig',
            fields=[
                ('config_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='配置唯一标识', primary_key=True, serialize=False)),
                ('level', models.IntegerField(help_text='佣金等级', validators=[MinValueValidator(1), MaxValueValidator(10)])),
                ('rate_percent', models.DecimalField(decimal_places=2, help_text='佣金比例（%）', max_digits=5, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])),
                ('hold_days', models.IntegerField(default=7, help_text='持有天数', validators=[MinValueValidator(0)])),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='配置激活状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(help_text='所属站点', on_delete=models.deletion.PROTECT, related_name='commission_configs', to='sites.site')),
            ],
            options={
                'verbose_name': 'Commission Config',
                'verbose_name_plural': 'Commission Configs',
                'db_table': 'commission_configs',
            },
        ),
        migrations.CreateModel(
            name='Commission',
            fields=[
                ('commission_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='佣金唯一标识', primary_key=True, serialize=False)),
                ('level', models.IntegerField(help_text='佣金等级（1=直推, 2=间推）', validators=[MinValueValidator(1), MaxValueValidator(10)])),
                ('rate_percent', models.DecimalField(decimal_places=2, help_text='佣金比例（%）', max_digits=5, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])),
                ('commission_amount_usd', models.DecimalField(decimal_places=6, help_text='佣金金额（USD）', max_digits=18, validators=[MinValueValidator(Decimal('0'))])),
                ('status', models.CharField(choices=[('hold', 'Hold'), ('ready', 'Ready'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], db_index=True, default='hold', help_text='佣金状态', max_length=20)),
                ('hold_until', models.DateTimeField(blank=True, help_text='持有截止时间（创建后7天）', null=True)),
                ('paid_at', models.DateTimeField(blank=True, help_text='结算时间', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(help_text='代理人（获得佣金者）', on_delete=models.deletion.PROTECT, related_name='earned_commissions', to='users.user')),
                ('order', models.ForeignKey(help_text='关联订单', on_delete=models.deletion.CASCADE, related_name='commissions', to='orders.order')),
            ],
            options={
                'verbose_name': 'Commission',
                'verbose_name_plural': 'Commissions',
                'db_table': 'commissions',
            },
        ),
        migrations.AddConstraint(
            model_name='commissionconfig',
            constraint=models.UniqueConstraint(fields=('site', 'level'), name='uq_commission_config_site_level'),
        ),
        migrations.AddIndex(
            model_name='commissionconfig',
            index=models.Index(fields=['site', 'is_active'], name='commission_configs_site_id_7d9f42_idx'),
        ),
        migrations.AddIndex(
            model_name='commissionconfig',
            index=models.Index(fields=['level'], name='commission_configs_level_5e8c31_idx'),
        ),
        migrations.AddConstraint(
            model_name='commission',
            constraint=models.CheckConstraint(check=models.Q(('status__in', ['hold', 'ready', 'paid', 'cancelled'])), name='chk_commission_status'),
        ),
        migrations.AddConstraint(
            model_name='commission',
            constraint=models.UniqueConstraint(fields=('order', 'agent', 'level'), name='uq_commission_order_agent_level'),
        ),
        migrations.AddIndex(
            model_name='commission',
            index=models.Index(fields=['order'], name='commissions_order_i_9c2f84_idx'),
        ),
        migrations.AddIndex(
            model_name='commission',
            index=models.Index(fields=['agent', 'status'], name='commissions_agent_i_6b3e71_idx'),
        ),
        migrations.AddIndex(
            model_name='commission',
            index=models.Index(fields=['status', 'hold_until'], name='commissions_status_2a7d59_idx'),
        ),
        migrations.AddIndex(
            model_name='commission',
            index=models.Index(fields=['created_at'], name='commissions_created_4f8b68_idx'),
        ),
    ]


