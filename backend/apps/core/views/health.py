"""
Health Check Views
核心检查点 #6: 健壮的健康检查 ⭐

包含：
- 正确的依赖导入
- 异常路径返回 503（不是 500）
- DB/Redis/RLS 检查
"""
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
import logging

logger = logging.getLogger(__name__)


def health(request):
    """
    简单健康检查
    仅检查服务是否运行
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
    })


def ready(request):
    """
    就绪检查（⭐ 核心检查点 #6）
    
    检查：
    1. 数据库连接
    2. Redis 连接
    3. 数据库迁移状态
    4. RLS 启用状态
    
    返回：
    - 200: 所有检查通过
    - 503: 任何检查失败（⭐ 不是 500）
    """
    checks = {}
    all_healthy = True
    
    # 1. 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks['database'] = 'ok'
    except Exception as e:
        logger.error(f'Database check failed: {e}', exc_info=True)
        checks['database'] = f'error: {str(e)}'
        all_healthy = False
    
    # 2. 检查 Redis 连接
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['redis'] = 'ok'
        else:
            checks['redis'] = 'error: cache verification failed'
            all_healthy = False
    except Exception as e:
        logger.error(f'Redis check failed: {e}', exc_info=True)
        checks['redis'] = f'error: {str(e)}'
        all_healthy = False
    
    # 3. 检查数据库迁移状态
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            checks['migrations'] = f'warning: {len(plan)} unapplied migrations'
            all_healthy = False
        else:
            checks['migrations'] = 'ok'
    except Exception as e:
        logger.error(f'Migration check failed: {e}', exc_info=True)
        checks['migrations'] = f'error: {str(e)}'
        all_healthy = False
    
    # 4. 检查 RLS 启用状态（可选但推荐）
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename, rowsecurity 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                  AND tablename IN ('orders', 'tiers', 'commissions', 'allocations')
            """)
            rls_status = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 检查是否所有表都启用了 RLS
            if all(rls_status.values()):
                checks['rls'] = 'ok'
            else:
                disabled_tables = [t for t, enabled in rls_status.items() if not enabled]
                checks['rls'] = f'warning: RLS disabled on {disabled_tables}'
                # 注意：RLS 未启用不一定是错误（开发环境可能故意禁用）
    except Exception as e:
        logger.error(f'RLS check failed: {e}', exc_info=True)
        checks['rls'] = f'error: {str(e)}'
        # RLS 检查失败不影响服务可用性
    
    # 构造响应
    response_data = {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
    }
    
    # ⭐ 返回正确的状态码
    if all_healthy:
        return JsonResponse(response_data, status=200)
    else:
        return JsonResponse(response_data, status=503)  # ⭐ 503 Service Unavailable


def version(request):
    """
    版本信息
    """
    return JsonResponse({
        'version': 'v1.0.0',
        'codename': 'Foundation',
        'release_date': '2025-11-07',
        'timestamp': timezone.now().isoformat(),
    })
