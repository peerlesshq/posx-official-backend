"""
请求ID中间件

为每个请求生成唯一ID，便于日志追踪
"""
import uuid
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    为每个请求生成唯一ID
    
    功能：
    - 生成 UUID 请求ID
    - 附加到 request.request_id
    - 添加到响应头 X-Request-ID
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # 处理请求
        response = self.get_response(request)
        
        # 添加响应头
        response['X-Request-ID'] = request_id
        
        return response



