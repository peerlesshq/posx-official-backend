"""
订单视图

⭐ 端点：
- POST /api/v1/orders/ - 创建订单（幂等）
- GET /api/v1/orders/ - 订单列表（分页 + 过滤）
- GET /api/v1/orders/{id}/ - 订单详情
- POST /api/v1/orders/{id}/cancel/ - 取消订单

⭐ 权限：
- 创建/查询/取消：IsAuthenticated
- 站点隔离：自动通过request.site过滤
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Order
from .serializers import (
    OrderCreateRequestSerializer,
    OrderCreateResponseSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderCancelRequestSerializer,
)
from .services.order_service import create_order, cancel_order

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    订单视图集
    
    功能：
    - POST /api/v1/orders/ - 创建订单
    - GET /api/v1/orders/ - 列表
    - GET /api/v1/orders/{id}/ - 详情
    - POST /api/v1/orders/{id}/cancel/ - 取消
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        """
        获取查询集（站点隔离）
        
        ⭐ 安全：
        - 通过 request.site 显式过滤
        - RLS 策略提供二次保障
        - 仅返回当前用户的订单
        """
        if not hasattr(self.request, 'site'):
            return Order.objects.none()
        
        queryset = Order.objects.filter(
            site=self.request.site,
            buyer=self.request.user
        ).select_related('site', 'buyer', 'referrer').prefetch_related('items__tier')
        
        # 过滤参数
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 买家地址过滤
        buyer_wallet = self.request.query_params.get('buyer')
        if buyer_wallet:
            queryset = queryset.filter(wallet_address__icontains=buyer_wallet)
        
        # 时间范围过滤
        created_after = self.request.query_params.get('created_after')
        if created_after:
            try:
                from django.utils.dateparse import parse_datetime
                created_after_dt = parse_datetime(created_after)
                if created_after_dt:
                    queryset = queryset.filter(created_at__gte=created_after_dt)
            except ValueError:
                pass
        
        created_before = self.request.query_params.get('created_before')
        if created_before:
            try:
                from django.utils.dateparse import parse_datetime
                created_before_dt = parse_datetime(created_before)
                if created_before_dt:
                    queryset = queryset.filter(created_at__lte=created_before_dt)
            except ValueError:
                pass
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作返回序列化器"""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateRequestSerializer
        elif self.action == 'cancel':
            return OrderCancelRequestSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """
        创建订单（幂等）
        
        POST /api/v1/orders/
        Header: Idempotency-Key (可选但推荐)
        Body: {
            "tier_id": "uuid",
            "quantity": 1,
            "wallet_address": "0xabc...",
            "referral_code": "NA-ABC123"
        }
        
        Response: 200
        {
            "order_id": "uuid",
            "status": "pending",
            "final_price_usd": "100.50",
            "expires_at": "2025-11-08T12:15:00Z",
            "stripe": {
                "payment_intent_id": "pi_...",
                "client_secret": "pi_..._secret_..."
            }
        }
        """
        # 验证请求数据
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 提取参数
        tier_id = serializer.validated_data['tier_id']
        quantity = serializer.validated_data['quantity']
        wallet_address = serializer.validated_data['wallet_address']
        referral_code = serializer.validated_data.get('referral_code')
        
        # 获取幂等键（从Header）
        idempotency_key = request.META.get('HTTP_IDEMPOTENCY_KEY')
        
        # 创建订单
        try:
            order, client_secret = create_order(
                site_id=request.site.site_id,
                tier_id=tier_id,
                quantity=quantity,
                wallet_address=wallet_address,
                referral_code=referral_code,
                idempotency_key=idempotency_key,
                user=request.user
            )
        except Exception as e:
            logger.error(
                f"Failed to create order: {e}",
                exc_info=True,
                extra={
                    'user_id': str(request.user.user_id),
                    'tier_id': str(tier_id)
                }
            )
            
            # 根据错误类型返回适当的响应
            error_message = str(e)
            
            if 'INVENTORY' in error_message:
                error_code = 'INVENTORY.CONFLICT'
                http_status = status.HTTP_409_CONFLICT
            elif 'TIER' in error_message:
                error_code = 'TIER.INVALID'
                http_status = status.HTTP_400_BAD_REQUEST
            else:
                error_code = 'ORDERS.CREATE_FAILED'
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            return Response({
                'code': error_code,
                'message': error_message,
                'request_id': getattr(request, 'request_id', 'unknown')
            }, status=http_status)
        
        # 成功响应
        response_data = {
            'order_id': order.order_id,
            'status': order.status,
            'final_price_usd': order.final_price_usd,
            'expires_at': order.expires_at,
            'stripe': {
                'payment_intent_id': order.stripe_payment_intent_id,
                'client_secret': client_secret
            }
        }
        
        response_serializer = OrderCreateResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, id=None):
        """
        取消订单
        
        POST /api/v1/orders/{id}/cancel/
        Body: {
            "reason": "USER_CANCELLED"
        }
        
        Response: 200
        {
            "order_id": "uuid",
            "status": "cancelled",
            "message": "订单已取消"
        }
        """
        order = self.get_object()
        
        # 验证请求数据
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data.get('reason', 'USER_CANCELLED')
        
        # 取消订单
        try:
            cancelled_order = cancel_order(order.order_id, reason)
        except Exception as e:
            logger.error(
                f"Failed to cancel order: {e}",
                exc_info=True,
                extra={'order_id': str(order.order_id)}
            )
            
            return Response({
                'code': 'ORDERS.CANCEL_FAILED',
                'message': str(e),
                'request_id': getattr(request, 'request_id', 'unknown')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 返回
        return Response({
            'order_id': str(cancelled_order.order_id),
            'status': cancelled_order.status,
            'message': '订单已取消'
        }, status=status.HTTP_200_OK)


