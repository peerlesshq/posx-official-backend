"""
Orders App Django Admin Configuration

⭐ 注册模型：
- PromoCode: 促销码管理
- PromoCodeUsage: 促销码使用记录
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import PromoCode, PromoCodeUsage


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """
    Promo Code 管理
    
    功能：
    - 创建/编辑促销码
    - 查看使用情况
    - 批量停用
    """
    
    list_display = [
        'code',
        'name',
        'site_code',
        'discount_type_display',
        'discount_value_display',
        'usage_status',
        'valid_status',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'site',
        'discount_type',
        'is_active',
        'created_at',
    ]
    search_fields = [
        'code',
        'name',
        'description'
    ]
    readonly_fields = [
        'promo_id',
        'current_uses',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('promo_id', 'site', 'code', 'name', 'description')
        }),
        ('折扣配置', {
            'fields': (
                'discount_type',
                'discount_value',
                'bonus_tokens_value'
            )
        }),
        ('使用限制', {
            'fields': (
                'max_uses',
                'uses_per_user',
                'current_uses',
                'min_order_amount',
                'applicable_tiers'
            )
        }),
        ('有效期', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    filter_horizontal = ['applicable_tiers']
    actions = ['deactivate_promo_codes', 'activate_promo_codes']
    
    def site_code(self, obj):
        """站点代码"""
        return obj.site.code
    site_code.short_description = 'Site'
    
    def discount_type_display(self, obj):
        """折扣类型显示"""
        type_colors = {
            'percentage': '#2196F3',
            'fixed_amount': '#4CAF50',
            'bonus_tokens': '#FF9800',
            'combo': '#9C27B0'
        }
        color = type_colors.get(obj.discount_type, '#777')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_discount_type_display()
        )
    discount_type_display.short_description = 'Type'
    
    def discount_value_display(self, obj):
        """折扣值显示"""
        if obj.discount_type == PromoCode.DISCOUNT_TYPE_PERCENTAGE:
            return f"{obj.discount_value}%"
        elif obj.discount_type == PromoCode.DISCOUNT_TYPE_FIXED:
            return f"${obj.discount_value}"
        elif obj.discount_type == PromoCode.DISCOUNT_TYPE_BONUS_TOKENS:
            return f"+{obj.bonus_tokens_value} tokens"
        elif obj.discount_type == PromoCode.DISCOUNT_TYPE_COMBO:
            parts = []
            if obj.discount_value > 0:
                parts.append(f"{obj.discount_value}%")
            if obj.bonus_tokens_value > 0:
                parts.append(f"+{obj.bonus_tokens_value} tokens")
            return " + ".join(parts)
        return "-"
    discount_value_display.short_description = 'Value'
    
    def usage_status(self, obj):
        """使用情况"""
        if obj.max_uses is None:
            return format_html(
                '<span style="color: #4CAF50;">{} / ∞</span>',
                obj.current_uses
            )
        
        percentage = (obj.current_uses / obj.max_uses * 100) if obj.max_uses > 0 else 0
        color = '#f44336' if percentage >= 90 else ('#FF9800' if percentage >= 70 else '#4CAF50')
        
        return format_html(
            '<span style="color: {};">{} / {} ({}%)</span>',
            color,
            obj.current_uses,
            obj.max_uses,
            int(percentage)
        )
    usage_status.short_description = 'Usage'
    
    def valid_status(self, obj):
        """有效状态"""
        now = timezone.now()
        
        if now < obj.valid_from:
            return format_html(
                '<span style="color: #2196F3;">未开始</span><br><small>{}</small>',
                obj.valid_from.strftime('%Y-%m-%d %H:%M')
            )
        elif now > obj.valid_until:
            return format_html(
                '<span style="color: #f44336;">已过期</span><br><small>{}</small>',
                obj.valid_until.strftime('%Y-%m-%d %H:%M')
            )
        else:
            return format_html(
                '<span style="color: #4CAF50;">生效中</span><br><small>{}</small>',
                obj.valid_until.strftime('%Y-%m-%d %H:%M')
            )
    valid_status.short_description = 'Validity'
    
    def deactivate_promo_codes(self, request, queryset):
        """批量停用促销码"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"成功停用 {count} 个促销码")
    deactivate_promo_codes.short_description = "停用选中的促销码"
    
    def activate_promo_codes(self, request, queryset):
        """批量激活促销码"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"成功激活 {count} 个促销码")
    activate_promo_codes.short_description = "激活选中的促销码"


@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    """
    Promo Code 使用记录管理
    
    功能：
    - 查看使用记录
    - 统计分析
    """
    
    list_display = [
        'usage_id_short',
        'promo_code_code',
        'user_email',
        'order_id_short',
        'discount_applied',
        'bonus_tokens_applied',
        'created_at'
    ]
    list_filter = [
        'promo_code',
        'created_at',
    ]
    search_fields = [
        'promo_code__code',
        'user__email',
        'order__order_id'
    ]
    readonly_fields = [
        'usage_id',
        'promo_code',
        'order',
        'user',
        'discount_applied',
        'bonus_tokens_applied',
        'created_at'
    ]
    
    fieldsets = (
        ('关联信息', {
            'fields': ('usage_id', 'promo_code', 'order', 'user')
        }),
        ('应用结果', {
            'fields': ('discount_applied', 'bonus_tokens_applied')
        }),
        ('时间戳', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """禁止手动添加（由系统自动创建）"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """禁止删除（审计记录）"""
        return False
    
    def usage_id_short(self, obj):
        """使用记录ID（简写）"""
        return str(obj.usage_id)[:8] + '...'
    usage_id_short.short_description = 'Usage ID'
    
    def promo_code_code(self, obj):
        """促销码"""
        return obj.promo_code.code
    promo_code_code.short_description = 'Promo Code'
    
    def user_email(self, obj):
        """用户邮箱"""
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'User'
    
    def order_id_short(self, obj):
        """订单ID（简写）"""
        return str(obj.order.order_id)[:8] + '...'
    order_id_short.short_description = 'Order ID'

