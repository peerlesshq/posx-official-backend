"""
Notification Serializers
"""
from rest_framework import serializers
from .models import Notification, NotificationReadReceipt


class NotificationSerializer(serializers.ModelSerializer):
    """
    通知序列化器
    
    用于用户查看通知列表和详情
    """
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'recipient_type',
            'category',
            'subcategory',
            'severity',
            'source_type',
            'source_id',
            'title',
            'body',
            'payload',
            'action_url',
            'read_at',
            'is_read',
            'visible_at',
            'expires_at',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_is_read(self, obj):
        """
        判断是否已读
        
        - 个人通知：检查 read_at
        - 站点广播：检查 NotificationReadReceipt
        """
        if obj.recipient_type == Notification.RECIPIENT_SITE_BROADCAST:
            # 站点广播：从 context 获取用户 ID
            user_id = self.context.get('user_id')
            if user_id:
                return NotificationReadReceipt.objects.filter(
                    notification=obj,
                    user_id=user_id
                ).exists()
            return False
        else:
            # 个人通知：检查 read_at
            return obj.read_at is not None


class NotificationListSerializer(serializers.ModelSerializer):
    """
    通知列表序列化器（简化版）
    """
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'category',
            'severity',
            'title',
            'read_at',
            'is_read',
            'visible_at',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_is_read(self, obj):
        """判断是否已读"""
        if obj.recipient_type == Notification.RECIPIENT_SITE_BROADCAST:
            user_id = self.context.get('user_id')
            if user_id:
                return NotificationReadReceipt.objects.filter(
                    notification=obj,
                    user_id=user_id
                ).exists()
            return False
        else:
            return obj.read_at is not None


class MarkReadSerializer(serializers.Serializer):
    """
    标记已读序列化器
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="通知 ID 列表（批量标记）"
    )
    mark_all = serializers.BooleanField(
        default=False,
        help_text="标记全部已读"
    )
    
    def validate(self, data):
        """验证：必须提供 notification_ids 或 mark_all"""
        if not data.get('notification_ids') and not data.get('mark_all'):
            raise serializers.ValidationError(
                "必须提供 notification_ids 或设置 mark_all=true"
            )
        return data


class UnreadCountSerializer(serializers.Serializer):
    """
    未读数统计序列化器
    """
    total = serializers.IntegerField(help_text="总未读数")
    by_category = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="按分类统计"
    )
    by_severity = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="按严重度统计"
    )

