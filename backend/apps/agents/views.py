"""
代理视图

⭐ 权限：
- IsAuthenticated（所有端点）
- 仅返回当前用户为根的下线

⭐ 站点隔离：
- 通过 request.site 自动隔离
- RLS 策略提供二次保障
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services.tree_query import AgentTreeService
from .serializers import (
    AgentStructureNodeSerializer,
    AgentCustomerListSerializer,
)


class AgentViewSet(viewsets.ViewSet):
    """
    代理视图集
    
    功能：
    - GET /api/v1/agents/me/structure/ - 我的下线结构
    - GET /api/v1/agents/me/customers/ - 我的客户列表
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='me/structure')
    def my_structure(self, request):
        """
        获取我的下线结构
        
        Query Params:
        - depth: 最大深度（默认10）
        
        Response:
        {
            "agent_id": "...",
            "site_code": "NA",
            "total_downlines": 50,
            "structure": [
                {
                    "agent_id": "...",
                    "parent_id": "...",
                    "depth": 1,
                    "path": "/root/agent/",
                    "level": 1,
                    "total_customers": 10
                },
                ...
            ]
        }
        """
        # 参数
        max_depth = int(request.query_params.get('depth', 10))
        if max_depth < 1 or max_depth > 20:
            max_depth = 10
        
        # 查询
        agent_id = request.user.user_id
        site_id = request.site.site_id
        
        structure = AgentTreeService.get_downline_structure(
            agent_id=agent_id,
            site_id=site_id,
            max_depth=max_depth
        )
        
        # 序列化
        serializer = AgentStructureNodeSerializer(structure, many=True)
        
        return Response({
            'agent_id': str(agent_id),
            'site_code': request.site.code,
            'total_downlines': len(structure),
            'structure': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='me/customers')
    def my_customers(self, request):
        """
        获取我的客户列表
        
        Query Params:
        - scope: 'direct' | 'all'（默认 'all'）
        - level: 指定层级（1-10，仅 scope='all' 时有效）
        - search: 搜索关键词（邮箱/钱包）
        - page: 页码（默认1）
        - size: 每页大小（默认20，最大100）
        
        ⚠️ scope='all' 必须分页（防止大结果集）
        """
        # 参数
        scope = request.query_params.get('scope', 'all')
        if scope not in ['direct', 'all']:
            scope = 'all'
        
        # ⚠️ scope='all' 强制分页
        if scope == 'all':
            page = request.query_params.get('page')
            size = request.query_params.get('size')
            
            if not page or not size:
                return Response({
                    'code': 'VALIDATION.PAGINATION_REQUIRED',
                    'message': 'scope="all" 时必须提供 page 和 size 参数',
                    'hint': '例如：?scope=all&page=1&size=20'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        level = request.query_params.get('level')
        if level:
            try:
                level = int(level)
                if level < 1 or level > 10:
                    level = None
            except ValueError:
                level = None
        
        search = request.query_params.get('search', '').strip()
        
        page = int(request.query_params.get('page', 1))
        if page < 1:
            page = 1
        
        page_size = int(request.query_params.get('size', 20))
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # 查询
        agent_id = request.user.user_id
        site_id = request.site.site_id
        
        result = AgentTreeService.get_downline_customers(
            agent_id=agent_id,
            site_id=site_id,
            scope=scope,
            level=level,
            search=search,
            page=page,
            page_size=page_size
        )
        
        # 序列化
        serializer = AgentCustomerListSerializer(result)
        
        return Response(serializer.data)

