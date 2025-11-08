"""
推荐链查询工具

⭐ Phase D: 环路检测防护

功能：
- 递归查询推荐链路
- 环路检测（visited set）
- 限制最大层级（防无限递归）
- 可选Redis缓存（未来优化）
"""
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from apps.users.models import User

logger = logging.getLogger(__name__)


class CircularReferralError(Exception):
    """推荐链环路异常"""
    pass


def get_referral_chain(
    user: User,
    max_levels: int = 10,
    check_circular: bool = True
) -> List[Dict]:
    """
    获取推荐链路（含环路检测）
    
    ⭐ Phase D 修正：
    - 使用 visited set 防止环路
    - 限制最大层级
    - 检测到环路时记录ERROR日志并抛出异常
    
    Args:
        user: 起始用户
        max_levels: 最大层级（默认10层，防止无限递归）
        check_circular: 是否检查环路（默认True）
    
    Returns:
        List[Dict]: 推荐链路
            [
                {'agent': User对象, 'level': 1},
                {'agent': User对象, 'level': 2},
                ...
            ]
    
    Raises:
        CircularReferralError: 检测到环路
    
    Examples:
        >>> chain = get_referral_chain(buyer_user, max_levels=2)
        >>> # [{'agent': referrer1, 'level': 1}, {'agent': referrer2, 'level': 2}]
    """
    chain = []
    visited = set() if check_circular else None
    current_user = user
    
    for level in range(1, max_levels + 1):
        # 检查是否有上级推荐人
        if not current_user.referrer:
            break
        
        # ⭐ 环路检测
        if check_circular and visited is not None:
            if current_user.referrer.user_id in visited:
                # 检测到环路！
                error_msg = (
                    f"Circular referral detected: "
                    f"user={current_user.user_id} → "
                    f"referrer={current_user.referrer.user_id} "
                    f"(already visited)"
                )
                logger.error(
                    error_msg,
                    extra={
                        'user_id': str(current_user.user_id),
                        'referrer_id': str(current_user.referrer.user_id),
                        'visited_count': len(visited),
                        'chain_length': len(chain)
                    }
                )
                raise CircularReferralError(error_msg)
            
            # 标记已访问 ⭐
            visited.add(current_user.referrer.user_id)
        
        # 添加到链路
        chain.append({
            'agent': current_user.referrer,
            'level': level,
            'user_id': current_user.referrer.user_id,
            'wallet_address': current_user.referrer.wallet_address,
            'referral_code': current_user.referrer.referral_code
        })
        
        # 移动到下一层
        current_user = current_user.referrer
    
    logger.debug(
        f"Referral chain retrieved: {len(chain)} levels",
        extra={'start_user': str(user.user_id), 'chain_length': len(chain)}
    )
    
    return chain


def get_referral_tree_stats(user: User, max_depth: int = 3) -> Dict:
    """
    获取推荐树统计（递归查询下级）
    
    ⭐ 包含环路检测
    
    Args:
        user: 代理用户
        max_depth: 最大递归深度
    
    Returns:
        Dict: 统计数据
            {
                'total_downline': int,
                'direct_referrals': int,
                'levels': {1: count, 2: count, ...}
            }
    """
    from apps.agents.services.tree_query import get_agent_downline_recursive
    
    # 使用已有的递归查询（带环路检测）
    downline = get_agent_downline_recursive(user.user_id, max_depth=max_depth)
    
    # 统计
    stats = {
        'total_downline': len(downline),
        'direct_referrals': len([d for d in downline if d['level'] == 1]),
        'levels': {}
    }
    
    # 按层级统计
    for agent in downline:
        level = agent['level']
        stats['levels'][level] = stats['levels'].get(level, 0) + 1
    
    return stats

