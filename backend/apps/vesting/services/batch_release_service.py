"""
批量发放服务
处理Vesting代币的批量链上发放
"""
import logging
from decimal import Decimal
from typing import List, Dict
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.vesting.models import VestingRelease
from apps.vesting.services.client_factory import get_fireblocks_client
from apps.allocations.models import Allocation
from apps.vesting.metrics import (  # ⭐ v2.2.1
    vesting_batch_submitted_total,
    vesting_batch_failed_total
)

logger = logging.getLogger(__name__)


def batch_release_vesting(
    release_ids: List[str],
    operator_user,
    site_id: str
) -> Dict:
    """
    批量发放代币
    
    ⭐ Phase E 核心功能
    
    参数:
        release_ids: Release ID列表（最多100）
        operator_user: 操作员
        site_id: 站点ID（强制站点隔离）
    
    返回:
        {
            'submitted': 提交成功数量,
            'failed': 失败数量,
            'skipped': 跳过数量,
            'total_amount': 总金额
        }
    
    流程:
    1. 查询unlocked状态的release（站点隔离）
    2. 调用Fireblocks API发放
    3. 更新状态为processing
    4. 等待webhook回调更新为released
    """
    # 1. 前置检查
    if len(release_ids) > 100:
        raise ValueError("批量发放最多100条/次")
    
    # 2. 查询release（⭐ 站点隔离 + 行锁）
    releases = VestingRelease.objects.filter(
        release_id__in=release_ids,
        status=VestingRelease.STATUS_UNLOCKED,
        schedule__allocation__order__site_id=site_id  # ⭐ 站点隔离
    ).select_related(
        'schedule__allocation__order__site',
        'schedule__user'
    ).select_for_update()
    
    if not releases.exists():
        return {
            'submitted': 0,
            'failed': 0,
            'skipped': len(release_ids),
            'total_amount': Decimal('0')
        }
    
    # 二次检查：确保所有release属于同一站点
    site_ids = set(r.schedule.allocation.order.site_id for r in releases)
    if len(site_ids) > 1:
        raise Exception(f"跨站点操作检测: {site_ids}")
    
    # 3. LIVE模式双保险检查
    mode = getattr(settings, 'FIREBLOCKS_MODE', 'MOCK')
    allow_prod = getattr(settings, 'ALLOW_PROD_TX', False)
    
    if mode == 'LIVE' and not allow_prod:
        raise Exception(
            "LIVE模式未授权。请设置 ALLOW_PROD_TX=1"
        )
    
    # 4. 获取客户端
    client = get_fireblocks_client()
    
    # 5. 批量发放
    results = {
        'submitted': 0,
        'failed': 0,
        'skipped': 0,
        'total_amount': Decimal('0')
    }
    
    for release in releases:
        try:
            # 获取allocation和钱包地址
            allocation = release.schedule.allocation
            wallet_address = allocation.wallet_address
            order = allocation.order
            
            # ⭐ v2.2.1: 查询资产配置获取精度
            from apps.sites.models import ChainAssetConfig
            
            try:
                asset_config = ChainAssetConfig.objects.get(
                    site=order.site,
                    chain='ETH',  # TODO: 从订单读取实际链
                    token_symbol='POSX',  # TODO: 从订单读取实际代币
                    is_active=True
                )
                
                # 人类可读金额 → 链上最小单位
                # 例如：100.000000 POSX * 10^18 = 100000000000000000000
                chain_amount = release.amount * (Decimal('10') ** asset_config.token_decimals)
                
                logger.debug(
                    f"[BatchRelease] Amount conversion: "
                    f"{release.amount} → {chain_amount} (decimals={asset_config.token_decimals})"
                )
                
            except ChainAssetConfig.DoesNotExist:
                logger.warning(
                    f"[BatchRelease] ChainAssetConfig not found for site {order.site_id}, "
                    f"using amount as-is"
                )
                chain_amount = release.amount
            
            # 调用Fireblocks API（使用链上单位）
            tx_id = client.create_transaction(
                to_address=wallet_address,
                amount=chain_amount,  # ⭐ 已转换为链上最小单位
                note=f"Vesting P{release.period_no} for order {allocation.order_id}"
            )
            
            # 更新状态为processing
            with transaction.atomic():
                release.status = VestingRelease.STATUS_PROCESSING
                release.fireblocks_tx_id = tx_id
                release.chain_amount = chain_amount  # ⭐ 保存链上金额
                release.save()
            
            results['submitted'] += 1
            results['total_amount'] += release.amount
            
            # ⭐ v2.2.1: 指标埋点
            vesting_batch_submitted_total.labels(
                mode=mode,
                site_id=str(order.site_id)
            ).inc()
            
            logger.info(
                f"[BatchRelease] Submitted: {tx_id}",
                extra={
                    'release_id': str(release.release_id),
                    'tx_id': tx_id,
                    'amount': str(release.amount),
                    'mode': mode
                }
            )
            
        except Exception as e:
            results['failed'] += 1
            
            # ⭐ v2.2.1: 指标埋点
            vesting_batch_failed_total.labels(
                mode=mode,
                site_id=str(release.schedule.allocation.order.site_id),
                error_type=type(e).__name__
            ).inc()
            
            logger.error(
                f"[BatchRelease] Failed: {e}",
                extra={
                    'release_id': str(release.release_id),
                    'error': str(e)
                },
                exc_info=True
            )
    
    logger.info(
        f"[BatchRelease] Completed",
        extra={
            'submitted': results['submitted'],
            'failed': results['failed'],
            'total_amount': str(results['total_amount'])
        }
    )
    
    return results


def handle_release_completed(release_id: str, tx_hash: str) -> None:
    """
    处理release完成（webhook回调）
    
    参数:
        release_id: Release ID
        tx_hash: 链上交易哈希
    
    流程:
    1. 更新release状态为released
    2. 累加allocation.released_tokens
    3. 检查是否所有release都已完成
    """
    try:
        with transaction.atomic():
            # 查询release（行锁）
            release = VestingRelease.objects.select_for_update().get(
                release_id=release_id
            )
            
            # 状态检查（防重复）
            if release.status != VestingRelease.STATUS_PROCESSING:
                logger.warning(
                    f"[ReleaseComplete] Invalid status: {release.status}",
                    extra={'release_id': release_id}
                )
                return
            
            # 更新release状态
            release.status = VestingRelease.STATUS_RELEASED
            release.tx_hash = tx_hash
            release.released_at = timezone.now()
            release.save()
            
            # 累加allocation.released_tokens
            allocation = release.schedule.allocation
            allocation.released_tokens += release.amount
            
            # 检查是否全部完成
            total_tokens = allocation.token_amount
            if allocation.released_tokens >= total_tokens:
                allocation.status = Allocation.STATUS_COMPLETED
            
            allocation.save()
            
            logger.info(
                f"[ReleaseComplete] Success",
                extra={
                    'release_id': release_id,
                    'tx_hash': tx_hash,
                    'released_amount': str(release.amount),
                    'total_released': str(allocation.released_tokens),
                    'total_tokens': str(total_tokens)
                }
            )
            
    except VestingRelease.DoesNotExist:
        logger.error(
            f"[ReleaseComplete] Release not found: {release_id}"
        )
    except Exception as e:
        logger.error(
            f"[ReleaseComplete] Error: {e}",
            extra={'release_id': release_id},
            exc_info=True
        )
        raise


def handle_release_failed(release_id: str, reason: str) -> None:
    """
    处理release失败（webhook回调）
    
    参数:
        release_id: Release ID
        reason: 失败原因
    
    流程:
    1. 回滚release状态为unlocked
    2. 记录失败原因
    """
    try:
        with transaction.atomic():
            release = VestingRelease.objects.select_for_update().get(
                release_id=release_id
            )
            
            if release.status != VestingRelease.STATUS_PROCESSING:
                logger.warning(
                    f"[ReleaseFailed] Invalid status: {release.status}",
                    extra={'release_id': release_id}
                )
                return
            
            # 回滚状态
            release.status = VestingRelease.STATUS_UNLOCKED
            release.fireblocks_tx_id = None
            release.chain_amount = None
            release.save()
            
            logger.warning(
                f"[ReleaseFailed] Release rolled back",
                extra={
                    'release_id': release_id,
                    'reason': reason
                }
            )
            
    except VestingRelease.DoesNotExist:
        logger.error(
            f"[ReleaseFailed] Release not found: {release_id}"
        )
    except Exception as e:
        logger.error(
            f"[ReleaseFailed] Error: {e}",
            extra={'release_id': release_id},
            exc_info=True
        )
        raise

