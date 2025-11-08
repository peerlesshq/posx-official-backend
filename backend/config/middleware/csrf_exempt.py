"""
CSRF Exemption Middleware
核心检查点 #3: CSRF 与 API 路由一致性 ⭐

功能：对特定路径（API endpoints）豁免 CSRF 检查
位置：必须在 CsrfViewMiddleware 之前
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFExemptMiddleware(MiddlewareMixin):
    """
    智能 CSRF 豁免中间件
    
    对以下路径豁免 CSRF：
    - /api/v1/* (所有 API endpoints)
    - /health/ (健康检查)
    - /ready/ (就绪检查)
    - /version/ (版本信息)
    - /api/v1/webhooks/* (Webhook endpoints)
    
    原理：
    设置 request._dont_enforce_csrf_checks = True
    让后续的 CsrfViewMiddleware 跳过检查
    """
    
    def process_request(self, request):
        """在 CSRF 中间件之前处理请求"""
        # 获取配置的豁免路径
        exempt_paths = getattr(settings, 'CSRF_EXEMPT_PATHS', [])
        
        # 检查当前路径是否需要豁免
        for path in exempt_paths:
            if request.path.startswith(path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
        
        return None
