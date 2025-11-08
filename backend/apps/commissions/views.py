"""
Commission API Views and ViewSets
"""
from rest_framework import viewsets

from apps.commissions.serializers import CommissionViewSet

# ViewSet已在serializers.py中定义
# 这里仅导出，保持Django惯例
__all__ = ['CommissionViewSet']
