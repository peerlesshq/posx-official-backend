"""
Webhooks app初始迁移
包含IdempotencyKey模型（全局表，不受RLS限制）
用于Webhook事件去重（Stripe + Fireblocks）
"""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IdempotencyKey',
            fields=[
                ('key_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='记录唯一标识', primary_key=True, serialize=False)),
                ('key', models.CharField(db_index=True, help_text='幂等键（webhook事件ID）', max_length=255, unique=True)),
                ('source', models.CharField(choices=[('stripe', 'Stripe'), ('fireblocks', 'Fireblocks')], db_index=True, help_text='来源系统', max_length=50)),
                ('processed_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='处理时间')),
                ('payload', models.JSONField(blank=True, help_text='原始payload（用于排查）', null=True)),
            ],
            options={
                'verbose_name': 'Idempotency Key',
                'verbose_name_plural': 'Idempotency Keys',
                'db_table': 'idempotency_keys',
            },
        ),
        migrations.AddIndex(
            model_name='idempotencykey',
            index=models.Index(fields=['key', 'source'], name='idempotency_keys_key_8f7d42_idx'),
        ),
        migrations.AddIndex(
            model_name='idempotencykey',
            index=models.Index(fields=['source', 'processed_at'], name='idempotency_keys_source_6c3e91_idx'),
        ),
        migrations.AddIndex(
            model_name='idempotencykey',
            index=models.Index(fields=['processed_at'], name='idempotency_keys_process_5b2d80_idx'),
        ),
    ]


