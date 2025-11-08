"""
自定义异常处理器

⭐ 功能：
- 统一异常响应格式
- 记录异常日志
- 返回友好错误信息
- 包含 request_id 便于追踪
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# 错误码映射（轻量设计）
ERROR_CODE_MAP = {
    status.HTTP_400_BAD_REQUEST: 'VALIDATION.INVALID_INPUT',
    status.HTTP_401_UNAUTHORIZED: 'AUTH.UNAUTHORIZED',
    status.HTTP_403_FORBIDDEN: 'AUTH.FORBIDDEN',
    status.HTTP_404_NOT_FOUND: 'RESOURCE.NOT_FOUND',
    status.HTTP_500_INTERNAL_SERVER_ERROR: 'SERVER.INTERNAL_ERROR',
}


def custom_exception_handler(exc, context):
    """
    自定义 DRF 异常处理器
    
    Returns:
        Response: 统一格式的错误响应
        {
            "code": "AUTH.UNAUTHORIZED",
            "message": "Authentication failed",
            "detail": {...},
            "request_id": "uuid"
        }
    """
    # 调用 DRF 默认处理器
    response = exception_handler(exc, context)
    
    if response is not None:
        # 获取 request_id
        request = context.get('request')
        request_id = getattr(request, 'request_id', 'unknown')
        
        # 生成错误码
        error_code = ERROR_CODE_MAP.get(
            response.status_code,
            f'ERROR.HTTP_{response.status_code}'
        )
        
        # 统一错误响应格式
        custom_response_data = {
            'code': error_code,
            'message': str(exc),
            'detail': response.data,
            'request_id': request_id,
        }
        
        response.data = custom_response_data
        
        # 记录错误日志
        log_extra = {
            'request_id': request_id,
            'status_code': response.status_code,
            'error_code': error_code,
        }
        
        if response.status_code >= 500:
            logger.error(
                f"Server error [{error_code}]: {exc}",
                exc_info=True,
                extra=log_extra
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Client error [{error_code}]: {exc}",
                extra=log_extra
            )
    
    return response

