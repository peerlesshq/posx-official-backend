"""
Phase F: Agent 扩展（AgentProfile, WithdrawalRequest, CommissionStatement）
新增代理余额账户、提现申请、月度对账单功能
"""
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0001_initial'),
        ('users', '0001_initial'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentProfile',
            fields=[
                ('profile_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='资料唯一标识', primary_key=True, serialize=False)),
                ('agent_level', models.CharField(choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], db_index=True, default='bronze', help_text='代理等级', max_length=20)),
                ('balance_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='可提现余额（USD）', max_digits=18)),
                ('total_earned_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='累计收入（USD）', max_digits=18)),
                ('total_withdrawn_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='累计提现（USD）', max_digits=18)),
                ('kyc_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], db_index=True, default='pending', help_text='KYC 认证状态', max_length=20)),
                ('kyc_submitted_at', models.DateTimeField(blank=True, help_text='KYC 提交时间', null=True)),
                ('kyc_approved_at', models.DateTimeField(blank=True, help_text='KYC 批准时间', null=True)),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='账户激活状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(help_text='所属站点（RLS隔离）', on_delete=models.deletion.PROTECT, related_name='agent_profiles', to='sites.site')),
                ('user', models.OneToOneField(help_text='关联用户', on_delete=models.deletion.CASCADE, related_name='agent_profile', to='users.user')),
            ],
            options={
                'verbose_name': 'Agent Profile',
                'verbose_name_plural': 'Agent Profiles',
                'db_table': 'agent_profiles',
            },
        ),
        migrations.CreateModel(
            name='WithdrawalRequest',
            fields=[
                ('request_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='申请唯一标识', primary_key=True, serialize=False)),
                ('amount_usd', models.DecimalField(decimal_places=6, help_text='提现金额（USD）', max_digits=18, validators=[MinValueValidator(Decimal('0.01'))])),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], db_index=True, default='submitted', help_text='申请状态', max_length=20)),
                ('withdrawal_method', models.CharField(choices=[('bank_transfer', 'Bank Transfer'), ('paypal', 'PayPal'), ('crypto', 'Cryptocurrency')], help_text='提现方式', max_length=50)),
                ('account_info', models.JSONField(help_text='账户信息（加密存储）：{bank_name, account_number, ...}')),
                ('admin_note', models.TextField(blank=True, help_text='管理员备注')),
                ('approved_at', models.DateTimeField(blank=True, help_text='审核时间', null=True)),
                ('completed_at', models.DateTimeField(blank=True, help_text='完成时间', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent_profile', models.ForeignKey(help_text='代理资料', on_delete=models.deletion.PROTECT, related_name='withdrawal_requests', to='agents.agentprofile')),
                ('approved_by', models.ForeignKey(blank=True, help_text='审核人', null=True, on_delete=models.deletion.SET_NULL, related_name='approved_withdrawals', to='users.user')),
            ],
            options={
                'verbose_name': 'Withdrawal Request',
                'verbose_name_plural': 'Withdrawal Requests',
                'db_table': 'withdrawal_requests',
            },
        ),
        migrations.CreateModel(
            name='CommissionStatement',
            fields=[
                ('statement_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='对账单唯一标识', primary_key=True, serialize=False)),
                ('period_start', models.DateField(help_text='统计周期开始日期')),
                ('period_end', models.DateField(help_text='统计周期结束日期')),
                ('total_commissions_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='本期佣金总额', max_digits=18)),
                ('paid_commissions_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='已结算佣金', max_digits=18)),
                ('pending_commissions_usd', models.DecimalField(decimal_places=6, default=Decimal('0'), help_text='未结算佣金（hold + ready）', max_digits=18)),
                ('order_count', models.PositiveIntegerField(default=0, help_text='本期订单数')),
                ('customer_count', models.PositiveIntegerField(default=0, help_text='本期新增客户数')),
                ('pdf_url', models.CharField(blank=True, help_text='PDF 文件 URL', max_length=255)),
                ('generated_at', models.DateTimeField(auto_now_add=True, help_text='生成时间')),
                ('agent_profile', models.ForeignKey(help_text='代理资料', on_delete=models.deletion.PROTECT, related_name='statements', to='agents.agentprofile')),
            ],
            options={
                'verbose_name': 'Commission Statement',
                'verbose_name_plural': 'Commission Statements',
                'db_table': 'commission_statements',
            },
        ),
        migrations.AddConstraint(
            model_name='agentprofile',
            constraint=models.UniqueConstraint(fields=('site', 'user'), name='uq_agent_profile_site_user'),
        ),
        migrations.AddConstraint(
            model_name='agentprofile',
            constraint=models.CheckConstraint(check=models.Q(('balance_usd__gte', 0)), name='chk_agent_profile_balance_non_negative'),
        ),
        migrations.AddIndex(
            model_name='agentprofile',
            index=models.Index(fields=['site', 'agent_level'], name='agent_profiles_site_id_8d7f42_idx'),
        ),
        migrations.AddIndex(
            model_name='agentprofile',
            index=models.Index(fields=['site', 'balance_usd'], name='agent_profiles_site_id_9e6c31_idx'),
        ),
        migrations.AddIndex(
            model_name='agentprofile',
            index=models.Index(fields=['site', 'is_active'], name='agent_profiles_site_id_7f5b20_idx'),
        ),
        migrations.AddIndex(
            model_name='agentprofile',
            index=models.Index(fields=['kyc_status'], name='agent_profiles_kyc_sta_6d4e19_idx'),
        ),
        migrations.AddConstraint(
            model_name='withdrawalrequest',
            constraint=models.CheckConstraint(check=models.Q(('status__in', ['submitted', 'approved', 'rejected', 'completed', 'cancelled'])), name='chk_withdrawal_status'),
        ),
        migrations.AddIndex(
            model_name='withdrawalrequest',
            index=models.Index(fields=['agent_profile', 'status'], name='withdrawal_requests_agent_p_8c9f32_idx'),
        ),
        migrations.AddIndex(
            model_name='withdrawalrequest',
            index=models.Index(fields=['status', 'created_at'], name='withdrawal_requests_status_7b8e21_idx'),
        ),
        migrations.AddIndex(
            model_name='withdrawalrequest',
            index=models.Index(fields=['approved_by'], name='withdrawal_requests_approve_6d7c10_idx'),
        ),
        migrations.AddConstraint(
            model_name='commissionstatement',
            constraint=models.UniqueConstraint(fields=('agent_profile', 'period_start', 'period_end'), name='uq_statement_agent_period'),
        ),
        migrations.AddIndex(
            model_name='commissionstatement',
            index=models.Index(fields=['agent_profile', 'period_start'], name='commission_statements_agent_p_9d8f43_idx'),
        ),
        migrations.AddIndex(
            model_name='commissionstatement',
            index=models.Index(fields=['period_start', 'period_end'], name='commission_statements_period__7e6d32_idx'),
        ),
        migrations.AddIndex(
            model_name='commissionstatement',
            index=models.Index(fields=['generated_at'], name='commission_statements_generat_8f5c21_idx'),
        ),
    ]

