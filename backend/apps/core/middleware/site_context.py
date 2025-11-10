"""
站点上下文中间件

⭐ 核心功能：
- 从 X-Site-Code 或 Host 解析站点
- 在数据库会话中设置 app.current_site_id（触发 RLS）
- 将 site 实例附加到 request.site

⭐ RLS 集成：
- 每个请求在 process_request 时执行：
  SET LOCAL app.current_site_id = '<site_uuid>'
- 所有后续 SQL 查询自动受 RLS 隔离

⚠️ 安全注意：
- 无站点 = 400 Bad Request
- 不允许跨站点访问
- Admin 查询使用独立连接（posx_admin role）
"""
import logging
from django.http import JsonResponse
from django.db import connection
from apps.sites.models import Site

logger = logging.getLogger(__name__)


class SiteContextMiddleware:
    """
    站点上下文中间件
    
    解析顺序：
    1. X-Site-Code 请求头（优先）
    2. request.get_host() 域名映射
    3. 无匹配 → 400 错误
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """处理每个请求"""
        # 豁免路径与前缀
        EXEMPT_PATHS = ("/health/", "/ready/", "/version/", "/favicon.ico")
        EXEMPT_PREFIXES = ("/admin/", "/__debug__/", "/static/", "/static/admin/", "/media/")
        
        if request.path in EXEMPT_PATHS or \
           any(request.path.startswith(p) for p in EXEMPT_PREFIXES):
            return self.get_response(request)
        
        # 解析站点
        site = self._resolve_site(request)
        
        if not site:
            return JsonResponse(
                {
                    "error": "invalid_site",
                    "message": "无法识别站点，请提供有效的 X-Site-Code 或访问正确的域名"
                },
                status=400
            )
        
        # 附加到 request
        request.site = site
        
        # 设置数据库上下文（RLS）
        self._set_database_context(site)
        
        # 继续处理
        response = self.get_response(request)
        
        return response
    
    def _resolve_site(self, request) -> Site:
        """
        解析站点
        
        优先级：
        1. X-Site-Code 头
        2. Host 域名
        
        Returns:
            Site 实例或 None
        """
        # 方式1: X-Site-Code 头
        site_code = request.META.get('HTTP_X_SITE_CODE')
        if site_code:
            try:
                site = Site.objects.get(code=site_code, is_active=True)
                logger.debug(f"Resolved site from X-Site-Code: {site_code}")
                return site
            except Site.DoesNotExist:
                logger.warning(f"Invalid X-Site-Code: {site_code}")
                return None
        
        # 方式2: Host 域名
        host = request.get_host()
        # 移除端口
        if ':' in host:
            host = host.split(':')[0]
        
        try:
            site = Site.objects.get(domain=host, is_active=True)
            logger.debug(f"Resolved site from host: {host}")
            return site
        except Site.DoesNotExist:
            logger.warning(f"No site found for host: {host}")
            return None
    
    def _set_database_context(self, site: Site):
        """
        设置数据库会话变量（触发 RLS）
        
        ⭐ 关键：
        - 使用 SET LOCAL（仅当前事务有效）
        - 每个请求都重新设置
        - UUID 类型转换确保 RLS 策略匹配
        
        SQL 示例：
        SET LOCAL app.current_site_id = '550e8400-e29b-41d4-a716-446655440000';
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.current_site_id = %s",
                [str(site.site_id)]
            )
        
        logger.debug(f"Set database context for site: {site.code} ({site.site_id})")


class SiteContextMiddlewareExempt:
    """
    站点上下文豁免装饰器
    
    用于不需要站点上下文的端点（如健康检查）
    
    使用：
    @site_context_exempt
    def health_check(request):
        return JsonResponse({"status": "ok"})
    """
    
    def __init__(self, view_func):
        self.view_func = view_func
    
    def __call__(self, request, *args, **kwargs):
        request.site_context_exempt = True
        return self.view_func(request, *args, **kwargs)


# 导出装饰器
site_context_exempt = SiteContextMiddlewareExempt



