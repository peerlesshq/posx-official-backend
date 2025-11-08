"""
金额处理工具

⭐ 核心原则：
- 所有金额使用 Decimal(18, 6)
- 禁止使用 float
- 与 Stripe 交互时转换为分（cents）
- 避免浮点误差

使用示例：
>>> from decimal import Decimal
>>> amount = Decimal('100.50')
>>> cents = to_cents(amount)  # 10050
>>> stripe.PaymentIntent.create(amount=cents, currency='usd')
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


# 金额精度（6位小数）
MONEY_PRECISION = Decimal('0.000001')

# Stripe 单位转换（1 USD = 100 cents）
STRIPE_UNIT_MULTIPLIER = 100


def quantize_money(amount: Union[Decimal, str, int, float]) -> Decimal:
    """
    标准化金额精度
    
    ⚠️ 统一使用6位小数精度
    
    Args:
        amount: 金额（支持多种类型，但推荐 Decimal）
    
    Returns:
        Decimal: 标准化后的金额
    
    Examples:
        >>> quantize_money(Decimal('100.123456789'))
        Decimal('100.123457')
        
        >>> quantize_money('99.9999995')
        Decimal('100.000000')
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    return amount.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def to_cents(amount: Union[Decimal, str]) -> int:
    """
    转换为 Stripe 金额（分）
    
    ⚠️ Stripe API 要求金额为整数（最小单位）
    - USD: 1 USD = 100 cents
    - EUR: 1 EUR = 100 cents
    
    Args:
        amount: 金额（Decimal 或字符串）
    
    Returns:
        int: Stripe 金额（分）
    
    Raises:
        ValueError: 金额为负数
    
    Examples:
        >>> to_cents(Decimal('100.50'))
        10050
        
        >>> to_cents('0.01')
        1
        
        >>> to_cents('99.999999')
        10000  # 四舍五入
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    if amount < 0:
        raise ValueError(f"金额不能为负数: {amount}")
    
    # 标准化精度
    amount = quantize_money(amount)
    
    # 转换为分（整数）
    cents = int(amount * STRIPE_UNIT_MULTIPLIER)
    
    return cents


def from_cents(cents: int) -> Decimal:
    """
    从 Stripe 金额（分）转回 Decimal
    
    Args:
        cents: Stripe 金额（分）
    
    Returns:
        Decimal: 标准化后的金额
    
    Examples:
        >>> from_cents(10050)
        Decimal('100.500000')
        
        >>> from_cents(1)
        Decimal('0.010000')
    """
    if cents < 0:
        raise ValueError(f"金额不能为负数: {cents}")
    
    amount = Decimal(cents) / STRIPE_UNIT_MULTIPLIER
    
    return quantize_money(amount)


def validate_amount(amount: Union[Decimal, str], min_amount: Decimal = None, max_amount: Decimal = None) -> Decimal:
    """
    验证并标准化金额
    
    Args:
        amount: 待验证的金额
        min_amount: 最小金额（可选）
        max_amount: 最大金额（可选）
    
    Returns:
        Decimal: 标准化后的金额
    
    Raises:
        ValueError: 金额非法
    
    Examples:
        >>> validate_amount('100.50', min_amount=Decimal('1'), max_amount=Decimal('1000'))
        Decimal('100.500000')
    """
    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except Exception as e:
            raise ValueError(f"无效的金额格式: {amount}") from e
    
    amount = quantize_money(amount)
    
    if amount < 0:
        raise ValueError(f"金额不能为负数: {amount}")
    
    if min_amount is not None and amount < min_amount:
        raise ValueError(f"金额不能小于 {min_amount}: {amount}")
    
    if max_amount is not None and amount > max_amount:
        raise ValueError(f"金额不能大于 {max_amount}: {amount}")
    
    return amount


def format_money(amount: Union[Decimal, str], currency: str = 'USD') -> str:
    """
    格式化金额为可读字符串
    
    Args:
        amount: 金额
        currency: 货币代码
    
    Returns:
        str: 格式化后的字符串
    
    Examples:
        >>> format_money(Decimal('1234.56'))
        '1,234.56 USD'
        
        >>> format_money('1000000.123456')
        '1,000,000.12 USD'
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # 显示时使用2位小数（标准货币格式）
    display_amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # 添加千分位分隔符
    formatted = f"{display_amount:,}"
    
    return f"{formatted} {currency}"


# ============================================
# Phase D: 佣金计算专用量化函数
# ⭐ 统一使用2位小数 ROUND_HALF_UP（与Stripe一致）
# ============================================

def quantize_commission(amount: Union[Decimal, str]) -> Decimal:
    """
    佣金计算专用量化（2位小数）
    
    ⭐ Phase D 修正：
    - 数据库存储：Decimal(18, 6)
    - 计算时量化：2位小数 ROUND_HALF_UP
    - 与 Stripe cents 一致
    
    Args:
        amount: 原始金额
    
    Returns:
        Decimal: 量化到2位小数的金额
    
    Examples:
        >>> quantize_commission(Decimal('12.346'))
        Decimal('12.35')
        
        >>> quantize_commission('10.004')
        Decimal('10.00')
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # 量化到2位小数（标准货币精度）
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_commission_amount(order_amount: Decimal, rate_percent: Decimal) -> Decimal:
    """
    计算佣金金额
    
    ⭐ 统一量化策略：
    1. 原始计算：order_amount * (rate / 100)
    2. 量化到2位小数：ROUND_HALF_UP
    
    Args:
        order_amount: 订单金额
        rate_percent: 佣金比例（如 12.00 表示 12%）
    
    Returns:
        Decimal: 佣金金额（2位小数）
    
    Examples:
        >>> calculate_commission_amount(Decimal('100.00'), Decimal('12.00'))
        Decimal('12.00')
        
        >>> calculate_commission_amount(Decimal('99.99'), Decimal('10.50'))
        Decimal('10.50')  # 99.99 * 0.105 = 10.4990 → 10.50
    """
    # 计算原始佣金
    raw_commission = order_amount * (rate_percent / Decimal('100'))
    
    # 量化到2位小数（与Stripe一致）⭐
    return quantize_commission(raw_commission)


# 导出常用精度
ZERO = Decimal('0.000000')
ONE_CENT = Decimal('0.010000')
TWO_DECIMAL_PRECISION = Decimal('0.01')  # Phase D: 佣金计算精度


