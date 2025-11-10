"""
Fireblocks真实客户端
生产环境使用，需要真实凭证
"""
import time
import json
import logging
import hashlib
import uuid
import threading
from decimal import Decimal
from typing import Dict
import requests
from requests.exceptions import HTTPError
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)


class FireblocksClient:
    """
    Fireblocks真实客户端
    
    特性:
    - JWT签名认证
    - 429/5xx重试机制
    - 指数退避策略
    - ⭐ v2.2.2: API 速率保护（10 req/sec）
    """
    
    MAX_RETRIES = 3
    RETRY_DELAYS = [0.5, 1.0, 2.0]  # 指数退避
    
    # ⭐ v2.2.2: API 速率限制（防止批量100笔被429拒绝）
    _rate_lock = threading.Lock()
    _last_call_time = 0
    _min_interval = 0.12  # 120ms 最小间隔（约 8 req/sec，留余量）
    
    def __init__(self):
        self.api_key = settings.FIREBLOCKS_API_KEY
        self.private_key = settings.FIREBLOCKS_PRIVATE_KEY
        self.base_url = settings.FIREBLOCKS_BASE_URL
        self.vault_id = settings.FIREBLOCKS_VAULT_ACCOUNT_ID
        self.asset_id = settings.FIREBLOCKS_ASSET_ID
        
        # 验证配置
        if not self.api_key or not self.private_key:
            raise ValueError(
                "Fireblocks credentials not configured. "
                "Set FIREBLOCKS_API_KEY and FIREBLOCKS_PRIVATE_KEY."
            )
        
        self.mode = 'LIVE'
        logger.info("[Fireblocks] Initialized LIVE client")
    
    def create_transaction(
        self,
        to_address: str,
        amount: Decimal,
        note: str = ''
    ) -> str:
        """
        创建交易（带重试 + 速率保护）
        
        ⭐ v2.2.2: 速率保护
        - 最小间隔 120ms（约 8 req/sec）
        - 防止批量100笔被429拒绝
        
        重试策略:
        - 429 (Rate Limit): 重试3次
        - 5xx (Server Error): 重试3次
        - 4xx (Client Error): 不重试
        
        参数:
            to_address: 接收地址
            amount: 代币数量
            note: 备注
        
        返回:
            Fireblocks交易ID
        """
        # ⭐ v2.2.2: 速率保护
        self._enforce_rate_limit()
        
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return self._create_transaction_once(to_address, amount, note)
                
            except HTTPError as e:
                status_code = e.response.status_code
                
                # 429 或 5xx: 可重试
                if status_code == 429 or status_code >= 500:
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAYS[attempt]
                        logger.warning(
                            f"[Fireblocks] HTTP {status_code}, "
                            f"retry in {delay}s (attempt {attempt+1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(delay)
                        last_error = e
                        continue
                
                # 4xx: 不重试
                logger.error(f"[Fireblocks] HTTP {status_code}, no retry")
                raise
        
        # 重试耗尽
        raise Exception(
            f"Fireblocks API failed after {self.MAX_RETRIES} retries"
        ) from last_error
    
    def _create_transaction_once(
        self,
        to_address: str,
        amount: Decimal,
        note: str
    ) -> str:
        """单次API调用"""
        path = '/v1/transactions'
        
        # 构造请求体
        payload = {
            'assetId': self.asset_id,
            'source': {
                'type': 'VAULT_ACCOUNT',
                'id': self.vault_id
            },
            'destination': {
                'type': 'ONE_TIME_ADDRESS',
                'oneTimeAddress': {
                    'address': to_address
                }
            },
            'amount': str(amount),
            'note': note or f'Vesting release {uuid.uuid4().hex[:8]}'
        }
        
        # 发送请求
        response = self._request('POST', path, payload)
        
        tx_id = response.get('id')
        
        logger.info(
            f"[Fireblocks] Transaction created: {tx_id}",
            extra={
                'tx_id': tx_id,
                'to_address': to_address,
                'amount': str(amount)
            }
        )
        
        return tx_id
    
    def get_transaction_status(self, tx_id: str) -> Dict:
        """
        查询交易状态
        
        参数:
            tx_id: 交易ID
        
        返回:
            {'id': tx_id, 'status': 'COMPLETED', 'txHash': '0x...'}
        """
        path = f'/v1/transactions/{tx_id}'
        
        response = self._request('GET', path)
        
        return {
            'id': response.get('id'),
            'status': response.get('status'),
            'txHash': response.get('txHash')
        }
    
    def _request(self, method: str, path: str, body: dict = None) -> dict:
        """
        发送HTTP请求（含JWT签名）
        
        参数:
            method: HTTP方法
            path: API路径
            body: 请求体
        
        返回:
            响应JSON
        """
        url = f"{self.base_url}{path}"
        
        # 生成JWT token
        token = self._generate_jwt(path, body)
        
        headers = {
            'X-API-Key': self.api_key,
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 发送请求
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )
        
        response.raise_for_status()
        
        return response.json()
    
    def _enforce_rate_limit(self):
        """
        ⭐ v2.2.2: 强制速率限制
        
        防止批量100笔瞬间发送触发429
        Fireblocks 默认 ~10 req/sec，我们限制到 8 req/sec
        """
        with self._rate_lock:
            current_time = time.time()
            elapsed = current_time - FireblocksClient._last_call_time
            
            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                logger.debug(
                    f"[Fireblocks] Rate limit sleep: {sleep_time:.3f}s"
                )
                time.sleep(sleep_time)
            
            FireblocksClient._last_call_time = time.time()
    
    def _generate_jwt(self, path: str, body: dict = None) -> str:
        """
        生成JWT token
        
        Fireblocks要求:
        - 算法: RS256
        - Payload: path, bodyHash, timestamp, nonce
        - 过期时间: 30秒
        """
        now = int(time.time())
        
        # 计算body hash
        body_hash = ''
        if body:
            body_json = json.dumps(body, separators=(',', ':'))
            body_hash = hashlib.sha256(body_json.encode()).hexdigest()
        
        # 构造payload
        payload = {
            'uri': path,
            'nonce': uuid.uuid4().hex,
            'iat': now,
            'exp': now + 30,
            'sub': self.api_key,
            'bodyHash': body_hash
        }
        
        # 签名
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm='RS256'
        )
        
        return token

