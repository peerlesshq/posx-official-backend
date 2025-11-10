"""
添加 WebhookEvent 模型（Webhook 监控与重放）
"""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0002_remove_idempotencykey_idempotency_key_f43c7b_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('event_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='事件唯一标识', primary_key=True, serialize=False)),
                ('source', models.CharField(db_index=True, help_text='来源系统（fireblocks/stripe）', max_length=50)),
                ('event_type', models.CharField(db_index=True, help_text='事件类型（TRANSACTION_STATUS_UPDATED等）', max_length=100)),
                ('tx_id', models.CharField(db_index=True, help_text='交易ID或类似标识', max_length=200)),
                ('payload', models.JSONField(help_text='原始 payload')),
                ('processing_status', models.CharField(choices=[('pending', 'Pending'), ('processed', 'Processed'), ('failed', 'Failed'), ('duplicate', 'Duplicate')], db_index=True, default='pending', help_text='处理状态', max_length=20)),
                ('error_message', models.TextField(blank=True, help_text='错误信息（失败时）', null=True)),
                ('latency_ms', models.IntegerField(blank=True, help_text='处理延迟（毫秒）', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='事件接收时间')),
                ('processed_at', models.DateTimeField(blank=True, help_text='处理完成时间', null=True)),
            ],
            options={
                'verbose_name': 'Webhook Event',
                'verbose_name_plural': 'Webhook Events',
                'db_table': 'webhook_events',
            },
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['source', 'processing_status'], name='webhook_events_source_8f7d42_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['tx_id'], name='webhook_events_tx_id_6c3e91_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['created_at'], name='webhook_events_created_5b2d80_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['source', 'event_type'], name='webhook_events_source_9d8f43_idx'),
        ),
    ]

