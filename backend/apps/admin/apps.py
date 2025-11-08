"""
Admin API app configuration
"""
from django.apps import AppConfig


class AdminConfig(AppConfig):
    """Admin API application configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin'
    label = 'admin_api'  # ⭐ Unique label to avoid conflict with django.contrib.admin
    verbose_name = 'Admin API'



