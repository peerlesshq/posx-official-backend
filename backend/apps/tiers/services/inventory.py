"""
库存服务（乐观锁）

⭐ 并发安全：
- 乐观锁（version字段）
- SQL UPDATE返回affected_rows校验
- 失败返回409 INVENTORY.CONFLICT
- 支持锁定和回补操作

使用示例：
>>> success, error = lock_inventory(tier_id, quantity=10)
>>> if not success:
...     return Response({'code': error}, status=409)
>>> # 订单创建成功
>>> # 如果取消：
>>> release_inventory(tier_id, quantity=10)
"""
import logging
from typing import Tuple
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)


class InventoryError(Exception):
    """库存操作错误"""
    pass


def lock_inventory(tier_id: uuid.UUID, quantity: int) -> Tuple[bool, str]:
    """
    锁定库存（乐观锁）
    
    ⚠️ 并发安全：
    - 使用 version 乐观锁
    - 检查 affected_rows
    - 失败返回 INVENTORY.CONFLICT（409）
    
    Args:
        tier_id: 档位ID
        quantity: 锁定数量
    
    Returns:
        Tuple[bool, str]: (success, error_code)
            - (True, ''): 成功
            - (False, 'TIER.NOT_FOUND'): 档位不存在
            - (False, 'TIER.INACTIVE'): 档位未激活
            - (False, 'INVENTORY.INSUFFICIENT'): 库存不足
            - (False, 'INVENTORY.CONFLICT'): 并发冲突
    
    Examples:
        >>> success, error = lock_inventory(tier_id, 10)
        >>> if not success:
        ...     if error == 'INVENTORY.CONFLICT':
        ...         return Response(status=409)
        ...     else:
        ...         return Response(status=400)
    """
    from apps.tiers.models import Tier
    
    # 参数校验
    if quantity <= 0:
        logger.warning(f"Invalid quantity: {quantity}")
        return False, 'INVENTORY.INVALID_QUANTITY'
    
    # 硬上限检查（防止恶意大单）
    max_quantity = getattr(settings, 'MAX_QUANTITY_PER_ORDER', 1000)
    if quantity > max_quantity:
        logger.warning(
            f"Quantity exceeds limit: {quantity} > {max_quantity}",
            extra={'tier_id': str(tier_id)}
        )
        return False, 'INVENTORY.QUANTITY_EXCEEDED'
    
    try:
        with transaction.atomic():
            # 获取当前档位（FOR UPDATE）
            try:
                tier = Tier.objects.select_for_update().get(tier_id=tier_id)
            except Tier.DoesNotExist:
                logger.warning(f"Tier not found: {tier_id}")
                return False, 'TIER.NOT_FOUND'
            
            # 检查激活状态
            if not tier.is_active:
                logger.warning(
                    f"Tier inactive: {tier_id}",
                    extra={'tier_id': str(tier_id)}
                )
                return False, 'TIER.INACTIVE'
            
            # 检查库存是否充足
            if tier.available_units < quantity:
                logger.warning(
                    f"Insufficient inventory: need={quantity}, available={tier.available_units}",
                    extra={'tier_id': str(tier_id)}
                )
                return False, 'INVENTORY.INSUFFICIENT'
            
            # 记录当前version
            current_version = tier.version
            
            # 乐观锁更新（关键！）
            affected = Tier.objects.filter(
                tier_id=tier_id,
                version=current_version,  # ⭐ 乐观锁条件
                available_units__gte=quantity  # ⭐ 双重检查
            ).update(
                available_units=F('available_units') - quantity,
                version=F('version') + 1,
                updated_at=timezone.now()
            )
            
            # 检查affected_rows（兜底校验）
            if affected == 0:
                # 并发冲突：version已变或库存已不足
                logger.warning(
                    f"Inventory lock conflict: tier_id={tier_id}, version={current_version}",
                    extra={'tier_id': str(tier_id), 'quantity': quantity}
                )
                return False, 'INVENTORY.CONFLICT'
            
            logger.info(
                f"Inventory locked: tier_id={tier_id}, quantity={quantity}, "
                f"available={tier.available_units} -> {tier.available_units - quantity}",
                extra={
                    'tier_id': str(tier_id),
                    'quantity': quantity,
                    'version': current_version
                }
            )
            
            return True, ''
            
    except Exception as e:
        logger.error(
            f"Error locking inventory: {e}",
            exc_info=True,
            extra={'tier_id': str(tier_id), 'quantity': quantity}
        )
        raise InventoryError(f"Failed to lock inventory: {e}") from e


def release_inventory(tier_id: uuid.UUID, quantity: int) -> Tuple[bool, str]:
    """
    回补库存（取消/超时/退款）
    
    ⚠️ 并发安全：
    - 同样使用 version 乐观锁
    - 确保回补的原子性
    
    Args:
        tier_id: 档位ID
        quantity: 回补数量
    
    Returns:
        Tuple[bool, str]: (success, error_code)
    
    Examples:
        >>> release_inventory(tier_id, 10)
        (True, '')
    """
    from apps.tiers.models import Tier
    
    if quantity <= 0:
        logger.warning(f"Invalid quantity: {quantity}")
        return False, 'INVENTORY.INVALID_QUANTITY'
    
    try:
        with transaction.atomic():
            # 获取当前档位
            try:
                tier = Tier.objects.select_for_update().get(tier_id=tier_id)
            except Tier.DoesNotExist:
                logger.warning(f"Tier not found: {tier_id}")
                return False, 'TIER.NOT_FOUND'
            
            current_version = tier.version
            
            # 回补库存（同样用乐观锁）
            affected = Tier.objects.filter(
                tier_id=tier_id,
                version=current_version
            ).update(
                available_units=F('available_units') + quantity,
                version=F('version') + 1,
                updated_at=timezone.now()
            )
            
            if affected == 0:
                # 并发冲突
                logger.warning(
                    f"Inventory release conflict: tier_id={tier_id}, version={current_version}",
                    extra={'tier_id': str(tier_id), 'quantity': quantity}
                )
                # 回补时冲突不是致命错误，可以重试
                return False, 'INVENTORY.CONFLICT'
            
            logger.info(
                f"Inventory released: tier_id={tier_id}, quantity={quantity}, "
                f"available={tier.available_units} -> {tier.available_units + quantity}",
                extra={
                    'tier_id': str(tier_id),
                    'quantity': quantity,
                    'version': current_version
                }
            )
            
            return True, ''
            
    except Exception as e:
        logger.error(
            f"Error releasing inventory: {e}",
            exc_info=True,
            extra={'tier_id': str(tier_id), 'quantity': quantity}
        )
        raise InventoryError(f"Failed to release inventory: {e}") from e


def check_inventory_available(tier_id: uuid.UUID, quantity: int) -> bool:
    """
    检查库存是否充足（不锁定）
    
    Args:
        tier_id: 档位ID
        quantity: 需要数量
    
    Returns:
        bool: True=充足, False=不足
    
    Examples:
        >>> if not check_inventory_available(tier_id, 10):
        ...     return Response({'error': 'Sold out'}, status=400)
    """
    from apps.tiers.models import Tier
    
    try:
        tier = Tier.objects.get(tier_id=tier_id)
        return tier.is_active and tier.available_units >= quantity
    except Tier.DoesNotExist:
        return False


def get_inventory_status(tier_id: uuid.UUID) -> dict:
    """
    获取库存状态
    
    Args:
        tier_id: 档位ID
    
    Returns:
        dict: {
            'total_units': int,
            'available_units': int,
            'sold_units': int,
            'is_sold_out': bool,
            'is_active': bool
        }
    """
    from apps.tiers.models import Tier
    
    try:
        tier = Tier.objects.get(tier_id=tier_id)
        
        sold_units = tier.total_units - tier.available_units
        
        return {
            'total_units': tier.total_units,
            'available_units': tier.available_units,
            'sold_units': sold_units,
            'is_sold_out': tier.available_units == 0,
            'is_active': tier.is_active,
            'version': tier.version
        }
    except Tier.DoesNotExist:
        return None


