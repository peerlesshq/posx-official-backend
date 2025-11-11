"""
Initial migration for errors app
"""
from django.db import migrations, models
import django.core.validators
import uuid


class Migration(migrations.Migration):
    """Initial migration"""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ErrorCode',
            fields=[
                ('error_code_id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False
                )),
                ('code', models.CharField(
                    help_text='错误码（格式：DOMAIN-XXXX）',
                    max_length=20,
                    unique=True,
                    validators=[
                        django.core.validators.RegexValidator(
                            message='Code must be in format DOMAIN-XXXX (e.g. CUSTODY-1015)',
                            regex='^[A-Z]+-\\d{4}$'
                        )
                    ]
                )),
                ('domain', models.CharField(
                    choices=[
                        ('AUTH', 'Authentication'),
                        ('WALLET', 'Wallet Connection'),
                        ('CUSTODY', 'Custody/Fireblocks'),
                        ('CHAIN', 'Chain/Assets'),
                        ('PAY', 'Payment'),
                        ('RISK', 'Risk/Compliance'),
                        ('KYC', 'KYC/KYB'),
                        ('RATE', 'Rate Limiting'),
                        ('SYS', 'System')
                    ],
                    db_index=True,
                    help_text='域',
                    max_length=20
                )),
                ('http_status', models.IntegerField(
                    help_text='HTTP 状态码（400/401/403/404/409/429/500/502/503）'
                )),
                ('severity', models.CharField(
                    choices=[
                        ('BLOCKING', 'Blocking'),
                        ('HIGH', 'High'),
                        ('MEDIUM', 'Medium'),
                        ('LOW', 'Low')
                    ],
                    db_index=True,
                    help_text='严重度',
                    max_length=20
                )),
                ('ui_type', models.CharField(
                    choices=[
                        ('DIALOG', 'Modal Dialog'),
                        ('BANNER', 'Page Banner'),
                        ('TOAST', 'Toast'),
                        ('INLINE', 'Inline')
                    ],
                    default='TOAST',
                    help_text='UI 展示方式',
                    max_length=20
                )),
                ('retryable', models.BooleanField(
                    default=False,
                    help_text='是否可重试'
                )),
                ('default_msg_key', models.CharField(
                    help_text='默认文案 Key（用于 i18n）',
                    max_length=100
                )),
                ('default_actions', models.JSONField(
                    default=list,
                    help_text='默认恢复动作，如 ["RETRY", "CONTACT_SUPPORT"]'
                )),
                ('owner_team', models.CharField(
                    blank=True,
                    help_text='负责团队',
                    max_length=100
                )),
                ('runbook_url', models.URLField(
                    blank=True,
                    help_text='运维手册 URL',
                    max_length=500
                )),
                ('is_active', models.BooleanField(
                    db_index=True,
                    default=True,
                    help_text='是否启用'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Error Code',
                'verbose_name_plural': 'Error Codes',
                'db_table': 'error_codes',
                'ordering': ['domain', 'code'],
            },
        ),
        migrations.CreateModel(
            name='ErrorMessage',
            fields=[
                ('message_id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False
                )),
                ('msg_key', models.CharField(
                    db_index=True,
                    help_text='文案 Key',
                    max_length=100
                )),
                ('language', models.CharField(
                    db_index=True,
                    default='en',
                    help_text='语言代码（en/zh/ja）',
                    max_length=10
                )),
                ('title', models.CharField(
                    help_text='标题',
                    max_length=255
                )),
                ('message', models.TextField(
                    help_text='消息内容'
                )),
                ('action_labels', models.JSONField(
                    default=dict,
                    help_text='动作按钮文案，如 {"RETRY": "重试", "CONTACT_SUPPORT": "联系客服"}'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Error Message',
                'verbose_name_plural': 'Error Messages',
                'db_table': 'error_messages',
            },
        ),
        migrations.AddIndex(
            model_name='errorcode',
            index=models.Index(
                fields=['domain', 'is_active'],
                name='error_codes_domain_c43bce_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='errorcode',
            index=models.Index(
                fields=['severity'],
                name='error_codes_severit_6abe1b_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='errorcode',
            index=models.Index(
                fields=['code'],
                name='error_codes_code_f8ed2d_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='errormessage',
            index=models.Index(
                fields=['msg_key', 'language'],
                name='error_messa_msg_key_e0b5a2_idx'
            ),
        ),
        migrations.AddConstraint(
            model_name='errormessage',
            constraint=models.UniqueConstraint(
                fields=['msg_key', 'language'],
                name='uq_error_message_key_lang'
            ),
        ),
    ]

