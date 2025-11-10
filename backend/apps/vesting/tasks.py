"""
Vesting Celery任务

⭐ Phase E 任务:
1. send_mock_fireblocks_webhook - MOCK webhook回调
2. unlock_vesting_releases - 定时解锁
3. reconcile_stuck_releases - 守护对账任务
4. update_vesting_metrics - 更新指标（v2.2.1）
"""
import uuid
import logging
import requests
from datetime import timedelta
from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from apps.vesting.metrics import update_stuck_gauge, update_unlocked_gauge  # ⭐ v2.2.1

logger = logging.getLogger(__name__)


@shared_task
def send_mock_fireblocks_webhook(tx_id: str):
    """
    发送MOCK Fireblocks webhook
    
    ⭐ 模拟链上确认延迟
    
    参数:
        tx_id: 交易ID（tx_mock_*格式）
    
    流程:
    1. 延迟N秒（模拟链上确认）
    2. 发送webhook到本地端点
    3. 状态: COMPLETED
    """
    webhook_url = getattr(
        settings,
        'MOCK_WEBHOOK_URL',
        'http://localhost:8000/api/v1/webhooks/fireblocks'
    )
    
    # 构造webhook payload
    payload = {
        'type': 'TRANSACTION_STATUS_UPDATED',
        'txId': tx_id,
        'status': 'COMPLETED',
        'txHash': f"0xmock{uuid.uuid4().hex[:40]}"
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-MOCK-WEBHOOK': 'true'  # ⭐ MOCK模式标记
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(
                f"[MOCK Webhook] Sent successfully: {tx_id}",
                extra={
                    'tx_id': tx_id,
                    'status_code': response.status_code
                }
            )
        else:
            logger.error(
                f"[MOCK Webhook] Failed: {response.status_code}",
                extra={
                    'tx_id': tx_id,
                    'status_code': response.status_code,
                    'response': response.text
                }
            )
    
    except Exception as e:
        logger.error(
            f"[MOCK Webhook] Error: {e}",
            extra={'tx_id': tx_id},
            exc_info=True
        )


@shared_task
def unlock_vesting_releases():
    """
    定时解锁Vesting releases
    
    ⭐ 调度: 每天0点运行
    
    流程:
    1. 查询 release_date <= 今天 且 status=locked
    2. 更新状态为 unlocked
    3. 记录 unlocked_at 时间戳
    
    返回:
        解锁数量
    """
    from apps.vesting.models import VestingRelease
    
    today = timezone.now().date()
    
    # 查询需要解锁的release
    locked_releases = VestingRelease.objects.filter(
        status=VestingRelease.STATUS_LOCKED,
        release_date__lte=today
    )
    
    count = locked_releases.count()
    
    if count == 0:
        logger.info("[UnlockVesting] No releases to unlock")
        return 0
    
    # 批量更新状态
    updated = locked_releases.update(
        status=VestingRelease.STATUS_UNLOCKED,
        unlocked_at=timezone.now()
    )
    
    logger.info(
        f"[UnlockVesting] Unlocked {updated} releases",
        extra={
            'count': updated,
            'date': str(today)
        }
    )
    
    # ⭐ v2.2.1: 更新待发放指标
    update_unlocked_gauge()
    
    return updated


@shared_task
def reconcile_stuck_releases():
    """
    守护任务：对账卡在processing的release
    
    ⭐ 调度: 每5分钟运行
    
    场景:
    - Webhook丢失
    - Fireblocks状态更新延迟
    - 网络问题
    
    策略:
    1. 查询processing且超过15分钟的release
    2. 调用Fireblocks API查询真实状态
    3. 根据结果更新状态或告警
    
    返回:
        {'reconciled': 对账成功数, 'failed': 失败数}
    """
    from apps.vesting.models import VestingRelease
    from apps.vesting.services.client_factory import get_fireblocks_client
    from apps.vesting.services.batch_release_service import (
        handle_release_completed,
        handle_release_failed
    )
    
    # 1. 查询卡住的release（超过15分钟）
    stuck_threshold = timezone.now() - timedelta(minutes=15)
    
    stuck_releases = VestingRelease.objects.filter(
        status=VestingRelease.STATUS_PROCESSING,
        updated_at__lt=stuck_threshold
    ).select_related('schedule__allocation')
    
    count = stuck_releases.count()
    
    if count == 0:
        return {'reconciled': 0, 'failed': 0}
    
    logger.warning(
        f"[Reconcile] Found {count} stuck releases",
        extra={'count': count}
    )
    
    # 2. 逐个对账
    mode = getattr(settings, 'FIREBLOCKS_MODE', 'MOCK')
    
    # MOCK模式：直接标记完成
    if mode == 'MOCK':
        reconciled = 0
        for release in stuck_releases:
            try:
                handle_release_completed(
                    str(release.release_id),
                    f"0xmock{uuid.uuid4().hex[:40]}"
                )
                reconciled += 1
            except Exception as e:
                logger.error(
                    f"[Reconcile] MOCK failed: {e}",
                    extra={'release_id': str(release.release_id)},
                    exc_info=True
                )
        
        logger.info(
            f"[Reconcile] MOCK mode completed: {reconciled}/{count}"
        )
        return {'reconciled': reconciled, 'failed': count - reconciled}
    
    # LIVE模式：查询Fireblocks真实状态
    client = get_fireblocks_client()
    reconciled = 0
    failed = 0
    
    for release in stuck_releases:
        try:
            # 查询Fireblocks真实状态
            tx_status = client.get_transaction_status(
                release.fireblocks_tx_id
            )
            
            # 模拟webhook回调处理
            status = tx_status['status']
            
            if status == 'COMPLETED':
                handle_release_completed(
                    str(release.release_id),
                    tx_status.get('txHash')
                )
                reconciled += 1
                
                logger.info(
                    f"[Reconcile] Release reconciled: {release.release_id}",
                    extra={
                        'release_id': str(release.release_id),
                        'fb_status': status
                    }
                )
            
            elif status in ['FAILED', 'CANCELLED']:
                handle_release_failed(
                    str(release.release_id),
                    tx_status.get('subStatus', status)
                )
                reconciled += 1
                
                logger.warning(
                    f"[Reconcile] Release failed: {release.release_id}",
                    extra={
                        'release_id': str(release.release_id),
                        'fb_status': status
                    }
                )
            
            else:
                # 仍在处理中，跳过
                logger.debug(
                    f"[Reconcile] Still processing: {release.release_id}",
                    extra={
                        'release_id': str(release.release_id),
                        'fb_status': status
                    }
                )
        
        except Exception as e:
            failed += 1
            logger.error(
                f"[Reconcile] Failed: {e}",
                extra={'release_id': str(release.release_id)},
                exc_info=True
            )
            
            # 超过1小时仍失败 → Sentry告警
            if release.updated_at < timezone.now() - timedelta(hours=1):
                from sentry_sdk import capture_message
                capture_message(
                    f"Release stuck >1h: {release.release_id}",
                    level='error'
                )
    
    logger.info(
        f"[Reconcile] Completed: reconciled={reconciled}, failed={failed}"
    )
    
    # ⭐ v2.2.1: 更新堆积指标
    update_stuck_gauge()
    
    return {'reconciled': reconciled, 'failed': failed}


@shared_task
def cleanup_old_idempotency_keys():
    """
    清理旧的幂等键
    
    ⭐ 调度: 每天2点运行
    
    策略:
    - 删除 48小时前的记录
    """
    from apps.webhooks.models import IdempotencyKey
    
    threshold = timezone.now() - timedelta(hours=48)
    
    deleted_count, _ = IdempotencyKey.objects.filter(
        processed_at__lt=threshold
    ).delete()
    
    logger.info(
        f"[Cleanup] Deleted {deleted_count} old idempotency keys",
        extra={'deleted_count': deleted_count}
    )
    
    return deleted_count

