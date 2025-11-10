"""
多链地址校验工具
支持:
- EVM (Ethereum/Polygon/BSC): EIP-55 Checksum
- TRON: Base58Check
"""
from web3 import Web3
import base58
import hashlib


def validate_and_format_address(address: str, chain: str) -> str:
    """
    验证并格式化地址
    
    参数:
        address: 原始地址
        chain: ETH | POLYGON | BSC | TRON
    
    返回:
        格式化后的地址（EVM: checksum, TRON: 原样）
    
    异常:
        ValueError: 地址格式错误
    """
    if chain in ['ETH', 'POLYGON', 'BSC']:
        return _validate_evm_address(address)
    elif chain == 'TRON':
        return _validate_tron_address(address)
    else:
        raise ValueError(f"Unsupported chain: {chain}")


def _validate_evm_address(address: str) -> str:
    """
    验证EVM地址（EIP-55）
    
    返回: Checksum地址
    """
    if not Web3.is_address(address):
        raise ValueError(f"Invalid EVM address: {address}")
    
    return Web3.to_checksum_address(address)


def _validate_tron_address(address: str) -> str:
    """
    验证TRON地址（Base58Check）
    
    TRON地址格式:
    - 以T开头（主网）或以27开头（测试网）
    - 34字符长度
    - Base58编码
    
    返回: 原地址（TRON不需要checksum转换）
    """
    # 1. 长度检查
    if len(address) != 34:
        raise ValueError(f"Invalid TRON address length: {address}")
    
    # 2. 前缀检查
    if not (address.startswith('T') or address.startswith('27')):
        raise ValueError(f"Invalid TRON address prefix: {address}")
    
    # 3. Base58解码校验
    try:
        decoded = base58.b58decode(address)
        
        # TRON地址 = 21字节地址 + 4字节校验和
        if len(decoded) != 25:
            raise ValueError("Invalid TRON address decoded length")
        
        # 分离地址和校验和
        addr_bytes = decoded[:21]
        checksum = decoded[21:]
        
        # 计算校验和
        hash_result = hashlib.sha256(
            hashlib.sha256(addr_bytes).digest()
        ).digest()
        
        if hash_result[:4] != checksum:
            raise ValueError("TRON address checksum failed")
        
        return address
        
    except Exception as e:
        raise ValueError(f"Invalid TRON address: {e}")


# 测试用例
def test_address_validation():
    """测试地址校验功能"""
    # EVM测试
    evm_addr = "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
    result = validate_and_format_address(evm_addr, 'ETH')
    assert result == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    print(f"✅ EVM validation passed: {result}")
    
    # TRON测试（主网地址）
    tron_addr = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"
    result = validate_and_format_address(tron_addr, 'TRON')
    assert result == tron_addr
    print(f"✅ TRON validation passed: {result}")
    
    # 错误地址测试
    try:
        validate_and_format_address("invalid", 'ETH')
        assert False, "Should raise error"
    except ValueError:
        print("✅ Invalid address detection passed")

