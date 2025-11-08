"""
Sites app初始迁移
包含Site模型（全局元数据，不受RLS限制）
"""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                ('site_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='站点唯一标识', primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, help_text='站点代码（NA/ASIA）', max_length=20, unique=True)),
                ('name', models.CharField(help_text='站点名称', max_length=100)),
                ('domain', models.CharField(help_text='站点域名', max_length=255, unique=True)),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='站点激活状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Site',
                'verbose_name_plural': 'Sites',
                'db_table': 'sites',
            },
        ),
        migrations.AddIndex(
            model_name='site',
            index=models.Index(fields=['code'], name='sites_code_a42e11_idx'),
        ),
        migrations.AddIndex(
            model_name='site',
            index=models.Index(fields=['is_active', 'created_at'], name='sites_is_acti_6d7f92_idx'),
        ),
    ]


