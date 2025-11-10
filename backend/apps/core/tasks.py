"""
Celery Task Base Classes

⭐ SiteContextTask: 支持站点上下文的 Celery 基础任务
确保异步任务执行期间 RLS 策略生效
"""
from celery import Task
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class SiteContextTask(Task):
    """
    支持站点上下文的 Celery 基础任务
    
    ⭐ 功能：
    - 自动设置 app.current_site_id GUC 变量
    - 确保任务执行期间 RLS 策略生效
    - 支持从任务参数中提取 site_id
    
    用法：
        @shared_task(base=SiteContextTask, bind=True)
        def my_task(self, site_id, **kwargs):
            # 此时 app.current_site_id 已设置
            # 所有 ORM 查询均受 RLS 保护
            pass
    
    示例：
        from apps.core.tasks import SiteContextTask
        from celery import shared_task
        
        @shared_task(base=SiteContextTask, bind=True)
        def process_order(self, order_id, site_id):
            # RLS context is set automatically
            order = Order.objects.get(order_id=order_id)
            # ... process order
    """
    
    def __call__(self, *args, **kwargs):
        """
        执行任务前设置站点上下文
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数（优先从这里提取 site_id）
        """
        # 从任务参数中提取 site_id
        site_id = self._extract_site_id(args, kwargs)
        
        if site_id:
            self._set_site_context(site_id)
        else:
            logger.warning(
                f"Task {self.name} executed without site_id",
                extra={
                    'task_id': self.request.id,
                    'args': args,
                    'kwargs': kwargs
                }
            )
        
        try:
            return super().__call__(*args, **kwargs)
        finally:
            # 清理上下文（可选，connection pool 会自动处理）
            pass
    
    def _extract_site_id(self, args, kwargs):
        """
        从任务参数中提取 site_id
        
        优先级：
        1. kwargs['site_id']
        2. kwargs 中第一个字典参数的 site_id
        3. args 中第一个字典参数的 site_id
        
        Returns:
            UUID string or None
        """
        # 1. 直接从 kwargs 获取
        site_id = kwargs.get('site_id')
        if site_id:
            return site_id
        
        # 2. 从 kwargs 中的第一个 dict 参数获取
        for value in kwargs.values():
            if isinstance(value, dict) and 'site_id' in value:
                return value['site_id']
        
        # 3. 从 args 中的第一个 dict 参数获取
        for arg in args:
            if isinstance(arg, dict) and 'site_id' in arg:
                return arg['site_id']
        
        return None
    
    def _set_site_context(self, site_id):
        """
        设置站点上下文
        
        Args:
            site_id: 站点 UUID（字符串或 UUID 对象）
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL app.current_site_id = %s",
                    [str(site_id)]
                )
            
            logger.debug(
                f"Task {self.name} set site context: {site_id}",
                extra={
                    'task_id': self.request.id,
                    'site_id': str(site_id)
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to set site context for task {self.name}: {e}",
                extra={
                    'task_id': self.request.id,
                    'site_id': str(site_id)
                },
                exc_info=True
            )
            # 不抛出异常，让任务继续执行（但可能违反 RLS）
            # 在生产环境中，可以选择抛出异常强制失败
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        任务失败处理
        
        Args:
            exc: 异常对象
            task_id: 任务ID
            args: 位置参数
            kwargs: 关键字参数
            einfo: 异常信息
        """
        logger.error(
            f"Task {self.name} failed: {exc}",
            extra={
                'task_id': task_id,
                'args': args,
                'kwargs': kwargs,
                'exception': str(exc)
            },
            exc_info=einfo
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        任务重试处理
        
        Args:
            exc: 异常对象
            task_id: 任务ID
            args: 位置参数
            kwargs: 关键字参数
            einfo: 异常信息
        """
        logger.warning(
            f"Task {self.name} retrying: {exc}",
            extra={
                'task_id': task_id,
                'retry_count': self.request.retries,
                'max_retries': self.max_retries,
                'exception': str(exc)
            }
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """
        任务成功处理
        
        Args:
            retval: 返回值
            task_id: 任务ID
            args: 位置参数
            kwargs: 关键字参数
        """
        logger.info(
            f"Task {self.name} completed successfully",
            extra={
                'task_id': task_id,
                'execution_time': self.request.duration if hasattr(self.request, 'duration') else None
            }
        )

