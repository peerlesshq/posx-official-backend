"""
Notifications Admin

⭐ Django Admin 配置
"""
from django.contrib import admin
from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationChannelTask,
    NotificationPreference,
    NotificationReadReceipt
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """通知模板管理"""
    list_display = ['name', 'site_id', 'category', 'language', 'is_active', 'created_at']
    list_filter = ['category', 'language', 'is_active', 'created_at']
    search_fields = ['name', 'category', 'subcategory']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('site_id', 'parent_template_id', 'name', 'category', 'subcategory', 'language')
        }),
        ('模板内容', {
            'fields': ('title_template', 'body_template', 'channels', 'channel_configs')
        }),
        ('状态', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """通知记录管理"""
    list_display = ['notification_id', 'site_id', 'recipient_type', 'category', 'severity', 'read_at', 'created_at']
    list_filter = ['recipient_type', 'category', 'severity', 'created_at']
    search_fields = ['title', 'body', 'recipient_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('接收者信息', {
            'fields': ('site_id', 'recipient_type', 'recipient_id')
        }),
        ('通知分类', {
            'fields': ('category', 'subcategory', 'severity', 'source_type', 'source_id')
        }),
        ('通知内容', {
            'fields': ('title', 'body', 'payload', 'action_url')
        }),
        ('状态', {
            'fields': ('read_at', 'visible_at', 'expires_at', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(NotificationChannelTask)
class NotificationChannelTaskAdmin(admin.ModelAdmin):
    """渠道任务管理"""
    list_display = ['task_id', 'notification', 'channel', 'status', 'retry_count', 'sent_at', 'created_at']
    list_filter = ['channel', 'status', 'created_at']
    search_fields = ['notification__notification_id', 'target']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('任务信息', {
            'fields': ('notification', 'channel', 'target', 'payload')
        }),
        ('状态', {
            'fields': ('status', 'sent_at', 'retry_count', 'next_retry_at', 'last_error')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """用户偏好管理"""
    list_display = ['preference_id', 'site_id', 'user_id', 'channel', 'category', 'is_enabled']
    list_filter = ['channel', 'category', 'is_enabled']
    search_fields = ['user_id']


@admin.register(NotificationReadReceipt)
class NotificationReadReceiptAdmin(admin.ModelAdmin):
    """已读回执管理"""
    list_display = ['receipt_id', 'notification', 'user_id', 'read_at']
    list_filter = ['read_at']
    search_fields = ['notification__notification_id', 'user_id']
    date_hierarchy = 'read_at'

