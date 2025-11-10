"""
系统配置查询 API（Retool 对接）
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_allow_prod_tx_status(request):
    """
    GET /api/v1/admin/config/allow-prod-tx
    
    返回 ALLOW_PROD_TX 和 FIREBLOCKS_MODE 状态
    
    ⭐ Retool 对接：检查生产交易开关
    """
    allow_prod_tx = getattr(settings, 'ALLOW_PROD_TX', False)
    fireblocks_mode = getattr(settings, 'FIREBLOCKS_MODE', 'SANDBOX')
    
    return Response({
        'allow_prod_tx': allow_prod_tx,
        'fireblocks_mode': fireblocks_mode,
        'warning': None if allow_prod_tx else '⚠️ LIVE模式已拦截：ALLOW_PROD_TX=0'
    })

