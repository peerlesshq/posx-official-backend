"""
Test API View for Auth0 Authentication
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_auth(request):
    """
    测试 Auth0 认证
    需要有效的 JWT token
    """
    try:
        user_data = {
            'message': 'Authentication successful!',
            'user_id': str(request.user.user_id) if hasattr(request.user, 'user_id') else 'N/A',
            'auth0_sub': getattr(request.user, 'auth0_sub', 'N/A'),
            'email': getattr(request.user, 'email', None),
            'site_code': request.site.code if hasattr(request, 'site') else 'N/A',
            'timestamp': timezone.now().isoformat(),
        }
        logger.info(f"Auth test successful for user: {user_data}")
        return Response(user_data)
    except Exception as e:
        logger.error(f"Auth test error: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'message': 'Error in auth test'
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_public(request):
    """
    公开端点，不需要认证
    """
    return Response({
        'message': 'Public endpoint - no authentication required',
        'site_code': request.site.code if hasattr(request, 'site') else 'N/A',
        'timestamp': timezone.now().isoformat(),
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def test_config(request):
    """
    测试配置端点（公开，用于调试）
    """
    from django.conf import settings
    return Response({
        'AUTH0_DOMAIN': getattr(settings, 'AUTH0_DOMAIN', 'NOT_SET'),
        'AUTH0_ISSUER': getattr(settings, 'AUTH0_ISSUER', 'NOT_SET'),
        'AUTH0_AUDIENCE': getattr(settings, 'AUTH0_AUDIENCE', 'NOT_SET'),
        'site_code': request.site.code if hasattr(request, 'site') else 'N/A',
    })

