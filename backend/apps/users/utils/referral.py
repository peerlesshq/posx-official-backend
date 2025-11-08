"""
推荐码生成与验证

⭐ 格式规范：
- {SITE_CODE}-{RANDOM}
- 示例：NA-8F3K2A、ASIA-9XYZ12
- 长度：8-12字符（不含站点前缀）
- 字符集：大写字母 + 数字（易识别）

使用示例：
>>> code = generate_referral_code('NA')  # 'NA-8F3K2A'
>>> validate_referral_code(code, 'NA')  # True
"""
import random
import string
import logging
from typing import Optional
from django.db import IntegrityError

logger = logging.getLogger(__name__)

# 推荐码字符集（去除易混淆字符：0/O, 1/I/l）
REFERRAL_CHARSET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

# 随机部分长度
REFERRAL_RANDOM_LENGTH = 6

# 最大重试次数（冲突时）
MAX_RETRY = 10


def generate_referral_code(site_code: str, length: int = REFERRAL_RANDOM_LENGTH) -> str:
    """
    生成推荐码
    
    格式：{SITE_CODE}-{RANDOM}
    
    Args:
        site_code: 站点代码（NA, ASIA 等）
        length: 随机部分长度（默认6）
    
    Returns:
        str: 推荐码
    
    Examples:
        >>> generate_referral_code('NA')
        'NA-8F3K2A'
        
        >>> generate_referral_code('ASIA', length=8)
        'ASIA-9XYZ1234'
    """
    # 生成随机部分
    random_part = ''.join(random.choices(REFERRAL_CHARSET, k=length))
    
    # 组合
    code = f"{site_code.upper()}-{random_part}"
    
    return code


def generate_unique_referral_code(
    site_code: str,
    check_exists_func: callable,
    length: int = REFERRAL_RANDOM_LENGTH,
    max_retry: int = MAX_RETRY
) -> str:
    """
    生成唯一推荐码（带冲突重试）
    
    Args:
        site_code: 站点代码
        check_exists_func: 检查重复的函数（返回 bool）
        length: 随机部分长度
        max_retry: 最大重试次数
    
    Returns:
        str: 唯一推荐码
    
    Raises:
        RuntimeError: 达到最大重试次数仍冲突
    
    Examples:
        >>> def check_exists(code):
        ...     return User.objects.filter(referral_code=code).exists()
        >>> code = generate_unique_referral_code('NA', check_exists)
    """
    for attempt in range(max_retry):
        code = generate_referral_code(site_code, length)
        
        if not check_exists_func(code):
            logger.debug(
                f"Generated unique referral code on attempt {attempt + 1}",
                extra={'site_code': site_code, 'code': code}
            )
            return code
        
        logger.warning(
            f"Referral code collision on attempt {attempt + 1}: {code}",
            extra={'site_code': site_code}
        )
    
    # 达到最大重试次数
    raise RuntimeError(
        f"Failed to generate unique referral code after {max_retry} attempts. "
        f"Consider increasing random length."
    )


def validate_referral_code(code: str, site_code: Optional[str] = None) -> bool:
    """
    验证推荐码格式
    
    Args:
        code: 推荐码
        site_code: 站点代码（可选，提供时会校验前缀）
    
    Returns:
        bool: True=格式有效, False=格式无效
    
    Examples:
        >>> validate_referral_code('NA-8F3K2A')
        True
        
        >>> validate_referral_code('NA-8F3K2A', 'NA')
        True
        
        >>> validate_referral_code('NA-8F3K2A', 'ASIA')  # 站点不匹配
        False
        
        >>> validate_referral_code('invalid')
        False
    """
    if not code:
        return False
    
    # 检查格式：{SITE}-{RANDOM}
    parts = code.split('-')
    if len(parts) != 2:
        return False
    
    prefix, random_part = parts
    
    # 检查站点代码
    if site_code and prefix.upper() != site_code.upper():
        return False
    
    # 检查随机部分（只允许字母和数字）
    if not random_part.isalnum():
        return False
    
    # 检查长度（合理范围）
    if len(random_part) < 4 or len(random_part) > 12:
        return False
    
    return True


def parse_referral_code(code: str) -> Optional[dict]:
    """
    解析推荐码
    
    Args:
        code: 推荐码
    
    Returns:
        dict: {'site_code': '...', 'random': '...'} 或 None
    
    Examples:
        >>> parse_referral_code('NA-8F3K2A')
        {'site_code': 'NA', 'random': '8F3K2A'}
        
        >>> parse_referral_code('invalid')
        None
    """
    if not validate_referral_code(code):
        return None
    
    parts = code.split('-')
    return {
        'site_code': parts[0].upper(),
        'random': parts[1]
    }


def normalize_referral_code(code: str) -> str:
    """
    标准化推荐码（uppercase）
    
    Args:
        code: 推荐码
    
    Returns:
        str: 标准化后的推荐码
    
    Examples:
        >>> normalize_referral_code('na-8f3k2a')
        'NA-8F3K2A'
    """
    if not code:
        return ''
    
    return code.upper().strip()


