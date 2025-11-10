"""
Fireblocks客户端工厂
根据环境变量选择实现
"""
from django.conf import settings
from apps.vesting.ports import TokenPayoutPort
from apps.vesting.services.mock_fireblocks_client import MockFireblocksClient
from apps.vesting.services.fireblocks_client import FireblocksClient
import logging

logger = logging.getLogger(__name__)


def get_fireblocks_client() -> TokenPayoutPort:
    """
    获取Fireblocks客户端实例
    
    根据 settings.FIREBLOCKS_MODE 选择:
    - 'MOCK': MockFireblocksClient（开发/测试）
    - 'LIVE': FireblocksClient（生产）
    
    返回:
        TokenPayoutPort实现
    """
    mode = getattr(settings, 'FIREBLOCKS_MODE', 'MOCK')
    
    if mode == 'LIVE':
        logger.info("[ClientFactory] Using LIVE Fireblocks client")
        return FireblocksClient()
    else:
        logger.info("[ClientFactory] Using MOCK Fireblocks client")
        return MockFireblocksClient()

