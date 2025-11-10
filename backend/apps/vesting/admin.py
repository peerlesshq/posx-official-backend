"""
Vesting Django Admin管理界面

⭐ Phase E 特性:
- 显示 FIREBLOCKS_MODE 徽标
- 批量发放 Action（最多100条）
- 4态着色显示
- 默认过滤 unlocked 状态
"""
from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.contrib import messages
from apps.vesting.models import VestingPolicy, VestingSchedule, VestingRelease
from apps.vesting.services.batch_release_service import batch_release_vesting


@admin.register(VestingPolicy)
class VestingPolicyAdmin(admin.ModelAdmin):
    """释放策略管理"""
    list_display = [
        'name',
        'site',
        'tge_percent',
        'cliff_months',
        'linear_periods',
        'period_unit',
        'is_active'
    ]
    list_filter = ['site', 'is_active', 'period_unit']
    search_fields = ['name', 'description']
    readonly_fields = ['policy_id', 'created_at']


@admin.register(VestingSchedule)
class VestingScheduleAdmin(admin.ModelAdmin):
    """释放计划管理"""
    list_display = [
        'schedule_id',
        'order',
        'user',
        'total_tokens',
        'tge_tokens',
        'locked_tokens',
        'unlock_start_date'
    ]
    list_filter = ['site', 'policy', 'unlock_start_date']
    search_fields = ['order__order_id', 'user__wallet_address']
    readonly_fields = ['schedule_id', 'created_at']
    raw_id_fields = ['order', 'user', 'allocation']


@admin.register(VestingRelease)
class VestingReleaseAdmin(admin.ModelAdmin):
    """
    释放明细管理
    
    ⭐ Phase E 核心管理界面
    """
    
    # ========== 列表显示 ==========
    
    list_display = [
        'mode_badge',  # ⭐ MOCK/LIVE 徽标
        'release_id_short',
        'schedule_order',
        'period_no',
        'amount_display',
        'release_date',
        'status_colored',  # ⭐ 着色状态
        'fireblocks_tx_id_short',
        'unlocked_at',
        'released_at'
    ]
    
    list_filter = [
        'status',
        'release_date',
        'schedule__site',
        'unlocked_at'
    ]
    
    search_fields = [
        'release_id',
        'schedule__order__order_id',
        'fireblocks_tx_id',
        'tx_hash'
    ]
    
    readonly_fields = [
        'release_id',
        'created_at',
        'updated_at',
        'fireblocks_tx_id',
        'tx_hash',
        'unlocked_at',
        'released_at'
    ]
    
    raw_id_fields = ['schedule']
    
    # ========== 默认排序和过滤 ==========
    
    ordering = ['-release_date', 'period_no']
    
    # 默认显示 unlocked 状态
    def changelist_view(self, request, extra_context=None):
        if 'status__exact' not in request.GET:
            q = request.GET.copy()
            q['status__exact'] = VestingRelease.STATUS_UNLOCKED
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)
    
    # ========== Actions ⭐ ==========
    
    actions = ['batch_release_action']
    
    def batch_release_action(self, request, queryset):
        """
        批量发放代币 Action
        
        ⭐ 限制:
        - 最多选择100条
        - 仅处理 unlocked 状态
        - 站点隔离
        - ⭐ v2.2.1: 限流 6次/分钟
        """
        # 0. ⭐ v2.2.1: 限流检查（防止误操作）
        from django.core.cache import cache
        
        cache_key = f'batch_release_limit_{request.user.id}'
        count_in_minute = cache.get(cache_key, 0)
        
        if count_in_minute >= 6:
            self.message_user(
                request,
                '⚠️ 操作过于频繁，请稍后再试（限制：6次/分钟）',
                level=messages.WARNING
            )
            return
        
        # 递增计数（60秒过期）
        cache.set(cache_key, count_in_minute + 1, 60)
        
        # 1. 数量检查
        count = queryset.count()
        if count > 100:
            self.message_user(
                request,
                f'❌ 批量发放最多100条，当前选择了 {count} 条',
                level=messages.ERROR
            )
            return
        
        # 2. 状态过滤
        unlocked_releases = queryset.filter(
            status=VestingRelease.STATUS_UNLOCKED
        )
        
        if unlocked_releases.count() == 0:
            self.message_user(
                request,
                '⚠️ 所选条目中没有 unlocked 状态的记录',
                level=messages.WARNING
            )
            return
        
        # 3. 站点隔离检查
        sites = set(
            r.schedule.allocation.order.site_id
            for r in unlocked_releases.select_related(
                'schedule__allocation__order'
            )
        )
        
        if len(sites) > 1:
            self.message_user(
                request,
                f'❌ 跨站点操作: {len(sites)} 个站点',
                level=messages.ERROR
            )
            return
        
        site_id = list(sites)[0]
        
        # 4. 执行批量发放
        try:
            release_ids = [str(r.release_id) for r in unlocked_releases]
            
            result = batch_release_vesting(
                release_ids=release_ids,
                operator_user=request.user,
                site_id=str(site_id)
            )
            
            # 5. 显示结果
            mode = getattr(settings, 'FIREBLOCKS_MODE', 'MOCK')
            mode_badge = '🧪 MOCK模式' if mode == 'MOCK' else '🔥 LIVE模式'
            
            self.message_user(
                request,
                format_html(
                    '<strong>{}</strong><br>'
                    '批量发放完成：<br>'
                    '✅ 提交: {} 条<br>'
                    '❌ 失败: {} 条<br>'
                    '⏭️ 跳过: {} 条<br>'
                    '💰 总金额: {} tokens',
                    mode_badge,
                    result['submitted'],
                    result['failed'],
                    result['skipped'],
                    result['total_amount']
                ),
                level=messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'❌ 批量发放失败: {str(e)}',
                level=messages.ERROR
            )
    
    batch_release_action.short_description = '📤 批量发放代币'
    
    # ========== 自定义列显示 ==========
    
    def mode_badge(self, obj):
        """
        显示 MOCK/LIVE 徽标
        
        ⭐ v2.2.2: MOCK 徽标更醒目
        """
        mode = getattr(settings, 'FIREBLOCKS_MODE', 'MOCK')
        
        if mode == 'MOCK':
            # ⭐ v2.2.2: 更醒目的 MOCK 徽标
            return format_html(
                '<span style="background: #ff9800; color: white; '
                'padding: 4px 12px; border-radius: 4px; font-size: 13px; '
                'font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">'
                '🧪 MOCK - No real transactions</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; '
                'padding: 4px 12px; border-radius: 4px; font-size: 13px; '
                'font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">'
                '🔥 LIVE - Production mode</span>'
            )
    
    mode_badge.short_description = 'Mode'
    
    def release_id_short(self, obj):
        """显示短ID"""
        return str(obj.release_id)[:8]
    
    release_id_short.short_description = 'Release ID'
    
    def schedule_order(self, obj):
        """显示订单"""
        order = obj.schedule.order
        return format_html(
            '<a href="/admin/orders/order/{}/change/">{}</a>',
            order.order_id,
            str(order.order_id)[:8]
        )
    
    schedule_order.short_description = 'Order'
    
    def amount_display(self, obj):
        """显示金额"""
        return f"{obj.amount:,.6f}"
    
    amount_display.short_description = 'Amount'
    
    def status_colored(self, obj):
        """⭐ 4态着色显示"""
        colors = {
            VestingRelease.STATUS_LOCKED: '#6c757d',      # 灰色
            VestingRelease.STATUS_UNLOCKED: '#28a745',    # 绿色
            VestingRelease.STATUS_PROCESSING: '#ffc107',  # 黄色
            VestingRelease.STATUS_RELEASED: '#007bff',    # 蓝色
        }
        
        color = colors.get(obj.status, '#000')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    status_colored.short_description = 'Status'
    
    def fireblocks_tx_id_short(self, obj):
        """显示短交易ID"""
        if obj.fireblocks_tx_id:
            if obj.fireblocks_tx_id.startswith('tx_mock_'):
                return format_html(
                    '<span style="color: #17a2b8;">🧪 {}</span>',
                    obj.fireblocks_tx_id[:16]
                )
            else:
                return obj.fireblocks_tx_id[:16]
        return '-'
    
    fireblocks_tx_id_short.short_description = 'TX ID'

