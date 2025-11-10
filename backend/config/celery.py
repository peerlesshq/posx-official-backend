"""
Celery Configuration for POSX
核心检查点 #4: Celery autodiscover_tasks ⭐
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

# Create Celery app
app = Celery('posx')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# ⭐ Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# ============================================
# Celery Beat Schedule（定时任务）
# ⭐ Phase D: 统一使用 beat_schedule，不使用 @periodic_task
# ============================================
app.conf.beat_schedule = {
    # 超时订单自动取消（每5分钟运行一次）
    'expire-pending-orders': {
        'task': 'apps.orders.tasks.expire_pending_orders',
        'schedule': crontab(minute='*/5'),  # 每5分钟
    },
    # Phase D: 释放锁定佣金（每小时整点运行）
    'release-held-commissions': {
        'task': 'apps.commissions.tasks.release_held_commissions',
        'schedule': crontab(minute=0),  # 每小时整点
    },
    # Phase D: 清理过期幂等键（每天凌晨3点运行）
    'cleanup-idempotency-keys': {
        'task': 'apps.webhooks.tasks.cleanup_old_idempotency_keys',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点
    },
    # Phase F: 生成月度对账单（每月1号凌晨2点运行）
    'generate-monthly-statements': {
        'task': 'apps.agents.tasks.generate_monthly_statements',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),  # 每月1号凌晨2点
    },
    # Phase F: 更新 Agent 统计（每小时运行）
    'update-agent-stats': {
        'task': 'apps.agents.tasks.update_agent_stats',
        'schedule': crontab(minute=30),  # 每小时30分
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')
