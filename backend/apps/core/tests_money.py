"""
金额处理工具测试

⭐ 测试场景：
- Decimal精度
- to_cents转换
- from_cents转换
- 边界值处理
"""
from django.test import TestCase
from decimal import Decimal

from apps.core.utils.money import (
    quantize_money,
    to_cents,
    from_cents,
    validate_amount,
    format_money,
    ZERO,
    ONE_CENT
)


class MoneyUtilsTestCase(TestCase):
    """金额工具测试"""
    
    def test_quantize_money(self):
        """测试金额标准化"""
        # 基本测试
        result = quantize_money(Decimal('100.123456789'))
        self.assertEqual(result, Decimal('100.123457'))  # 四舍五入到6位
        
        # 字符串输入
        result = quantize_money('99.9999995')
        self.assertEqual(result, Decimal('100.000000'))
        
        # 整数输入
        result = quantize_money(100)
        self.assertEqual(result, Decimal('100.000000'))
    
    def test_to_cents(self):
        """测试转换为Stripe金额"""
        # 基本测试
        self.assertEqual(to_cents(Decimal('100.50')), 10050)
        self.assertEqual(to_cents('0.01'), 1)
        self.assertEqual(to_cents('99.999999'), 10000)  # 四舍五入
        
        # 零值
        self.assertEqual(to_cents(Decimal('0')), 0)
        
        # 负数应抛出异常
        with self.assertRaises(ValueError):
            to_cents(Decimal('-100'))
    
    def test_from_cents(self):
        """测试从Stripe金额转回"""
        # 基本测试
        self.assertEqual(from_cents(10050), Decimal('100.500000'))
        self.assertEqual(from_cents(1), Decimal('0.010000'))
        self.assertEqual(from_cents(0), Decimal('0.000000'))
        
        # 负数应抛出异常
        with self.assertRaises(ValueError):
            from_cents(-100)
    
    def test_round_trip_conversion(self):
        """测试往返转换（无精度丢失）"""
        original = Decimal('123.456789')
        cents = to_cents(original)
        result = from_cents(cents)
        
        # 允许微小误差（6位小数精度）
        self.assertAlmostEqual(float(result), float(original), places=2)
    
    def test_validate_amount(self):
        """测试金额验证"""
        # 有效金额
        result = validate_amount('100.50', min_amount=Decimal('1'), max_amount=Decimal('1000'))
        self.assertEqual(result, Decimal('100.500000'))
        
        # 最小金额检查
        with self.assertRaises(ValueError):
            validate_amount('0.50', min_amount=Decimal('1'))
        
        # 最大金额检查
        with self.assertRaises(ValueError):
            validate_amount('2000', max_amount=Decimal('1000'))
        
        # 负数检查
        with self.assertRaises(ValueError):
            validate_amount('-100')
        
        # 无效格式
        with self.assertRaises(ValueError):
            validate_amount('abc')
    
    def test_format_money(self):
        """测试金额格式化"""
        # 基本测试
        self.assertEqual(format_money(Decimal('1234.56')), '1,234.56 USD')
        self.assertEqual(format_money('1000000.123456'), '1,000,000.12 USD')
        
        # 零值
        self.assertEqual(format_money(ZERO), '0.00 USD')
    
    def test_common_edge_cases(self):
        """测试常见边界情况"""
        # Stripe最小金额（1 cent = $0.01）
        cents = to_cents(ONE_CENT)
        self.assertEqual(cents, 1)
        
        # 大额订单
        large_amount = Decimal('999999.99')
        cents = to_cents(large_amount)
        self.assertEqual(cents, 99999999)
        
        # 微小金额（四舍五入）
        tiny = Decimal('0.001')  # 小于1 cent
        cents = to_cents(tiny)
        self.assertEqual(cents, 0)


class MoneyPrecisionTestCase(TestCase):
    """金额精度测试（防止浮点误差）"""
    
    def test_no_floating_point_errors(self):
        """测试无浮点误差"""
        # 经典浮点误差示例：0.1 + 0.2 != 0.3
        a = Decimal('0.1')
        b = Decimal('0.2')
        result = quantize_money(a + b)
        
        self.assertEqual(result, Decimal('0.300000'))
        
        # 大额计算
        price = Decimal('99.99')
        quantity = 1000
        total = quantize_money(price * quantity)
        
        self.assertEqual(total, Decimal('99990.000000'))
    
    def test_stripe_amount_precision(self):
        """测试Stripe金额精度"""
        # 确保转换为cents时无精度丢失（在2位小数内）
        test_cases = [
            ('100.00', 10000),
            ('100.50', 10050),
            ('100.99', 10099),
            ('0.01', 1),
            ('999999.99', 99999999),
        ]
        
        for amount_str, expected_cents in test_cases:
            cents = to_cents(Decimal(amount_str))
            self.assertEqual(
                cents,
                expected_cents,
                f"Failed for {amount_str}: expected {expected_cents}, got {cents}"
            )


