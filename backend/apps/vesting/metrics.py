"""
Vesting可观测性指标

⭐ v2.2.1: Prometheus指标埋点
用于 Grafana/Retool 仪表板监控
"""
from prometheus_client import Counter, Gauge, Histogram


# ========== 批量发放指标 ==========

vesting_batch_submitted_total = Counter(
    'vesting_batch_submitted_total',
    'Total vesting releases submitted to Fireblocks',
    ['mode', 'site_id']  # mode=MOCK|LIVE, site_id=站点UUID
)

vesting_batch_failed_total = Counter(
    'vesting_batch_failed_total',
    'Total vesting releases failed',
    ['mode', 'site_id', 'error_type']  # error_type=异常类型
)


# ========== Webhook指标 ==========

vesting_webhook_received_total = Counter(
    'vesting_webhook_received_total',
    'Total Fireblocks webhooks received',
    ['event_type', 'status']  # event_type=TRANSACTION_STATUS_UPDATED, status=COMPLETED|FAILED
)

vesting_webhook_completed_total = Counter(
    'vesting_webhook_completed_total',
    'Total webhooks completed successfully',
    ['status']  # status=COMPLETED|FAILED|CANCELLED
)

vesting_webhook_duplicate_total = Counter(
    'vesting_webhook_duplicate_total',
    'Total duplicate webhook events (idempotent skip)',
    []
)


# ========== Processing堆积指标 ==========

vesting_processing_stuck_gauge = Gauge(
    'vesting_processing_stuck_gauge',
    'Number of releases stuck in processing status >15min'
)

vesting_unlocked_pending_gauge = Gauge(
    'vesting_unlocked_pending_gauge',
    'Number of unlocked releases pending for batch release'
)


# ========== Fireblocks API指标 ==========

fireblocks_api_duration_seconds = Histogram(
    'fireblocks_api_duration_seconds',
    'Fireblocks API call duration in seconds',
    ['endpoint', 'status'],  # endpoint=create_transaction, status=success|failed
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

fireblocks_api_retry_total = Counter(
    'fireblocks_api_retry_total',
    'Total Fireblocks API retries',
    ['status_code', 'attempt']  # status_code=429|500, attempt=1|2|3
)


# ========== 业务指标 ==========

vesting_tokens_released_total = Counter(
    'vesting_tokens_released_total',
    'Total tokens released (human-readable amount)',
    ['site_id', 'token_symbol']
)

vesting_schedule_created_total = Counter(
    'vesting_schedule_created_total',
    'Total vesting schedules created',
    ['site_id', 'policy_name']
)


# ========== 辅助函数 ==========

def update_stuck_gauge():
    """
    更新 processing 堆积指标
    
    应在守护任务中定期调用
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.vesting.models import VestingRelease
    
    stuck_threshold = timezone.now() - timedelta(minutes=15)
    stuck_count = VestingRelease.objects.filter(
        status=VestingRelease.STATUS_PROCESSING,
        updated_at__lt=stuck_threshold
    ).count()
    
    vesting_processing_stuck_gauge.set(stuck_count)


def update_unlocked_gauge():
    """
    更新 unlocked 待发放指标
    
    应在定时任务中定期调用
    """
    from apps.vesting.models import VestingRelease
    
    unlocked_count = VestingRelease.objects.filter(
        status=VestingRelease.STATUS_UNLOCKED
    ).count()
    
    vesting_unlocked_pending_gauge.set(unlocked_count)

