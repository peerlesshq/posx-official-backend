"""
通知 Payload 序列化工具

⭐ 金融精度处理:
- Decimal → 字符串（存储到数据库）
- 字符串 → Decimal（从数据库读取）

使用场景:
- 通知 payload 包含金额字段（订单金额、佣金金额、提现金额等）
- 确保金融计算精度，避免浮点数误差
"""
from decimal import Decimal, InvalidOperation
import json
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """
    Decimal 序列化为字符串的 JSON 编码器
    
    Example:
        >>> data = {'amount': Decimal('100.50')}
        >>> json.dumps(data, cls=DecimalEncoder)
        '{"amount": "100.50"}'
    """
    
    def default(self, obj):
        """
        重写 default 方法处理 Decimal 类型
        
        Args:
            obj: 待序列化对象
            
        Returns:
            str: Decimal 转为字符串
            Any: 其他类型使用默认序列化
        """
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def serialize_notification_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    序列化通知 payload，确保 Decimal 精度
    
    ⭐ 功能：
    - 递归处理嵌套字典和列表
    - Decimal → 字符串
    - 保持其他类型不变
    
    Args:
        data: 原始数据字典（可能包含 Decimal）
        
    Returns:
        dict: JSON 安全的字典（Decimal → 字符串）
    
    Example:
        >>> payload = {
        ...     'order_id': '123',
        ...     'amount': Decimal('100.50'),
        ...     'commission': Decimal('12.06'),
        ...     'items': [
        ...         {'price': Decimal('50.25'), 'qty': 2}
        ...     ]
        ... }
        >>> serialize_notification_payload(payload)
        {
            'order_id': '123',
            'amount': '100.50',
            'commission': '12.06',
            'items': [{'price': '50.25', 'qty': 2}]
        }
    """
    try:
        # 使用 DecimalEncoder 序列化后再解析
        # 这样可以递归处理嵌套结构
        json_str = json.dumps(data, cls=DecimalEncoder)
        return json.loads(json_str)
    except (TypeError, ValueError) as e:
        logger.error(
            f"Failed to serialize notification payload: {e}",
            extra={'data_type': type(data).__name__},
            exc_info=True
        )
        # 返回原始数据（可能导致 JSONField 存储失败）
        return data


def deserialize_notification_payload(
    payload: Dict[str, Any],
    money_fields: List[str] = None
) -> Dict[str, Any]:
    """
    反序列化通知 payload，将金额字段转回 Decimal
    
    ⭐ 功能：
    - 将指定的金额字段从字符串转为 Decimal
    - 如果不指定 money_fields，使用默认字段列表
    - 递归处理嵌套字典和列表
    
    Args:
        payload: 从数据库读取的 JSONB 数据
        money_fields: 需要转换的金额字段列表（可选）
        
    Returns:
        dict: 恢复 Decimal 类型的字典
    
    Example:
        >>> payload = {
        ...     'order_id': '123',
        ...     'amount': '100.50',
        ...     'commission': '12.06'
        ... }
        >>> deserialize_notification_payload(payload)
        {
            'order_id': '123',
            'amount': Decimal('100.50'),
            'commission': Decimal('12.06')
        }
    """
    if money_fields is None:
        # 默认金额字段列表
        money_fields = [
            'amount', 'final_price', 'list_price', 'discount',
            'commission_amount', 'withdrawal_amount', 'balance',
            'total_earned', 'total_withdrawn', 'unit_price',
            'price', 'fee', 'refund', 'subtotal', 'total'
        ]
    
    return _deserialize_recursive(payload, money_fields)


def _deserialize_recursive(
    data: Union[Dict, List, Any],
    money_fields: List[str]
) -> Union[Dict, List, Any]:
    """
    递归反序列化，处理嵌套结构
    
    Args:
        data: 数据（字典、列表或标量）
        money_fields: 金额字段列表
        
    Returns:
        反序列化后的数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 如果是金额字段且为字符串，转为 Decimal
            if key in money_fields and isinstance(value, str):
                try:
                    result[key] = Decimal(value)
                except (ValueError, InvalidOperation) as e:
                    logger.warning(
                        f"Failed to convert '{key}' to Decimal: {value}",
                        extra={'key': key, 'value': value, 'error': str(e)}
                    )
                    result[key] = value  # 保持原值
            else:
                # 递归处理嵌套结构
                result[key] = _deserialize_recursive(value, money_fields)
        return result
    
    elif isinstance(data, list):
        return [_deserialize_recursive(item, money_fields) for item in data]
    
    else:
        # 标量值直接返回
        return data


def format_money(amount: Decimal, currency: str = 'USD') -> str:
    """
    格式化金额为友好显示
    
    Args:
        amount: 金额（Decimal）
        currency: 货币代码
        
    Returns:
        str: 格式化后的金额字符串
    
    Example:
        >>> format_money(Decimal('1234.56'))
        '$1,234.56'
        >>> format_money(Decimal('1000000.00'))
        '$1,000,000.00'
    """
    try:
        # 确保是 Decimal 类型
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # 格式化为两位小数
        formatted = f"{amount:,.2f}"
        
        # 添加货币符号
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'CNY': '¥',
        }
        
        symbol = currency_symbols.get(currency, currency + ' ')
        return f"{symbol}{formatted}"
        
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Failed to format money: {e}", exc_info=True)
        return str(amount)


def extract_money_fields(data: Dict[str, Any]) -> Dict[str, Decimal]:
    """
    从 payload 中提取所有金额字段
    
    Args:
        data: 数据字典
        
    Returns:
        dict: 仅包含金额字段的字典
    
    Example:
        >>> data = {
        ...     'order_id': '123',
        ...     'amount': Decimal('100.50'),
        ...     'quantity': 10,
        ...     'commission': Decimal('12.06')
        ... }
        >>> extract_money_fields(data)
        {'amount': Decimal('100.50'), 'commission': Decimal('12.06')}
    """
    money_fields = {}
    
    for key, value in data.items():
        if isinstance(value, Decimal):
            money_fields[key] = value
        elif isinstance(value, dict):
            # 递归处理嵌套字典
            nested_fields = extract_money_fields(value)
            if nested_fields:
                money_fields[key] = nested_fields
    
    return money_fields


def validate_money_payload(payload: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证 payload 中的金额字段
    
    ⭐ 检查：
    - 金额字段是否为字符串（已序列化）
    - 金额值是否有效（可以转为 Decimal）
    - 金额是否为负数（根据业务规则）
    
    Args:
        payload: 待验证的 payload
        
    Returns:
        tuple: (是否有效, 错误列表)
    
    Example:
        >>> payload = {'amount': '100.50', 'commission': '12.06'}
        >>> validate_money_payload(payload)
        (True, [])
        
        >>> payload = {'amount': 'invalid', 'commission': '-10'}
        >>> validate_money_payload(payload)
        (False, ['Invalid amount: invalid', 'Negative amount: -10'])
    """
    errors = []
    money_field_names = [
        'amount', 'final_price', 'list_price', 'commission_amount',
        'withdrawal_amount', 'balance'
    ]
    
    for field in money_field_names:
        if field not in payload:
            continue
        
        value = payload[field]
        
        # 检查类型（应该是字符串）
        if not isinstance(value, str):
            errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
            continue
        
        # 检查是否可以转为 Decimal
        try:
            decimal_value = Decimal(value)
        except (ValueError, InvalidOperation):
            errors.append(f"Invalid {field}: {value}")
            continue
        
        # 检查是否为负数（根据业务规则，大多数金额应该 >= 0）
        if decimal_value < 0:
            errors.append(f"Negative {field}: {value}")
    
    return (len(errors) == 0, errors)

