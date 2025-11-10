"""
MOCK Fireblocks客户端
用于开发和测试环境，不依赖真实凭证
"""
import uuid
import logging
from decimal import Decimal
from typing import Dict
from django.conf import settings

logger = logging.getLogger(__name__)


class MockFireblocksClient:
    """
    模拟Fireblocks客户端
    
    特性:
    - 生成 tx_mock_<uuid> 格式的交易ID
    - 延迟触发 webhook（通过 Celery）
    - 无需真实API凭证
    - ⭐ v2.2.2: 凭证误配置检测
    """
    
    def __init__(self):
        self.mode = 'MOCK'
        
        # ⭐ v2.2.2: 检测真实凭证误配置
        api_key = getattr(settings, 'FIREBLOCKS_API_KEY', '')
        if api_key:
            logger.warning(
                "⚠️ MOCK模式检测到真实 FIREBLOCKS_API_KEY！"
                "该凭证已被忽略。如需使用 LIVE 模式，请设置 FIREBLOCKS_MODE=LIVE",
                extra={
                    'mode': 'MOCK',
                    'api_key_configured': bool(api_key),
                    'reminder': '请检查 .env 配置是否正确'
                }
            )
        
        logger.info("[MockFireblocks] Initialized MOCK client")
    
    def create_transaction(
        self,
        to_address: str,
        amount: Decimal,
        note: str = ''
    ) -> str:
        """
        创建模拟交易
        
        参数:
            to_address: 接收地址
            amount: 代币数量
            note: 备注
        
        返回:
            交易ID（格式: tx_mock_<uuid>）
        """
        # 生成模拟交易ID
        tx_id = f"tx_mock_{uuid.uuid4().hex[:16]}"
        
        logger.info(
            f"[MockFireblocks] Transaction created",
            extra={
                'tx_id': tx_id,
                'to_address': to_address,
                'amount': str(amount),
                'note': note
            }
        )
        
        # 调度延迟webhook回调（模拟链上确认）
        delay = getattr(settings, 'MOCK_TX_COMPLETE_DELAY', 3)
        
        from apps.vesting.tasks import send_mock_fireblocks_webhook
        send_mock_fireblocks_webhook.apply_async(
            args=[tx_id],
            countdown=delay
        )
        
        logger.debug(
            f"[MockFireblocks] Webhook scheduled in {delay}s for {tx_id}"
        )
        
        return tx_id
    
    def get_transaction_status(self, tx_id: str) -> Dict:
        """
        查询交易状态（模拟）
        
        参数:
            tx_id: 交易ID
        
        返回:
            {'id': tx_id, 'status': 'COMPLETED', 'txHash': '0xmock...'}
        """
        logger.info(
            f"[MockFireblocks] Query transaction status: {tx_id}"
        )
        
        # 模拟返回COMPLETED状态
        return {
            'id': tx_id,
            'status': 'COMPLETED',
            'txHash': f"0xmock{uuid.uuid4().hex[:40]}"
        }

