"""
Commission Admin 管理界面（Phase D + Phase F 集成）

⭐ Phase F 集成：
- 批量结算时自动更新 Agent 余额
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from apps.commissions.models import (
    Commission,
    CommissionConfig,
    CommissionPlan,
    CommissionPlanTier
)

logger = logging.getLogger(__name__)


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    """
    佣金管理
    
    ⭐ Phase F: 批量结算时更新 Agent 余额
    """
    
    list_display = [
        'commission_id_short',
        'order_id_short',
        'agent_email',
        'level',
        'amount_display',
        'rate_display',
        'status_colored',
        'hold_until',
        'paid_at',
        'created_at'
    ]
    list_filter = ['status', 'level', 'created_at', 'hold_until']
    search_fields = [
        'commission_id',
        'order__order_id',
        'agent__email'
    ]
    readonly_fields = [
        'commission_id', 'order', 'agent', 'level',
        'rate_percent', 'commission_amount_usd',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('commission_id', 'order', 'agent', 'level')
        }),
        ('金额信息', {
            'fields': ('rate_percent', 'commission_amount_usd')
        }),
        ('状态信息', {
            'fields': ('status', 'hold_until', 'paid_at')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['settle_commissions']
    
    def commission_id_short(self, obj):
        return str(obj.commission_id)[:8] + '...'
    commission_id_short.short_description = 'Commission ID'
    
    def order_id_short(self, obj):
        return str(obj.order.order_id)[:8] + '...'
    order_id_short.short_description = 'Order'
    
    def agent_email(self, obj):
        return obj.agent.email
    agent_email.short_description = 'Agent'
    
    def amount_display(self, obj):
        return f"${obj.commission_amount_usd:.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'commission_amount_usd'
    
    def rate_display(self, obj):
        return f"{obj.rate_percent}%"
    rate_display.short_description = 'Rate'
    
    def status_colored(self, obj):
        colors = {
            'hold': 'orange',
            'ready': 'blue',
            'paid': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def settle_commissions(self, request, queryset):
        """
        批量结算佣金（Phase D + Phase F 集成）
        
        逻辑：
        1. 过滤 status='ready' 的佣金
        2. 批量更新 status='paid'
        3. ⭐ Phase F: 更新 Agent 余额（悲观锁）
        
        条件：
        - 状态必须是 ready
        - 更新为 paid
        - 记录 paid_at
        """
        # 过滤：仅 ready 状态
        ready_commissions = queryset.filter(status='ready')
        count = ready_commissions.count()
        
        if count == 0:
            self.message_user(
                request,
                "没有可结算的佣金（状态必须是 ready）",
                level='warning'
            )
            return
        
        # 计算总金额
        total_amount = sum(
            c.commission_amount_usd for c in ready_commissions
        )
        
        # 逐条处理（需更新余额）⭐
        settled_count = 0
        failed_count = 0
        balance_update_errors = []
        
        for commission in ready_commissions.select_related('agent', 'order__site'):
            try:
                with transaction.atomic():
                    # 更新 Commission 状态
                    Commission.objects.filter(
                        commission_id=commission.commission_id,
                        status='ready'  # 再次检查状态
                    ).update(
                        status='paid',
                        paid_at=timezone.now(),
                        updated_at=timezone.now()
                    )
                    
                    # ⭐ Phase F: 更新 Agent 余额
                    from apps.agents.services.balance import update_balance_on_commission_paid
                    
                    # 重新获取（状态已更新）
                    commission.refresh_from_db()
                    update_balance_on_commission_paid(commission)
                    
                    settled_count += 1
                    
            except Exception as e:
                failed_count += 1
                balance_update_errors.append({
                    'commission_id': str(commission.commission_id),
                    'agent_email': commission.agent.email,
                    'error': str(e)
                })
                logger.error(
                    f"Failed to settle commission {commission.commission_id}: {e}",
                    exc_info=True
                )
        
        # 消息提示
        if failed_count == 0:
            self.message_user(
                request,
                f"成功结算 {settled_count} 条佣金，总金额 ${total_amount:.2f}。"
                f"Agent 余额已同步更新。",
                level='success'
            )
        else:
            self.message_user(
                request,
                f"结算完成：成功 {settled_count} 条，失败 {failed_count} 条，"
                f"总金额 ${total_amount:.2f}",
                level='warning'
            )
            
            # 显示错误详情（最多5条）
            for error in balance_update_errors[:5]:
                self.message_user(
                    request,
                    f"错误：{error['agent_email']} - {error['error']}",
                    level='error'
                )
        
        # 审计日志
        logger.info(
            f"Admin settled commissions",
            extra={
                'admin': request.user.email,
                'settled_count': settled_count,
                'failed_count': failed_count,
                'total_amount': str(total_amount)
            }
        )
    
    settle_commissions.short_description = "结算选中的佣金（ready→paid，更新余额）"


@admin.register(CommissionConfig)
class CommissionConfigAdmin(admin.ModelAdmin):
    """佣金配置管理（已废弃，建议使用 CommissionPlan）"""
    
    list_display = ['site', 'level', 'rate_percent', 'hold_days', 'is_active']
    list_filter = ['site', 'level', 'is_active']
    
    def get_queryset(self, request):
        """添加废弃警告"""
        return super().get_queryset(request)


@admin.register(CommissionPlan)
class CommissionPlanAdmin(admin.ModelAdmin):
    """佣金方案管理（Phase F）"""
    
    list_display = [
        'plan_id_short',
        'site',
        'name',
        'max_levels',
        'is_default_display',
        'is_active',
        'tier_count',
        'created_at'
    ]
    list_filter = ['site', 'is_default', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['plan_id', 'created_at', 'updated_at']
    
    def plan_id_short(self, obj):
        return str(obj.plan_id)[:8] + '...'
    plan_id_short.short_description = 'Plan ID'
    
    def is_default_display(self, obj):
        if obj.is_default:
            return format_html('<span style="color: green;">✓ 默认</span>')
        return '-'
    is_default_display.short_description = 'Default'
    
    def tier_count(self, obj):
        return obj.tiers.count()
    tier_count.short_description = 'Tiers'


@admin.register(CommissionPlanTier)
class CommissionPlanTierAdmin(admin.ModelAdmin):
    """佣金方案层级管理（Phase F）"""
    
    list_display = [
        'plan',
        'level',
        'rate_percent',
        'hold_days',
        'min_order_amount'
    ]
    list_filter = ['plan', 'level']
    readonly_fields = ['tier_id', 'created_at', 'updated_at']

