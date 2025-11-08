"""
SIWE 认证测试

⭐ 测试场景：
- Nonce 生成与消费
- Nonce 重放攻击
- SIWE 消息验证
- 域名/链/URI 校验
"""
from django.test import TestCase
from django.conf import settings

from apps.sites.models import Site
from .services.nonce import generate_nonce, consume_nonce, check_nonce_exists


class NonceServiceTestCase(TestCase):
    """Nonce 服务测试"""
    
    def test_generate_and_consume_nonce(self):
        """测试生成和消费nonce"""
        # 生成nonce
        nonce, expires_in = generate_nonce('NA', 'test')
        
        self.assertIsNotNone(nonce)
        self.assertEqual(expires_in, 300)  # 5分钟
        
        # 检查nonce存在
        exists = check_nonce_exists(nonce, 'NA', 'test')
        self.assertTrue(exists)
        
        # 消费nonce
        consumed = consume_nonce(nonce, 'NA', 'test')
        self.assertTrue(consumed)
        
        # 再次消费（应该失败 - 重放攻击）
        consumed_again = consume_nonce(nonce, 'NA', 'test')
        self.assertFalse(consumed_again)
    
    def test_nonce_site_isolation(self):
        """测试nonce站点隔离"""
        # 在NA站点生成nonce
        nonce, _ = generate_nonce('NA', 'test')
        
        # 尝试在ASIA站点消费（应该失败）
        consumed = consume_nonce(nonce, 'ASIA', 'test')
        self.assertFalse(consumed)
        
        # 在NA站点消费（应该成功）
        consumed = consume_nonce(nonce, 'NA', 'test')
        self.assertTrue(consumed)
    
    def test_nonce_env_isolation(self):
        """测试nonce环境隔离"""
        # 在prod环境生成nonce
        nonce, _ = generate_nonce('NA', 'prod')
        
        # 尝试在dev环境消费（应该失败）
        consumed = consume_nonce(nonce, 'NA', 'dev')
        self.assertFalse(consumed)
        
        # 在prod环境消费（应该成功）
        consumed = consume_nonce(nonce, 'NA', 'prod')
        self.assertTrue(consumed)


class SIWEVerificationTestCase(TestCase):
    """SIWE 验证测试（需要Mock）"""
    
    def setUp(self):
        """测试前置"""
        self.site = Site.objects.create(
            code='NA',
            name='North America',
            domain='na.posx.test',
            is_active=True
        )
    
    def test_siwe_domain_validation(self):
        """测试域名校验"""
        # 需要Mock SIWE消息
        # 此处为结构性测试
        pass
    
    def test_siwe_chain_id_validation(self):
        """测试链ID校验"""
        # 需要Mock SIWE消息
        pass
    
    def test_siwe_nonce_replay_attack(self):
        """测试nonce重放攻击"""
        # 需要Mock SIWE消息
        pass


class WalletUtilsTestCase(TestCase):
    """钱包工具测试"""
    
    def test_normalize_address(self):
        """测试地址标准化"""
        from .utils.wallet import normalize_address
        
        # 测试带0x前缀
        addr1 = normalize_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B')
        self.assertEqual(addr1, '0xab5801a7d398351b8be11c439e05c5b3259aec9b')
        
        # 测试不带0x前缀
        addr2 = normalize_address('Ab5801a7D398351b8bE11C439e05C5B3259aeC9B')
        self.assertEqual(addr2, '0xab5801a7d398351b8be11c439e05c5b3259aec9b')
    
    def test_validate_address(self):
        """测试地址验证"""
        from .utils.wallet import validate_address
        
        # 有效地址
        self.assertTrue(validate_address('0xab5801a7d398351b8be11c439e05c5b3259aec9b'))
        
        # 无效地址
        self.assertFalse(validate_address('0xinvalid'))
        self.assertFalse(validate_address(''))


class ReferralUtilsTestCase(TestCase):
    """推荐码工具测试"""
    
    def test_generate_referral_code(self):
        """测试推荐码生成"""
        from .utils.referral import generate_referral_code
        
        code = generate_referral_code('NA')
        
        self.assertTrue(code.startswith('NA-'))
        self.assertEqual(len(code), 9)  # NA-6chars
    
    def test_validate_referral_code(self):
        """测试推荐码验证"""
        from .utils.referral import validate_referral_code
        
        # 有效推荐码
        self.assertTrue(validate_referral_code('NA-ABC123'))
        self.assertTrue(validate_referral_code('ASIA-XYZ789'))
        
        # 无效推荐码
        self.assertFalse(validate_referral_code('invalid'))
        self.assertFalse(validate_referral_code('NA_ABC123'))  # 错误分隔符
        self.assertFalse(validate_referral_code(''))
    
    def test_referral_code_site_matching(self):
        """测试推荐码站点匹配"""
        from .utils.referral import validate_referral_code
        
        # 站点匹配
        self.assertTrue(validate_referral_code('NA-ABC123', 'NA'))
        
        # 站点不匹配
        self.assertFalse(validate_referral_code('NA-ABC123', 'ASIA'))


