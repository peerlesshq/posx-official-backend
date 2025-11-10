# Generated manually for POSX Notification System

from django.db import migrations, models
import django.core.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # No dependencies for initial migration
    ]

    operations = [
        # 1. Create notification_templates table
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('template_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='模板唯一标识', primary_key=True, serialize=False)),
                ('site_id', models.UUIDField(blank=True, db_index=True, help_text='站点ID（NULL=全局模板，有值=站点覆盖模板）', null=True)),
                ('parent_template_id', models.UUIDField(blank=True, help_text='父模板ID（用于模板继承）', null=True)),
                ('name', models.CharField(help_text='模板名称（如 order.payment.success）', max_length=100)),
                ('category', models.CharField(db_index=True, help_text='分类（finance/order/security/system/agent）', max_length=50)),
                ('subcategory', models.CharField(help_text='子分类（payment_success/commission_ready）', max_length=50)),
                ('language', models.CharField(default='en', help_text='语言代码（en/zh/ja）', max_length=10)),
                ('title_template', models.TextField(help_text='标题模板（支持 Django Template 语法）')),
                ('body_template', models.TextField(help_text='正文模板（支持 Django Template 语法）')),
                ('channels', models.JSONField(default=list, help_text='支持的渠道列表，如 ["in_app", "email"]')),
                ('channel_configs', models.JSONField(default=dict, help_text='渠道特定配置（邮件主题/Slack Blocks）')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='激活状态')),
                ('created_by', models.UUIDField(blank=True, help_text='创建者（管理员用户ID）', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Notification Template',
                'verbose_name_plural': 'Notification Templates',
                'db_table': 'notification_templates',
            },
        ),
        
        # 2. Create notifications table
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('notification_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='通知唯一标识', primary_key=True, serialize=False)),
                ('site_id', models.UUIDField(db_index=True, help_text='站点ID（RLS 隔离）')),
                ('recipient_type', models.CharField(choices=[('user', 'User'), ('agent', 'Agent'), ('admin', 'Admin'), ('site_broadcast', 'Site Broadcast')], db_index=True, help_text='接收者类型', max_length=20)),
                ('recipient_id', models.UUIDField(blank=True, db_index=True, help_text='用户ID（site_broadcast时为NULL）', null=True)),
                ('category', models.CharField(db_index=True, help_text='分类', max_length=50)),
                ('subcategory', models.CharField(help_text='子分类', max_length=50)),
                ('severity', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('high', 'High'), ('critical', 'Critical')], db_index=True, help_text='严重度', max_length=20)),
                ('source_type', models.CharField(blank=True, help_text='来源类型（order/commission/withdrawal/admin_action）', max_length=50, null=True)),
                ('source_id', models.UUIDField(blank=True, db_index=True, help_text='来源对象ID（订单ID/佣金ID等）', null=True)),
                ('title', models.CharField(help_text='标题（已渲染）', max_length=255)),
                ('body', models.TextField(help_text='正文（已渲染）')),
                ('payload', models.JSONField(default=dict, help_text='原始数据（金额使用字符串）')),
                ('action_url', models.CharField(blank=True, help_text='跳转链接（App Deep Link）', max_length=500, null=True)),
                ('read_at', models.DateTimeField(blank=True, db_index=True, help_text='已读时间', null=True)),
                ('visible_at', models.DateTimeField(db_index=True, help_text='可见时间（支持定时发布）')),
                ('expires_at', models.DateTimeField(blank=True, help_text='过期时间', null=True)),
                ('created_by', models.UUIDField(blank=True, help_text='创建者（系统/管理员）', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications',
                'ordering': ['-visible_at', '-created_at'],
            },
        ),
        
        # 3. Create notification_channel_tasks table
        migrations.CreateModel(
            name='NotificationChannelTask',
            fields=[
                ('task_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='任务唯一标识', primary_key=True, serialize=False)),
                ('notification', models.ForeignKey(help_text='关联通知', on_delete=models.deletion.CASCADE, related_name='channel_tasks', to='notifications.notification')),
                ('channel', models.CharField(choices=[('in_app', 'In-App'), ('email', 'Email'), ('slack', 'Slack'), ('webhook', 'Webhook')], db_index=True, help_text='渠道', max_length=20)),
                ('target', models.CharField(help_text='目标地址（邮箱/Slack Channel/Webhook URL）', max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], db_index=True, default='pending', help_text='状态', max_length=20)),
                ('payload', models.JSONField(default=dict, help_text='渠道特定 payload')),
                ('sent_at', models.DateTimeField(blank=True, help_text='发送成功时间', null=True)),
                ('retry_count', models.IntegerField(default=0, help_text='重试次数', validators=[django.core.validators.MinValueValidator(0)])),
                ('last_error', models.TextField(blank=True, help_text='最后错误信息', null=True)),
                ('next_retry_at', models.DateTimeField(blank=True, db_index=True, help_text='下次重试时间', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Notification Channel Task',
                'verbose_name_plural': 'Notification Channel Tasks',
                'db_table': 'notification_channel_tasks',
            },
        ),
        
        # 4. Create notification_preferences table
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('preference_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='偏好设置ID', primary_key=True, serialize=False)),
                ('site_id', models.UUIDField(db_index=True, help_text='站点ID')),
                ('user_id', models.UUIDField(db_index=True, help_text='用户ID')),
                ('channel', models.CharField(help_text='渠道', max_length=20)),
                ('category', models.CharField(help_text='通知分类', max_length=50)),
                ('is_enabled', models.BooleanField(default=True, help_text='是否启用')),
                ('quiet_hours_start', models.TimeField(blank=True, help_text='免打扰开始时间', null=True)),
                ('quiet_hours_end', models.TimeField(blank=True, help_text='免打扰结束时间', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Notification Preference',
                'verbose_name_plural': 'Notification Preferences',
                'db_table': 'notification_preferences',
            },
        ),
        
        # 5. Create notification_read_receipts table
        migrations.CreateModel(
            name='NotificationReadReceipt',
            fields=[
                ('receipt_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='回执ID', primary_key=True, serialize=False)),
                ('notification', models.ForeignKey(help_text='关联通知（recipient_type="site_broadcast"）', on_delete=models.deletion.CASCADE, related_name='read_receipts', to='notifications.notification')),
                ('user_id', models.UUIDField(db_index=True, help_text='用户ID')),
                ('read_at', models.DateTimeField(auto_now_add=True, help_text='阅读时间')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Notification Read Receipt',
                'verbose_name_plural': 'Notification Read Receipts',
                'db_table': 'notification_read_receipts',
            },
        ),
        
        # 6. Add constraints and indexes
        migrations.AddConstraint(
            model_name='notificationtemplate',
            constraint=models.UniqueConstraint(fields=('site_id', 'name'), name='uq_notification_template_site_name'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['site_id', 'is_active'], name='notificatio_site_id_64cad4_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['category', 'subcategory'], name='notificatio_categor_ac58fe_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['name', 'language'], name='notificatio_name_e9d3f2_idx'),
        ),
        
        migrations.AddConstraint(
            model_name='notification',
            constraint=models.CheckConstraint(check=models.Q(('recipient_type__in', ['user', 'agent', 'admin', 'site_broadcast'])), name='chk_notifications_recipient_type'),
        ),
        migrations.AddConstraint(
            model_name='notification',
            constraint=models.CheckConstraint(check=models.Q(('severity__in', ['info', 'warning', 'high', 'critical'])), name='chk_notifications_severity'),
        ),
        migrations.AddConstraint(
            model_name='notification',
            constraint=models.CheckConstraint(
                check=models.Q(models.Q(('recipient_type', 'site_broadcast'), ('recipient_id__isnull', True)) | ~models.Q(('recipient_type', 'site_broadcast'), ('recipient_id__isnull', False))),
                name='chk_notifications_broadcast_recipient'
            ),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['site_id', 'recipient_id', 'read_at'], name='notificatio_site_id_7a3c91_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['site_id', 'visible_at'], name='notificatio_site_id_b7d24e_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['source_type', 'source_id'], name='notificatio_source__6aa74a_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['severity', 'created_at'], name='notificatio_severit_f1c45b_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient_type', 'created_at'], name='notificatio_recipie_e9c723_idx'),
        ),
        
        migrations.AddConstraint(
            model_name='notificationchanneltask',
            constraint=models.CheckConstraint(check=models.Q(('channel__in', ['in_app', 'email', 'slack', 'webhook'])), name='chk_channel_tasks_channel'),
        ),
        migrations.AddConstraint(
            model_name='notificationchanneltask',
            constraint=models.CheckConstraint(check=models.Q(('status__in', ['pending', 'sent', 'failed'])), name='chk_channel_tasks_status'),
        ),
        migrations.AddIndex(
            model_name='notificationchanneltask',
            index=models.Index(fields=['notification'], name='notificatio_notific_5f7218_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationchanneltask',
            index=models.Index(fields=['status', 'next_retry_at'], name='notificatio_status_c8de4f_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationchanneltask',
            index=models.Index(fields=['channel', 'status'], name='notificatio_channel_3cd94e_idx'),
        ),
        
        migrations.AddConstraint(
            model_name='notificationpreference',
            constraint=models.UniqueConstraint(fields=('site_id', 'user_id', 'channel', 'category'), name='uq_notification_preference'),
        ),
        migrations.AddIndex(
            model_name='notificationpreference',
            index=models.Index(fields=['site_id', 'user_id'], name='notificatio_site_id_3a9e74_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationpreference',
            index=models.Index(fields=['user_id', 'channel'], name='notificatio_user_id_7dcb19_idx'),
        ),
        
        migrations.AddConstraint(
            model_name='notificationreadreceipt',
            constraint=models.UniqueConstraint(fields=('notification', 'user_id'), name='uq_notification_read_receipt'),
        ),
        migrations.AddIndex(
            model_name='notificationreadreceipt',
            index=models.Index(fields=['notification', 'user_id'], name='notificatio_notific_c1f872_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationreadreceipt',
            index=models.Index(fields=['user_id', 'read_at'], name='notificatio_user_id_1e9ab3_idx'),
        ),
    ]

