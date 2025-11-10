"""
Vesting App配置
"""
from django.apps import AppConfig


class VestingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vesting'
    verbose_name = 'Vesting Management'

