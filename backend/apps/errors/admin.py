"""
Error Management Admin
"""
from django.contrib import admin
from apps.errors.models import ErrorCode, ErrorMessage


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    """错误码管理"""
    list_display = ['code', 'domain', 'severity', 'http_status', 'retryable', 'is_active', 'owner_team']
    list_filter = ['domain', 'severity', 'retryable', 'is_active', 'ui_type']
    search_fields = ['code', 'default_msg_key', 'owner_team']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'domain', 'http_status', 'severity', 'ui_type')
        }),
        ('行为配置', {
            'fields': ('retryable', 'default_actions', 'default_msg_key')
        }),
        ('治理信息', {
            'fields': ('owner_team', 'runbook_url', 'is_active')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ErrorMessage)
class ErrorMessageAdmin(admin.ModelAdmin):
    """错误消息文案管理"""
    list_display = ['msg_key', 'language', 'title', 'created_at']
    list_filter = ['language']
    search_fields = ['msg_key', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('msg_key', 'language', 'title', 'message')
        }),
        ('动作文案', {
            'fields': ('action_labels',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )


