"""
Promo Code 视图

⭐ 端点：
- POST /api/v1/admin/promo-codes/ - 创建（管理员）
- GET /api/v1/admin/promo-codes/ - 列表（管理员）
- GET /api/v1/admin/promo-codes/{id}/ - 详情（管理员）
- PATCH /api/v1/admin/promo-codes/{id}/ - 更新（管理员）
- POST /api/v1/admin/promo-codes/{id}/deactivate/ - 停用（管理员）
- POST /api/v1/promo-codes/validate/ - 验证（用户）

⭐ 权限：
- 管理端点：IsAdminUser
- 验证端点：IsAuthenticated
- 站点隔离：自动通过request.site过滤
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from decimal import Decimal

from .models import PromoCode, PromoCodeUsage
from .serializers_promo import (
    PromoCodeSerializer,
    PromoCodeListSerializer,
    PromoCodeValidateRequestSerializer,
    PromoCodeValidateResponseSerializer,
    PromoCodeUsageSerializer,
)
from .services.promo_service import validate_promo_code as validate_promo_code_service
from apps.tiers.models import Tier

logger = logging.getLogger(__name__)


class PromoCodeAdminViewSet(viewsets.ModelViewSet):
    """
    Promo Code 管理视图集（管理员）
    
    功能：
    - POST /api/v1/admin/promo-codes/ - 创建
    - GET /api/v1/admin/promo-codes/ - 列表
    - GET /api/v1/admin/promo-codes/{id}/ - 详情
    - PATCH /api/v1/admin/promo-codes/{id}/ - 更新
    - POST /api/v1/admin/promo-codes/{id}/deactivate/ - 停用
    """
    
    permission_classes = [IsAdminUser]
    lookup_field = 'promo_id'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        """
        获取查询集（站点隔离）
        
        ⭐ 安全：
        - 通过 request.site 显式过滤
        - RLS 策略提供二次保障
        """
        if not hasattr(self.request, 'site'):
            return PromoCode.objects.none()
        
        queryset = PromoCode.objects.filter(
            site=self.request.site
        ).select_related('site').prefetch_related('applicable_tiers')
        
        # 过滤参数
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        discount_type = self.request.query_params.get('discount_type')
        if discount_type:
            queryset = queryset.filter(discount_type=discount_type)
        
        # 搜索参数
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作返回序列化器"""
        if self.action == 'list':
            return PromoCodeListSerializer
        return PromoCodeSerializer
    
    def perform_create(self, serializer):
        """创建时自动设置site"""
        serializer.save(site=self.request.site)
    
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, id=None):
        """
        停用 Promo Code
        
        POST /api/v1/admin/promo-codes/{id}/deactivate/
        
        Response: 200
        {
            "message": "促销码已停用",
            "code": "SUMMER2025"
        }
        """
        promo = self.get_object()
        promo.is_active = False
        promo.save(update_fields=['is_active', 'updated_at'])
        
        logger.info(
            f"Promo code deactivated: {promo.code}",
            extra={'promo_id': str(promo.promo_id), 'code': promo.code}
        )
        
        return Response({
            'message': '促销码已停用',
            'code': promo.code
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_promo_code(request):
    """
    验证 Promo Code（用户）
    
    POST /api/v1/promo-codes/validate/
    Body: {
        "code": "SUMMER2025",
        "tier_id": "uuid",
        "quantity": 10
    }
    
    Response: 200
    {
        "valid": true,
        "code": "SUMMER2025",
        "discount_amount": "15.00",
        "bonus_tokens": "0",
        "final_price": "85.00",
        "message": "优惠码有效：享受15%折扣"
    }
    """
    # 验证请求数据
    request_serializer = PromoCodeValidateRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    
    code = request_serializer.validated_data['code']
    tier_id = request_serializer.validated_data['tier_id']
    quantity = request_serializer.validated_data['quantity']
    
    # 获取 Tier
    try:
        tier = Tier.objects.get(tier_id=tier_id, site=request.site)
    except Tier.DoesNotExist:
        return Response({
            'valid': False,
            'error': '产品不存在',
            'error_code': 'TIER_NOT_FOUND'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # 计算订单金额
    unit_price = tier.get_current_price()
    order_amount = unit_price * quantity
    
    # 验证 Promo Code
    try:
        validation_result = validate_promo_code_service(
            code=code,
            site_id=request.site.site_id,
            user=request.user,
            tier=tier,
            order_amount=order_amount
        )
    except Exception as e:
        logger.error(
            f"Error validating promo code: {e}",
            exc_info=True,
            extra={'code': code}
        )
        return Response({
            'valid': False,
            'error': '验证促销码时发生错误',
            'error_code': 'VALIDATION_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 构建响应
    if validation_result['valid']:
        discount_amount = validation_result['discount_amount']
        bonus_tokens = validation_result['bonus_tokens']
        final_price = order_amount - discount_amount
        
        # 构建提示信息
        message_parts = []
        if discount_amount > 0:
            if validation_result['promo'].discount_type == PromoCode.DISCOUNT_TYPE_PERCENTAGE:
                message_parts.append(f"享受{validation_result['promo'].discount_value}%折扣")
            else:
                message_parts.append(f"减免${discount_amount}")
        
        if bonus_tokens > 0:
            message_parts.append(f"额外获得{bonus_tokens}代币")
        
        message = '优惠码有效：' + '，'.join(message_parts) if message_parts else '优惠码有效'
        
        response_data = {
            'valid': True,
            'code': code,
            'discount_amount': str(discount_amount),
            'bonus_tokens': str(bonus_tokens),
            'final_price': str(final_price),
            'message': message,
        }
    else:
        response_data = {
            'valid': False,
            'code': code,
            'discount_amount': '0',
            'bonus_tokens': '0',
            'error': validation_result.get('error'),
            'error_code': validation_result.get('error_code'),
        }
    
    response_serializer = PromoCodeValidateResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def promo_code_usage_list(request, promo_id):
    """
    查询 Promo Code 使用记录（管理员）
    
    GET /api/v1/admin/promo-codes/{id}/usages/
    
    Response: 200
    [
        {
            "usage_id": "uuid",
            "user_email": "user@example.com",
            "order_id": "uuid",
            "discount_applied": "15.00",
            "bonus_tokens_applied": "0",
            "created_at": "2025-11-10T10:30:00Z"
        }
    ]
    """
    try:
        promo = PromoCode.objects.get(promo_id=promo_id, site=request.site)
    except PromoCode.DoesNotExist:
        return Response({
            'error': '促销码不存在',
            'error_code': 'PROMO_CODE_NOT_FOUND'
        }, status=status.HTTP_404_NOT_FOUND)
    
    usages = PromoCodeUsage.objects.filter(
        promo_code=promo
    ).select_related('user', 'order').order_by('-created_at')
    
    # 分页
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    usages_page = usages[start:end]
    serializer = PromoCodeUsageSerializer(usages_page, many=True)
    
    return Response({
        'results': serializer.data,
        'count': usages.count(),
        'page': page,
        'page_size': page_size
    }, status=status.HTTP_200_OK)

