"""
认证视图（SIWE钱包认证）

⭐ 端点：
- POST /api/v1/auth/nonce - 获取nonce（匿名）
- POST /api/v1/auth/wallet - 钱包认证/注册
- GET /api/v1/auth/me - 用户信息
- POST /api/v1/auth/wallet/bind - 绑定额外钱包

⭐ 权限：
- nonce: 匿名
- wallet: 匿名（认证/注册）
- me: IsAuthenticated
- wallet/bind: IsAuthenticated
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import User, Wallet
from .serializers_auth import (
    NonceResponseSerializer,
    WalletAuthRequestSerializer,
    WalletAuthResponseSerializer,
    UserSerializer,
    WalletBindRequestSerializer,
    WalletSerializer,
)
from .services.nonce import generate_nonce
from .services.siwe import verify_siwe_message, is_contract_wallet
from .utils.wallet import normalize_address, validate_address
from .utils.referral import generate_unique_referral_code

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def nonce(request):
    """
    获取 Nonce
    
    POST /api/v1/auth/nonce
    
    Response: 200
    {
        "nonce": "...",
        "expires_in": 300,
        "issued_at": "2025-11-08T..."
    }
    """
    # 从站点上下文获取site
    if not hasattr(request, 'site'):
        return Response({
            'code': 'SITE.NOT_FOUND',
            'message': '无法识别站点'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    site = request.site
    env = getattr(request._request.META, 'ENV', 'prod')
    
    # 生成nonce
    nonce_value, expires_in = generate_nonce(site.code, env)
    
    # 返回
    response_data = {
        'nonce': nonce_value,
        'expires_in': expires_in,
        'issued_at': timezone.now()
    }
    
    serializer = NonceResponseSerializer(response_data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def wallet_auth(request):
    """
    钱包认证/注册
    
    POST /api/v1/auth/wallet
    Body: {
        "message": "SIWE消息",
        "signature": "0x...",
        "referral_code": "NA-ABC123" (可选)
    }
    
    Response: 200
    {
        "user_id": "...",
        "wallet_address": "0xabc...",
        "referral_code": "NA-XYZ789",
        "is_new_user": true,
        "email": null
    }
    """
    # 验证请求数据
    serializer = WalletAuthRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    message = serializer.validated_data['message']
    signature = serializer.validated_data['signature']
    referral_code = serializer.validated_data.get('referral_code')
    
    site = request.site
    env = getattr(request._request.META, 'ENV', 'prod')
    
    # 验证 SIWE 消息
    try:
        result = verify_siwe_message(message, signature, site, consume_nonce=True)
    except Exception as e:
        logger.warning(f"SIWE verification failed: {e}")
        return Response({
            'code': 'AUTH.SIGNATURE_INVALID',
            'message': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not result['valid']:
        return Response({
            'code': result.get('error', 'AUTH.VERIFICATION_FAILED'),
            'message': result.get('message', 'Signature verification failed')
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    wallet_address = result['address']
    
    # 检查是否为合约钱包（Phase C 暂不支持）
    if is_contract_wallet(wallet_address):
        return Response({
            'code': 'AUTH.CONTRACT_WALLET_NOT_SUPPORTED',
            'message': 'Contract wallets are not supported in Phase C. Coming in Phase D.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 查询或创建用户
    is_new_user = False
    
    with transaction.atomic():
        # 查询钱包
        wallet = Wallet.objects.filter(address=wallet_address).first()
        
        if wallet:
            # 已有钱包，返回用户
            user = wallet.user
            logger.info(
                f"Existing user authenticated via wallet: {user.user_id}",
                extra={'user_id': str(user.user_id), 'wallet': wallet_address[:10] + '...'}
            )
        else:
            # 新钱包，创建用户
            is_new_user = True
            
            # 查找推荐人
            referrer = None
            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code, is_active=True)
                except User.DoesNotExist:
                    logger.warning(f"Invalid referral code: {referral_code}")
            
            # 生成推荐码
            def check_code_exists(code):
                return User.objects.filter(referral_code=code).exists()
            
            new_referral_code = generate_unique_referral_code(site.code, check_code_exists)
            
            # 创建用户
            user = User.objects.create(
                referral_code=new_referral_code,
                referrer=referrer,
                is_active=True
            )
            
            # 创建钱包
            wallet = Wallet.objects.create(
                user=user,
                address=wallet_address,
                is_primary=True
            )
            
            logger.info(
                f"New user created via wallet: {user.user_id}",
                extra={
                    'user_id': str(user.user_id),
                    'wallet': wallet_address[:10] + '...',
                    'referrer': str(referrer.user_id) if referrer else None
                }
            )
    
    # 返回
    response_data = {
        'user_id': user.user_id,
        'wallet_address': wallet_address,
        'referral_code': user.referral_code,
        'is_new_user': is_new_user,
        'email': user.email
    }
    
    response_serializer = WalletAuthResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    获取当前用户信息
    
    GET /api/v1/auth/me
    
    Response: 200
    {
        "user_id": "...",
        "email": null,
        "referral_code": "NA-XYZ789",
        "is_active": true,
        "primary_wallet": {...},
        "wallets_count": 1,
        "created_at": "..."
    }
    """
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bind_wallet(request):
    """
    绑定额外钱包
    
    POST /api/v1/auth/wallet/bind
    Body: {
        "message": "SIWE消息",
        "signature": "0x...",
        "is_primary": false
    }
    
    Response: 201
    {
        "wallet_id": "...",
        "address": "0x...",
        "is_primary": false,
        "created_at": "..."
    }
    """
    # 验证请求数据
    serializer = WalletBindRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    message = serializer.validated_data['message']
    signature = serializer.validated_data['signature']
    is_primary = serializer.validated_data.get('is_primary', False)
    
    site = request.site
    
    # 验证 SIWE 消息
    try:
        result = verify_siwe_message(message, signature, site, consume_nonce=True)
    except Exception as e:
        return Response({
            'code': 'AUTH.SIGNATURE_INVALID',
            'message': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not result['valid']:
        return Response({
            'code': result.get('error', 'AUTH.VERIFICATION_FAILED'),
            'message': result.get('message', 'Signature verification failed')
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    wallet_address = result['address']
    
    # 检查钱包是否已存在
    existing_wallet = Wallet.objects.filter(address=wallet_address).first()
    
    if existing_wallet:
        if existing_wallet.user != request.user:
            return Response({
                'code': 'WALLET.ALREADY_BOUND',
                'message': '该钱包已绑定到其他用户'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 已绑定到当前用户
        wallet_serializer = WalletSerializer(existing_wallet)
        return Response(wallet_serializer.data, status=status.HTTP_200_OK)
    
    # 创建新钱包
    with transaction.atomic():
        # 如果设置为主钱包，先取消其他主钱包
        if is_primary:
            Wallet.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
        
        wallet = Wallet.objects.create(
            user=request.user,
            address=wallet_address,
            is_primary=is_primary
        )
    
    logger.info(
        f"Wallet bound to user: {request.user.user_id}, wallet={wallet_address[:10]}...",
        extra={'user_id': str(request.user.user_id)}
    )
    
    wallet_serializer = WalletSerializer(wallet)
    return Response(wallet_serializer.data, status=status.HTTP_201_CREATED)


