"""
订单预览API

⭐ 功能：
- 预览订单（计算价格、折扣、代币）
- 不创建实际订单
- 支持 Promo Code 验证

⭐ 端点：
- POST /api/v1/orders/preview/
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal

from apps.tiers.models import Tier
from .services.promo_service import validate_promo_code

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_preview(request):
    """
    订单预览（用户）
    
    POST /api/v1/orders/preview/
    Body: {
        "tier_id": "uuid",
        "quantity": 10,
        "promo_code": "SUMMER2025"  // 可选
    }
    
    Response: 200
    {
        "tier_name": "黄金套餐",
        "quantity": 10,
        "pricing": {
            "unit_price": "0.08",
            "subtotal": "0.80",
            "discount": "0.12",
            "final_price": "0.68"
        },
        "tokens": {
            "base_tokens": "9990.0",
            "tier_bonus": "1000.0",
            "promo_bonus": "0",
            "total_tokens": "10990.0"
        },
        "promo_code": {
            "code": "SUMMER2025",
            "description": "夏季促销15%折扣",
            "applied": true
        },
        "tier_promotion": {
            "active": true,
            "original_price": "0.10",
            "discount_percentage": "20.00"
        }
    }
    """
    # 验证请求数据
    tier_id = request.data.get('tier_id')
    quantity = request.data.get('quantity', 1)
    promo_code = request.data.get('promo_code')
    
    if not tier_id:
        return Response({
            'error': 'tier_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError("Quantity must be >= 1")
    except (ValueError, TypeError):
        return Response({
            'error': 'Invalid quantity'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 获取 Tier
    try:
        tier = Tier.objects.select_related('site').get(tier_id=tier_id, site=request.site)
    except Tier.DoesNotExist:
        return Response({
            'error': 'Tier not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # 计算价格
    unit_price = tier.get_current_price()
    subtotal = unit_price * quantity
    
    # 计算代币
    base_tokens = tier.tokens_per_unit * quantity
    tier_bonus_tokens = tier.bonus_tokens_per_unit * quantity
    
    # 应用 Promo Code（如果提供）
    discount = Decimal('0')
    promo_bonus_tokens = Decimal('0')
    promo_info = None
    
    if promo_code:
        validation_result = validate_promo_code(
            code=promo_code,
            site_id=request.site.site_id,
            user=request.user,
            tier=tier,
            order_amount=subtotal
        )
        
        if validation_result['valid']:
            discount = validation_result['discount_amount']
            promo_bonus_tokens = validation_result['bonus_tokens']
            
            # 构建 Promo Code 信息
            promo_obj = validation_result['promo']
            description_parts = []
            
            if promo_obj.discount_type == promo_obj.DISCOUNT_TYPE_PERCENTAGE:
                description_parts.append(f"{promo_obj.discount_value}%折扣")
            elif promo_obj.discount_type == promo_obj.DISCOUNT_TYPE_FIXED:
                description_parts.append(f"${discount}折扣")
            
            if promo_bonus_tokens > 0:
                description_parts.append(f"+{promo_bonus_tokens}代币")
            
            promo_info = {
                'code': promo_obj.code,
                'name': promo_obj.name,
                'description': ' + '.join(description_parts) if description_parts else promo_obj.description,
                'applied': True
            }
        else:
            # Promo Code 无效
            promo_info = {
                'code': promo_code,
                'applied': False,
                'error': validation_result.get('error'),
                'error_code': validation_result.get('error_code')
            }
    
    # 计算最终价格
    final_price = subtotal - discount
    if final_price < Decimal('0'):
        final_price = Decimal('0')
    
    # 计算总代币
    total_tokens = base_tokens + tier_bonus_tokens + promo_bonus_tokens
    
    # Tier 促销信息
    tier_promotion = None
    if tier.is_promotion_active():
        original_price = tier.list_price_usd
        discount_pct = Decimal('0')
        if original_price > 0:
            discount_pct = ((original_price - unit_price) / original_price) * 100
        
        tier_promotion = {
            'active': True,
            'original_price': str(original_price),
            'promotional_price': str(unit_price),
            'discount_percentage': str(discount_pct.quantize(Decimal('0.01'))),
            'ends_at': tier.promotion_valid_until.isoformat() if tier.promotion_valid_until else None
        }
    else:
        tier_promotion = {'active': False}
    
    # 构建响应
    response_data = {
        'tier_id': str(tier.tier_id),
        'tier_name': tier.name,
        'quantity': quantity,
        'pricing': {
            'unit_price': str(unit_price),
            'subtotal': str(subtotal),
            'discount': str(discount),
            'final_price': str(final_price)
        },
        'tokens': {
            'base_tokens': str(base_tokens),
            'tier_bonus': str(tier_bonus_tokens),
            'promo_bonus': str(promo_bonus_tokens),
            'total_tokens': str(total_tokens)
        },
        'tier_promotion': tier_promotion
    }
    
    if promo_info:
        response_data['promo_code'] = promo_info
    
    logger.info(
        f"Order preview generated",
        extra={
            'tier_id': str(tier.tier_id),
            'quantity': quantity,
            'final_price': str(final_price),
            'total_tokens': str(total_tokens),
            'promo_code': promo_code
        }
    )
    
    return Response(response_data, status=status.HTTP_200_OK)

