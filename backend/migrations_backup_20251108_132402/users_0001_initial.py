"""
Users app初始迁移
包含User和Wallet模型
⚠️ Wallet.address唯一索引使用CONCURRENTLY创建（避免锁表）
"""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='用户唯一标识', primary_key=True, serialize=False)),
                ('auth0_sub', models.CharField(blank=True, db_index=True, help_text='Auth0 Subject ID（Email/Passkey登录）', max_length=255, null=True, unique=True)),
                ('email', models.EmailField(blank=True, db_index=True, help_text='邮箱地址', max_length=254, null=True, unique=True)),
                ('referral_code', models.CharField(db_index=True, help_text='推荐码（格式：NA-ABC123）', max_length=20, unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='账户激活状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('referrer', models.ForeignKey(blank=True, help_text='推荐人', null=True, on_delete=models.deletion.SET_NULL, related_name='referrals', to='users.user')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('wallet_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='钱包唯一标识', primary_key=True, serialize=False)),
                ('address', models.CharField(help_text='钱包地址（统一存储lowercase）', max_length=42)),
                ('is_primary', models.BooleanField(default=False, help_text='是否为主钱包')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(help_text='钱包所有者', on_delete=models.deletion.CASCADE, related_name='wallets', to='users.user')),
            ],
            options={
                'verbose_name': 'Wallet',
                'verbose_name_plural': 'Wallets',
                'db_table': 'wallets',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['referral_code'], name='users_referra_64d8d6_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_78ac31_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['auth0_sub'], name='users_auth0_s_2c6c73_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active', 'created_at'], name='users_is_acti_6e3a51_idx'),
        ),
        migrations.AddIndex(
            model_name='wallet',
            index=models.Index(fields=['user', 'is_primary'], name='wallets_user_id_7f9543_idx'),
        ),
        migrations.AddIndex(
            model_name='wallet',
            index=models.Index(fields=['created_at'], name='wallets_created_e7c244_idx'),
        ),
    ]


