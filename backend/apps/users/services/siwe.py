"""
SIWE (Sign-In with Ethereum) 验签服务

⭐ EIP-4361 标准实现
⭐ 安全校验项：
1. domain - 必须匹配后端配置
2. chain_id - 必须匹配后端配置
3. uri - 必须匹配后端配置
4. nonce - 一次性消费 + TTL
5. expiration_time - 未过期
6. signature - EIP-191 签名验证

暂不支持：
❌ EIP-1271（合约钱包）- Phase D实现

使用示例：
>>> result = verify_siwe_message(message, signature, site)
>>> if result['valid']:
...     address = result['address']
...     # 创建/登录用户
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone as dt_timezone
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# 尝试导入 siwe 库
try:
    from siwe import SiweMessage
    from siwe.siwe import VerificationError, ExpiredMessage, MalformedSession
    SIWE_AVAILABLE = True
except ImportError:
    SIWE_AVAILABLE = False
    logger.warning("siwe library not installed. SIWE authentication will not work.")

# 尝试导入 eth_account
try:
    from eth_account.messages import encode_defunct
    from eth_account import Account
    ETH_ACCOUNT_AVAILABLE = True
except ImportError:
    ETH_ACCOUNT_AVAILABLE = False
    logger.warning("eth-account library not installed. Fallback signature verification disabled.")


class SIWEError(Exception):
    """SIWE 验证错误基类"""
    pass


class SIWEConfigError(SIWEError):
    """SIWE 配置错误"""
    pass


class SIWEVerificationError(SIWEError):
    """SIWE 验证失败"""
    pass


def _get_siwe_config() -> Dict[str, Any]:
    """
    获取 SIWE 配置
    
    Returns:
        dict: {domain, chain_id, uri}
    
    Raises:
        SIWEConfigError: 配置缺失
    """
    domain = getattr(settings, 'SIWE_DOMAIN', '')
    chain_id = getattr(settings, 'SIWE_CHAIN_ID', 1)
    uri = getattr(settings, 'SIWE_URI', '')
    
    if not domain:
        raise SIWEConfigError("SIWE_DOMAIN not configured")
    
    if not uri:
        raise SIWEConfigError("SIWE_URI not configured")
    
    return {
        'domain': domain,
        'chain_id': chain_id,
        'uri': uri
    }


def verify_siwe_message(
    message: str,
    signature: str,
    site,
    consume_nonce: bool = True
) -> Dict[str, Any]:
    """
    验证 SIWE 消息
    
    ⚠️ 安全校验（6项）：
    1. domain 匹配
    2. chain_id 匹配
    3. uri 匹配
    4. nonce 有效且一次性消费
    5. 未过期
    6. 签名正确（EIP-191）
    
    Args:
        message: SIWE 消息（纯文本）
        signature: 签名（hex字符串，带0x前缀）
        site: Site 实例
        consume_nonce: 是否消费 nonce（默认True）
    
    Returns:
        dict: {
            'valid': bool,
            'address': str,  # lowercase
            'nonce': str,
            'error': str  # 验证失败时
        }
    
    Raises:
        SIWEConfigError: 配置错误
        SIWEVerificationError: 验证失败
    
    Examples:
        >>> message = '''posx.io wants you to sign in...'''
        >>> signature = '0xabc123...'
        >>> result = verify_siwe_message(message, signature, site)
        >>> if result['valid']:
        ...     print(f"Address: {result['address']}")
    """
    # 检查库是否可用
    if not SIWE_AVAILABLE:
        raise SIWEConfigError("siwe library not installed")
    
    # 获取配置
    config = _get_siwe_config()
    
    try:
        # 解析 SIWE 消息
        siwe_message = SiweMessage.from_message(message=message)
        
        # 1. 验证 domain
        if siwe_message.domain != config['domain']:
            logger.warning(
                f"SIWE domain mismatch: expected={config['domain']}, got={siwe_message.domain}",
                extra={'site_code': site.code}
            )
            return {
                'valid': False,
                'error': 'SIWE.DOMAIN_MISMATCH',
                'message': f"Domain must be {config['domain']}"
            }
        
        # 2. 验证 chain_id
        if siwe_message.chain_id != config['chain_id']:
            logger.warning(
                f"SIWE chain_id mismatch: expected={config['chain_id']}, got={siwe_message.chain_id}",
                extra={'site_code': site.code}
            )
            return {
                'valid': False,
                'error': 'SIWE.CHAIN_MISMATCH',
                'message': f"Chain ID must be {config['chain_id']}"
            }
        
        # 3. 验证 uri
        if siwe_message.uri != config['uri']:
            logger.warning(
                f"SIWE URI mismatch: expected={config['uri']}, got={siwe_message.uri}",
                extra={'site_code': site.code}
            )
            return {
                'valid': False,
                'error': 'SIWE.URI_MISMATCH',
                'message': f"URI must be {config['uri']}"
            }
        
        # 4. 验证 nonce（一次性消费）
        if consume_nonce:
            from .nonce import consume_nonce as _consume_nonce
            
            env = getattr(settings, 'ENV', 'prod')
            nonce_valid = _consume_nonce(
                siwe_message.nonce,
                site.code,
                env
            )
            
            if not nonce_valid:
                logger.warning(
                    f"SIWE nonce invalid or expired",
                    extra={'site_code': site.code, 'nonce': siwe_message.nonce[:8] + '...'}
                )
                return {
                    'valid': False,
                    'error': 'AUTH.NONCE_INVALID',
                    'message': 'Nonce is invalid, expired, or already used'
                }
        
        # 5. 验证过期时间
        if siwe_message.expiration_time:
            # SIWE使用UTC时间
            expiration = siwe_message.expiration_time
            if isinstance(expiration, str):
                expiration = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
            
            now = datetime.now(dt_timezone.utc)
            if now >= expiration:
                logger.warning(
                    f"SIWE message expired",
                    extra={'site_code': site.code, 'expiration': expiration}
                )
                return {
                    'valid': False,
                    'error': 'AUTH.MESSAGE_EXPIRED',
                    'message': 'Message has expired'
                }
        
        # 6. 验证签名（EIP-191）
        try:
            # siwe库会自动验证签名
            siwe_message.verify(signature)
        except (VerificationError, ExpiredMessage, MalformedSession) as e:
            logger.warning(
                f"SIWE signature verification failed: {e}",
                extra={'site_code': site.code}
            )
            return {
                'valid': False,
                'error': 'AUTH.SIGNATURE_INVALID',
                'message': 'Signature verification failed'
            }
        
        # 验证成功
        address = siwe_message.address.lower()
        
        logger.info(
            f"SIWE verification successful",
            extra={
                'site_code': site.code,
                'address': address[:10] + '...',
                'nonce': siwe_message.nonce[:8] + '...'
            }
        )
        
        return {
            'valid': True,
            'address': address,
            'nonce': siwe_message.nonce,
            'issued_at': siwe_message.issued_at,
            'expiration_time': siwe_message.expiration_time
        }
        
    except Exception as e:
        logger.error(
            f"SIWE verification error: {e}",
            exc_info=True,
            extra={'site_code': site.code}
        )
        raise SIWEVerificationError(f"Failed to verify SIWE message: {e}") from e


def create_siwe_message_template(
    address: str,
    nonce: str,
    site
) -> str:
    """
    创建 SIWE 消息模板（供前端参考）
    
    ⚠️ 前端应使用 siwe 库生成消息，此函数仅供参考
    
    Args:
        address: 钱包地址
        nonce: Nonce
        site: Site 实例
    
    Returns:
        str: SIWE 消息模板
    """
    config = _get_siwe_config()
    
    # 当前时间（ISO 8601格式）
    issued_at = timezone.now().isoformat()
    
    # 模板
    template = f"""{config['domain']} wants you to sign in with your Ethereum account:
{address}

Sign in to POSX on {site.name}

URI: {config['uri']}
Version: 1
Chain ID: {config['chain_id']}
Nonce: {nonce}
Issued At: {issued_at}"""
    
    return template


def is_contract_wallet(address: str) -> bool:
    """
    检查是否为合约钱包（EIP-1271）
    
    ⚠️ Phase C 暂不支持，返回 False
    Phase D 实现：查询链上 code
    
    Args:
        address: 钱包地址
    
    Returns:
        bool: True=合约钱包, False=EOA钱包
    """
    # Phase C: 暂不支持合约钱包
    # Phase D: 使用 web3.eth.get_code(address) 检查
    return False


