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
# ============================================
app.conf.beat_schedule = {
    # 超时订单自动取消（每5分钟运行一次）
    'expire-pending-orders': {
        'task': 'apps.orders.tasks.expire_pending_orders',
        'schedule': crontab(minute='*/5'),  # 每5分钟
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')
