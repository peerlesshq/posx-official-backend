"""
Notifications App Configuration
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Notifications app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'
    
    def ready(self):
        """Import signals when app is ready"""
        # import apps.notifications.signals  # TODO: 添加信号处理
        pass

