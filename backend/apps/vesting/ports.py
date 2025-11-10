"""
代币发放端口（Port）
定义统一接口，支持多种实现
"""
from typing import Protocol
from decimal import Decimal


class TokenPayoutPort(Protocol):
    """
    代币发放接口
    
    实现:
    - MockFireblocksClient（模拟）
    - FireblocksClient（真实）
    """
    
    def create_transaction(
        self,
        to_address: str,
        amount: Decimal,
        note: str = ''
    ) -> str:
        """
        创建转账交易
        
        返回:
            交易ID（MOCK: tx_mock_*, LIVE: fireblocks-tx-id）
        """
        ...
    
    def get_transaction_status(self, tx_id: str) -> dict:
        """
        查询交易状态
        
        返回:
            {'id': '...', 'status': 'COMPLETED', 'txHash': '0x...'}
        """
        ...

