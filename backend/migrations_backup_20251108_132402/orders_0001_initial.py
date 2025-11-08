"""
Orders app初始迁移
包含Order和OrderItem模型（受RLS保护）
依赖: users, sites, tiers
"""
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('sites', '0001_initial'),
        ('tiers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='订单唯一标识', primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], db_index=True, default='pending', help_text='订单状态', max_length=20)),
                ('stripe_payment_intent_id', models.CharField(blank=True, db_index=True, help_text='Stripe PaymentIntent ID', max_length=255, null=True, unique=True)),
                ('idempotency_key', models.CharField(blank=True, help_text='幂等键', max_length=255, null=True, unique=True)),
                ('list_price_usd', models.DecimalField(decimal_places=6, help_text='原价总额', max_digits=18, validators=[MinValueValidator(Decimal('0'))])),
                ('discount_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='折扣金额', max_digits=18, validators=[MinValueValidator(Decimal('0'))])),
                ('final_price_usd', models.DecimalField(decimal_places=6, help_text='实付金额', max_digits=18, validators=[MinValueValidator(Decimal('0'))])),
                ('wallet_address', models.CharField(help_text='收币钱包地址（快照，lowercase）', max_length=42)),
                ('disputed', models.BooleanField(db_index=True, default=False, help_text='是否有争议（Stripe dispute）')),
                ('expires_at', models.DateTimeField(blank=True, help_text='过期时间（创建后15分钟）', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('buyer', models.ForeignKey(help_text='购买者', on_delete=models.deletion.PROTECT, related_name='orders', to='users.user')),
                ('referrer', models.ForeignKey(blank=True, help_text='推荐人', null=True, on_delete=models.deletion.SET_NULL, related_name='referred_orders', to='users.user')),
                ('site', models.ForeignKey(help_text='所属站点', on_delete=models.deletion.PROTECT, related_name='orders', to='sites.site')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'db_table': 'orders',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('item_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='明细唯一标识', primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(help_text='购买数量', validators=[MinValueValidator(1)])),
                ('unit_price_usd', models.DecimalField(decimal_places=6, help_text='单价快照', max_digits=18, validators=[MinValueValidator(Decimal('0'))])),
                ('token_amount', models.DecimalField(decimal_places=6, help_text='代币数量快照', max_digits=18, validators=[MinValueValidator(Decimal('0'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(help_text='所属订单', on_delete=models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('tier', models.ForeignKey(help_text='档位（快照）', on_delete=models.deletion.PROTECT, to='tiers.tier')),
            ],
            options={
                'verbose_name': 'Order Item',
                'verbose_name_plural': 'Order Items',
                'db_table': 'order_items',
            },
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(check=models.Q(('status__in', ['pending', 'paid', 'failed', 'cancelled'])), name='chk_order_status'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['buyer', 'created_at'], name='orders_buyer_i_8e4f21_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['site', 'created_at'], name='orders_site_id_3c9d74_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['referrer'], name='orders_referre_7b2c94_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', 'created_at'], name='orders_status_9f3a62_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['disputed'], name='orders_dispute_5d8c73_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['order'], name='order_items_order_i_6c2a84_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['tier'], name='order_items_tier_id_3f8b95_idx'),
        ),
    ]


