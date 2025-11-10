"""
Errors App Configuration
"""
from django.apps import AppConfig


class ErrorsConfig(AppConfig):
    """Errors app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.errors'
    verbose_name = 'Error Management'


