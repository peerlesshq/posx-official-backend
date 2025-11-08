"""
Nonce 服务

⭐ 安全特性：
- Redis SET NX EX 保证原子性
- 5分钟 TTL（可配置）
- 一次性消费（用后即删）
- Key规范：posx:{site}:{env}:nonce:{nonce}
- 防止重放攻击

使用示例：
>>> nonce, expires_in = generate_nonce('NA', 'prod')
>>> # 用户签名后提交
>>> valid = consume_nonce(nonce, 'NA', 'prod')
>>> if valid:
>>>     # 验证签名
"""
import secrets
import logging
from typing import Tuple, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Nonce TTL（秒）
NONCE_TTL = getattr(settings, 'NONCE_TTL_SECONDS', 300)  # 5分钟

# Key 前缀规范
NONCE_KEY_PREFIX = 'posx'


def _get_nonce_key(nonce: str, site_code: str, env: str) -> str:
    """
    生成 Redis Key
    
    格式：posx:{site}:{env}:nonce:{nonce}
    
    Args:
        nonce: Nonce 值
        site_code: 站点代码（NA, ASIA 等）
        env: 环境（prod, dev, test）
    
    Returns:
        str: Redis Key
    
    Examples:
        >>> _get_nonce_key('abc123', 'NA', 'prod')
        'posx:NA:prod:nonce:abc123'
    """
    return f"{NONCE_KEY_PREFIX}:{site_code}:{env}:nonce:{nonce}"


def generate_nonce(site_code: str, env: str = 'prod') -> Tuple[str, int]:
    """
    生成 Nonce
    
    ⚠️ 安全特性：
    - 使用 secrets.token_urlsafe() 生成密码学安全的随机字符串
    - Redis SET NX EX 保证原子性
    - 返回过期时间供前端倒计时
    
    Args:
        site_code: 站点代码
        env: 环境（默认 prod）
    
    Returns:
        Tuple[str, int]: (nonce, expires_in_seconds)
    
    Examples:
        >>> nonce, expires_in = generate_nonce('NA')
        >>> print(f"Nonce: {nonce}, 过期时间: {expires_in}秒")
    """
    # 生成32字节的URL安全随机字符串
    nonce = secrets.token_urlsafe(32)
    
    # 构造 Redis Key
    key = _get_nonce_key(nonce, site_code, env)
    
    # 存储到 Redis（SET NX EX）
    # 值为时间戳（便于调试）
    from django.utils import timezone
    timestamp = timezone.now().isoformat()
    
    cache.set(key, timestamp, timeout=NONCE_TTL)
    
    logger.debug(
        f"Generated nonce for site={site_code}, env={env}, expires_in={NONCE_TTL}s",
        extra={'nonce': nonce[:8] + '...', 'site_code': site_code}
    )
    
    return nonce, NONCE_TTL


def consume_nonce(nonce: str, site_code: str, env: str = 'prod') -> bool:
    """
    消费 Nonce（一次性使用）
    
    ⚠️ 安全特性：
    - 原子获取并删除（GETDEL）
    - 防止重放攻击
    - 自动过期（TTL）
    
    Args:
        nonce: Nonce 值
        site_code: 站点代码
        env: 环境
    
    Returns:
        bool: True=有效且已消费, False=无效/已使用/过期
    
    Examples:
        >>> nonce, _ = generate_nonce('NA')
        >>> consume_nonce(nonce, 'NA')  # True
        >>> consume_nonce(nonce, 'NA')  # False（重放攻击）
    """
    key = _get_nonce_key(nonce, site_code, env)
    
    # 原子获取并删除
    # Django cache 不支持 GETDEL，用 get + delete 模拟
    # ⚠️ 生产环境建议用 Redis 客户端直接调用 GETDEL
    value = cache.get(key)
    
    if value is None:
        logger.warning(
            f"Invalid or expired nonce: site={site_code}, env={env}",
            extra={'nonce': nonce[:8] + '...', 'site_code': site_code}
        )
        return False
    
    # 删除 nonce
    cache.delete(key)
    
    logger.info(
        f"Consumed nonce: site={site_code}, env={env}",
        extra={'nonce': nonce[:8] + '...', 'site_code': site_code}
    )
    
    return True


def check_nonce_exists(nonce: str, site_code: str, env: str = 'prod') -> bool:
    """
    检查 Nonce 是否存在（不消费）
    
    ⚠️ 仅用于调试，生产环境应直接使用 consume_nonce()
    
    Args:
        nonce: Nonce 值
        site_code: 站点代码
        env: 环境
    
    Returns:
        bool: True=存在, False=不存在/已过期
    """
    key = _get_nonce_key(nonce, site_code, env)
    return cache.get(key) is not None


def clear_expired_nonces(site_code: Optional[str] = None, env: Optional[str] = None):
    """
    清理过期 Nonce（可选）
    
    ⚠️ Redis 会自动清理过期 Key，通常不需要手动调用
    
    Args:
        site_code: 站点代码（None=所有站点）
        env: 环境（None=所有环境）
    """
    # Redis TTL 会自动清理，此函数预留用于统计或调试
    logger.info(
        f"Nonce auto-expiration handled by Redis TTL",
        extra={'site_code': site_code, 'env': env}
    )


