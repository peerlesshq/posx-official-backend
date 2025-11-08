"""
订单定时任务

⭐ 功能：
- 自动取消超时订单（15分钟未支付）
- 回补库存
- 分页处理避免大事务

Celery配置：
# backend/config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'expire-pending-orders': {
        'task': 'apps.orders.tasks.expire_pending_orders',
        'schedule': crontab(minute='*/5'),  # 每5分钟运行一次
    },
}
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def expire_pending_orders(self):
    """
    自动取消超时订单
    
    ⚠️ 设计：
    - 每5分钟运行一次
    - 分页处理（避免大事务）
    - 查询 pending 且 expires_at <= now 的订单
    - 状态改为 cancelled
    - 回补库存
    
    Returns:
        dict: {
            'processed': int,
            'succeeded': int,
            'failed': int
        }
    """
    from apps.orders.models import Order
    from apps.tiers.services.inventory import release_inventory
    
    # 分页大小
    page_size = 100
    
    # 统计
    processed = 0
    succeeded = 0
    failed = 0
    
    # 当前时间
    cutoff = timezone.now()
    
    logger.info(f"Starting expire_pending_orders task, cutoff={cutoff}")
    
    while True:
        # 查询超时订单（分页）
        expired_orders = Order.objects.filter(
            status='pending',
            expires_at__lte=cutoff
        ).select_related('tier')[:page_size]
        
        # 转为列表（避免重复查询）
        expired_orders_list = list(expired_orders)
        
        if not expired_orders_list:
            logger.info(f"No more expired orders to process")
            break
        
        logger.info(f"Found {len(expired_orders_list)} expired orders")
        
        # 逐个处理
        for order in expired_orders_list:
            processed += 1
            
            try:
                with transaction.atomic():
                    # 更新订单状态
                    order.status = 'cancelled'
                    order.cancelled_reason = 'TIMEOUT'
                    order.cancelled_at = timezone.now()
                    order.save(update_fields=['status', 'cancelled_reason', 'cancelled_at', 'updated_at'])
                    
                    # 回补库存
                    success, error_code = release_inventory(
                        order.tier_id,
                        order.quantity
                    )
                    
                    if success:
                        logger.info(
                            f"Expired order cancelled and inventory released: {order.order_id}",
                            extra={
                                'order_id': str(order.order_id),
                                'tier_id': str(order.tier_id),
                                'quantity': order.quantity
                            }
                        )
                        succeeded += 1
                    else:
                        logger.error(
                            f"Failed to release inventory for expired order: {error_code}",
                            extra={
                                'order_id': str(order.order_id),
                                'error_code': error_code
                            }
                        )
                        # 订单已取消，但库存回补失败
                        # 记录到监控，需要人工介入
                        failed += 1
                        
            except Exception as e:
                logger.error(
                    f"Error processing expired order {order.order_id}: {e}",
                    exc_info=True,
                    extra={'order_id': str(order.order_id)}
                )
                failed += 1
        
        # 如果本批次少于page_size，说明已处理完
        if len(expired_orders_list) < page_size:
            break
    
    result = {
        'processed': processed,
        'succeeded': succeeded,
        'failed': failed
    }
    
    logger.info(
        f"Completed expire_pending_orders task: {result}",
        extra=result
    )
    
    return result


@shared_task
def check_order_payment_status(order_id: str):
    """
    检查订单支付状态（Webhook触发或定时检查）
    
    ⚠️ Phase D 实现
    - 查询 Stripe PaymentIntent 状态
    - 更新订单状态
    - 触发代币分配（如果成功）
    
    Args:
        order_id: 订单ID
    """
    logger.info(f"check_order_payment_status task: {order_id} (Phase D)")
    # Phase D implementation
    pass


@shared_task
def send_order_confirmation_email(order_id: str):
    """
    发送订单确认邮件（可选）
    
    Args:
        order_id: 订单ID
    """
    logger.info(f"send_order_confirmation_email task: {order_id} (optional)")
    # Optional implementation
    pass


@shared_task
def generate_order_receipt(order_id: str):
    """
    生成订单收据（可选）
    
    Args:
        order_id: 订单ID
    """
    logger.info(f"generate_order_receipt task: {order_id} (optional)")
    # Optional implementation
    pass


