"""
资产配置 CRUD API（Retool 对接）
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status
import logging

from apps.sites.models import ChainAssetConfig, Site

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_chain_assets(request):
    """
    GET /api/v1/admin/chain-assets?site=<code>
    
    列出站点的资产配置
    
    ⭐ Retool 对接：查询链/资产配置
    """
    site_code = request.headers.get('X-Site-Code')
    
    if not site_code:
        return Response(
            {'error': 'Missing X-Site-Code header'},
            status=http_status.HTTP_400_BAD_REQUEST
        )
    
    # 查询资产配置
    assets = ChainAssetConfig.objects.filter(
        site__code=site_code
    ).select_related('site')
    
    return Response({
        'results': [
            {
                'config_id': str(a.config_id),
                'chain': a.chain,
                'token_symbol': a.token_symbol,
                'token_decimals': a.token_decimals,
                'fireblocks_asset_id': a.fireblocks_asset_id,
                'fireblocks_vault_id': a.fireblocks_vault_id,
                'address_type': a.address_type,
                'is_active': a.is_active,
                'created_at': a.created_at.isoformat(),
            }
            for a in assets
        ]
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_or_update_chain_asset(request):
    """
    POST /api/v1/admin/chain-assets
    
    创建或更新资产配置
    
    Body:
    {
        "chain": "ETH",
        "token_symbol": "POSX",
        "token_decimals": 18,
        "fireblocks_asset_id": "POSX_ETH",
        "fireblocks_vault_id": "0",
        "address_type": "EVM",
        "is_active": true
    }
    
    ⭐ Retool 对接：配置资产
    """
    site_code = request.headers.get('X-Site-Code')
    
    try:
        site = Site.objects.get(code=site_code)
    except Site.DoesNotExist:
        return Response(
            {'error': 'Site not found'},
            status=http_status.HTTP_404_NOT_FOUND
        )
    
    data = request.data
    
    # 校验必填字段
    required = ['chain', 'token_symbol', 'token_decimals', 'fireblocks_asset_id']
    for field in required:
        if field not in data:
            return Response(
                {'error': f'Missing required field: {field}'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
    
    # 创建或更新
    asset, created = ChainAssetConfig.objects.update_or_create(
        site=site,
        chain=data['chain'],
        token_symbol=data['token_symbol'],
        defaults={
            'token_decimals': data['token_decimals'],
            'fireblocks_asset_id': data['fireblocks_asset_id'],
            'fireblocks_vault_id': data.get('fireblocks_vault_id', '0'),
            'address_type': data.get('address_type', 'EVM'),
            'is_active': data.get('is_active', True),
        }
    )
    
    logger.info(
        f"{'Created' if created else 'Updated'} chain asset config",
        extra={
            'config_id': str(asset.config_id),
            'site_code': site_code,
            'chain': asset.chain,
            'token_symbol': asset.token_symbol,
            'admin': request.user.email
        }
    )
    
    return Response({
        'status': 'created' if created else 'updated',
        'config_id': str(asset.config_id),
    }, status=http_status.HTTP_201_CREATED if created else http_status.HTTP_200_OK)

