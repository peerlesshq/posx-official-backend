"""
Agent Admin 管理界面（Phase F）
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import transaction
import logging

from .models import AgentProfile, WithdrawalRequest, CommissionStatement, AgentTree, AgentStats
from .services.balance import refund_balance_for_withdrawal, complete_withdrawal

logger = logging.getLogger(__name__)


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    """Agent 资料管理"""
    
    list_display = [
        'user_email',
        'site_code',
        'agent_level_colored',
        'balance_display',
        'total_earned_display',
        'total_withdrawn_display',
        'kyc_status_colored',
        'is_active',
        'created_at'
    ]
    list_filter = ['agent_level', 'kyc_status', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__user_id']
    readonly_fields = [
        'profile_id', 'balance_usd', 'total_earned_usd',
        'total_withdrawn_usd', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('profile_id', 'user', 'site', 'agent_level', 'is_active')
        }),
        ('余额信息', {
            'fields': ('balance_usd', 'total_earned_usd', 'total_withdrawn_usd')
        }),
        ('KYC 信息', {
            'fields': ('kyc_status', 'kyc_submitted_at', 'kyc_approved_at')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def site_code(self, obj):
        return obj.site.code
    site_code.short_description = 'Site'
    
    def agent_level_colored(self, obj):
        colors = {
            'bronze': '#cd7f32',
            'silver': '#c0c0c0',
            'gold': '#ffd700',
            'platinum': '#e5e4e2'
        }
        color = colors.get(obj.agent_level, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_agent_level_display()
        )
    agent_level_colored.short_description = 'Level'
    
    def balance_display(self, obj):
        return f"${obj.balance_usd:.2f}"
    balance_display.short_description = 'Balance'
    balance_display.admin_order_field = 'balance_usd'
    
    def total_earned_display(self, obj):
        return f"${obj.total_earned_usd:.2f}"
    total_earned_display.short_description = 'Total Earned'
    
    def total_withdrawn_display(self, obj):
        return f"${obj.total_withdrawn_usd:.2f}"
    total_withdrawn_display.short_description = 'Total Withdrawn'
    
    def kyc_status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.kyc_status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_kyc_status_display()
        )
    kyc_status_colored.short_description = 'KYC Status'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    """提现申请管理"""
    
    list_display = [
        'request_id_short',
        'agent_email',
        'amount_display',
        'withdrawal_method',
        'status_colored',
        'approved_by',
        'created_at'
    ]
    list_filter = ['status', 'withdrawal_method', 'created_at']
    search_fields = ['request_id', 'agent_profile__user__email']
    readonly_fields = [
        'request_id', 'agent_profile', 'amount_usd',
        'withdrawal_method', 'account_info', 'created_at', 'updated_at'
    ]
    
    actions = ['approve_withdrawals', 'reject_withdrawals', 'complete_withdrawals']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('request_id', 'agent_profile', 'amount_usd', 'withdrawal_method')
        }),
        ('账户信息', {
            'fields': ('account_info',),
            'classes': ('collapse',)
        }),
        ('审核信息', {
            'fields': ('status', 'admin_note', 'approved_by', 'approved_at', 'completed_at')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def request_id_short(self, obj):
        return str(obj.request_id)[:8] + '...'
    request_id_short.short_description = 'Request ID'
    
    def agent_email(self, obj):
        return obj.agent_profile.user.email
    agent_email.short_description = 'Agent'
    
    def amount_display(self, obj):
        return f"${obj.amount_usd:.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount_usd'
    
    def status_colored(self, obj):
        colors = {
            'submitted': 'orange',
            'approved': 'blue',
            'rejected': 'red',
            'completed': 'green',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def approve_withdrawals(self, request, queryset):
        """批量审核通过"""
        # 过滤：仅 submitted 状态
        submitted = queryset.filter(status='submitted')
        count = submitted.count()
        
        if count == 0:
            self.message_user(request, "没有可审核的申请（状态必须是 submitted）", level='warning')
            return
        
        # 批量更新
        submitted.update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        self.message_user(request, f"已批准 {count} 条提现申请", level='success')
        
        logger.info(
            f"Admin approved {count} withdrawal requests",
            extra={'admin': request.user.email, 'count': count}
        )
    
    approve_withdrawals.short_description = "批准选中的申请（submitted→approved）"
    
    def reject_withdrawals(self, request, queryset):
        """批量拒绝（返还余额）"""
        submitted = queryset.filter(status='submitted')
        count = submitted.count()
        
        if count == 0:
            self.message_user(request, "没有可拒绝的申请", level='warning')
            return
        
        # 逐条处理（需返还余额）
        rejected_count = 0
        for withdrawal in submitted:
            try:
                with transaction.atomic():
                    # 返还余额
                    refund_balance_for_withdrawal(
                        withdrawal.agent_profile,
                        withdrawal.amount_usd,
                        reason='withdrawal_rejected'
                    )
                    
                    # 更新状态
                    withdrawal.status = 'rejected'
                    withdrawal.approved_by = request.user
                    withdrawal.approved_at = timezone.now()
                    withdrawal.save()
                    
                    rejected_count += 1
            except Exception as e:
                logger.error(f"Failed to reject withdrawal {withdrawal.request_id}: {e}")
        
        self.message_user(
            request,
            f"已拒绝 {rejected_count} 条申请并返还余额",
            level='success'
        )
    
    reject_withdrawals.short_description = "拒绝选中的申请（submitted→rejected，返还余额）"
    
    def complete_withdrawals(self, request, queryset):
        """标记完成（线下转账后）"""
        approved = queryset.filter(status='approved')
        count = approved.count()
        
        if count == 0:
            self.message_user(request, "没有可完成的申请（状态必须是 approved）", level='warning')
            return
        
        # 逐条处理（记录 total_withdrawn）
        completed_count = 0
        for withdrawal in approved:
            try:
                with transaction.atomic():
                    # 更新 total_withdrawn
                    complete_withdrawal(
                        withdrawal.agent_profile,
                        withdrawal.amount_usd
                    )
                    
                    # 更新状态
                    withdrawal.status = 'completed'
                    withdrawal.completed_at = timezone.now()
                    withdrawal.save()
                    
                    completed_count += 1
            except Exception as e:
                logger.error(f"Failed to complete withdrawal {withdrawal.request_id}: {e}")
        
        self.message_user(
            request,
            f"已标记 {completed_count} 条申请为完成",
            level='success'
        )
    
    complete_withdrawals.short_description = "标记完成（approved→completed）"


@admin.register(CommissionStatement)
class CommissionStatementAdmin(admin.ModelAdmin):
    """对账单管理"""
    
    list_display = [
        'statement_id_short',
        'agent_email',
        'period_display',
        'total_display',
        'paid_display',
        'pending_display',
        'order_count',
        'customer_count',
        'generated_at'
    ]
    list_filter = ['period_start', 'generated_at']
    search_fields = ['statement_id', 'agent_profile__user__email']
    readonly_fields = (
        'statement_id', 'agent_profile', 'period_start', 'period_end',
        'balance_start_of_period', 'balance_end_of_period',
        'total_commissions_usd', 'paid_commissions_usd', 'pending_commissions_usd',
        'order_count', 'customer_count', 'generated_at'
    )
    
    def statement_id_short(self, obj):
        return str(obj.statement_id)[:8] + '...'
    statement_id_short.short_description = 'Statement ID'
    
    def agent_email(self, obj):
        return obj.agent_profile.user.email
    agent_email.short_description = 'Agent'
    
    def period_display(self, obj):
        return f"{obj.period_start} ~ {obj.period_end}"
    period_display.short_description = 'Period'
    
    def total_display(self, obj):
        return f"${obj.total_commissions_usd:.2f}"
    total_display.short_description = 'Total'
    
    def paid_display(self, obj):
        return f"${obj.paid_commissions_usd:.2f}"
    paid_display.short_description = 'Paid'
    
    def pending_display(self, obj):
        return f"${obj.pending_commissions_usd:.2f}"
    pending_display.short_description = 'Pending'


@admin.register(AgentTree)
class AgentTreeAdmin(admin.ModelAdmin):
    """代理树管理"""
    
    list_display = ['agent', 'parent', 'depth', 'path_short', 'active', 'created_at']
    list_filter = ['depth', 'active', 'created_at']
    search_fields = ['agent', 'parent', 'path']
    readonly_fields = ['tree_id', 'created_at', 'updated_at']
    
    def path_short(self, obj):
        if len(obj.path) > 50:
            return obj.path[:50] + '...'
        return obj.path
    path_short.short_description = 'Path'


@admin.register(AgentStats)
class AgentStatsAdmin(admin.ModelAdmin):
    """代理统计管理"""
    
    list_display = [
        'agent',
        'total_customers',
        'direct_customers',
        'total_sales_display',
        'total_commissions_display',
        'last_order_at',
        'updated_at'
    ]
    list_filter = ['last_order_at', 'updated_at']
    search_fields = ['agent']
    readonly_fields = (
        'stat_id', 'agent', 'total_customers', 'direct_customers',
        'total_sales', 'total_commissions', 'last_order_at', 'updated_at'
    )
    
    def total_sales_display(self, obj):
        return f"${obj.total_sales:.2f}"
    total_sales_display.short_description = 'Total Sales'
    total_sales_display.admin_order_field = 'total_sales'
    
    def total_commissions_display(self, obj):
        return f"${obj.total_commissions:.2f}"
    total_commissions_display.short_description = 'Total Commissions'
    total_commissions_display.admin_order_field = 'total_commissions'

