"""
Fireblocks签名验证工具
"""
import base64
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


def verify_fireblocks_signature(
    payload: bytes,
    signature: str,
    public_key_pem: str
) -> bool:
    """
    验证Fireblocks RSA-SHA512签名
    
    参数:
        payload: 原始请求体
        signature: Base64编码的签名（X-Fireblocks-Signature头）
        public_key_pem: PEM格式的公钥
    
    返回:
        bool: 签名是否有效
    """
    try:
        # 1. 解码签名
        signature_bytes = base64.b64decode(signature)
        
        # 2. 加载公钥
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # 3. 验证签名
        public_key.verify(
            signature_bytes,
            payload,
            padding.PKCS1v15(),
            hashes.SHA512()
        )
        
        return True
        
    except Exception as e:
        logger.warning(
            f"[Fireblocks] Signature verification failed: {e}",
            exc_info=True
        )
        return False

