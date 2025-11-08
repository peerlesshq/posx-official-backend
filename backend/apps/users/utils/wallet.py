"""
钱包地址工具

⭐ EIP-55 混合大小写校验和
- 提高地址可读性
- 防止输入错误
- 标准化存储格式（lowercase）

使用示例：
>>> addr = '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B'
>>> normalize_address(addr)  # '0xab5801a7d398351b8be11c439e05c5b3259aec9b'
>>> validate_address(addr)  # True
"""
import re
from typing import Optional
from eth_utils import is_address, to_checksum_address


def normalize_address(address: str) -> str:
    """
    标准化钱包地址（lowercase）
    
    ⚠️ 数据库统一存储 lowercase 格式
    
    Args:
        address: 钱包地址（支持 0x 前缀或无前缀）
    
    Returns:
        str: lowercase 地址（带 0x 前缀）
    
    Raises:
        ValueError: 地址格式非法
    
    Examples:
        >>> normalize_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B')
        '0xab5801a7d398351b8be11c439e05c5b3259aec9b'
        
        >>> normalize_address('Ab5801a7D398351b8bE11C439e05C5B3259aeC9B')
        '0xab5801a7d398351b8be11c439e05c5b3259aec9b'
    """
    if not address:
        raise ValueError("地址不能为空")
    
    # 移除空格
    address = address.strip()
    
    # 添加 0x 前缀（如果缺失）
    if not address.startswith('0x'):
        address = f'0x{address}'
    
    # 验证格式
    if not is_address(address):
        raise ValueError(f"无效的以太坊地址: {address}")
    
    # 转换为 lowercase
    return address.lower()


def validate_address(address: str) -> bool:
    """
    验证钱包地址（EIP-55 校验和）
    
    ⚠️ 支持：
    - lowercase 地址（始终有效）
    - uppercase 地址（始终有效）
    - 混合大小写地址（EIP-55 校验和）
    
    Args:
        address: 钱包地址
    
    Returns:
        bool: True=有效, False=无效
    
    Examples:
        >>> validate_address('0xab5801a7d398351b8be11c439e05c5b3259aec9b')  # lowercase
        True
        
        >>> validate_address('0xAB5801A7D398351B8BE11C439E05C5B3259AEC9B')  # uppercase
        True
        
        >>> validate_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B')  # EIP-55
        True
        
        >>> validate_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9b')  # 错误校验和
        False
    """
    if not address:
        return False
    
    address = address.strip()
    
    # 添加 0x 前缀（如果缺失）
    if not address.startswith('0x'):
        address = f'0x{address}'
    
    # 基本格式验证
    if not is_address(address):
        return False
    
    # 如果是全 lowercase 或全 uppercase，视为有效
    if address == address.lower() or address == address.upper():
        return True
    
    # 混合大小写：验证 EIP-55 校验和
    try:
        checksum_address = to_checksum_address(address)
        return address == checksum_address
    except Exception:
        return False


def to_checksum(address: str) -> str:
    """
    转换为 EIP-55 校验和地址
    
    Args:
        address: 钱包地址
    
    Returns:
        str: EIP-55 校验和地址
    
    Raises:
        ValueError: 地址格式非法
    
    Examples:
        >>> to_checksum('0xab5801a7d398351b8be11c439e05c5b3259aec9b')
        '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B'
    """
    if not address:
        raise ValueError("地址不能为空")
    
    address = address.strip()
    
    if not address.startswith('0x'):
        address = f'0x{address}'
    
    if not is_address(address):
        raise ValueError(f"无效的以太坊地址: {address}")
    
    return to_checksum_address(address)


def is_valid_hex_address(address: str) -> bool:
    """
    验证是否为有效的十六进制地址格式
    
    Args:
        address: 地址字符串
    
    Returns:
        bool: True=格式有效, False=格式无效
    
    Examples:
        >>> is_valid_hex_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B')
        True
        
        >>> is_valid_hex_address('0xGGGGG')  # 非十六进制
        False
    """
    if not address:
        return False
    
    address = address.strip()
    
    # 检查格式：0x + 40个十六进制字符
    pattern = r'^0x[0-9a-fA-F]{40}$'
    return bool(re.match(pattern, address))


def get_short_address(address: str, start: int = 6, end: int = 4) -> str:
    """
    获取缩短的地址显示
    
    Args:
        address: 完整地址
        start: 保留前面字符数（不含0x）
        end: 保留后面字符数
    
    Returns:
        str: 缩短的地址
    
    Examples:
        >>> get_short_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B')
        '0xAb5801...eC9B'
        
        >>> get_short_address('0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B', 4, 4)
        '0xAb58...eC9B'
    """
    if not address or len(address) < (start + end + 2):
        return address
    
    return f"{address[:2+start]}...{address[-end:]}"


