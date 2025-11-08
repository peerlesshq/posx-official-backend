"""
代理树查询服务

⭐ 功能：
- 递归查询下线结构（使用 PostgreSQL CTE）
- 支持深度限制
- 分页支持

⚠️ 注意：
- 所有查询自动受 RLS 保护（site_id 隔离）
- 仅返回当前用户为根的下线
"""
from typing import List, Dict, Any, Optional
from django.db import connection
from decimal import Decimal
import uuid


class AgentTreeService:
    """代理树查询服务"""
    
    @staticmethod
    def get_downline_structure(
        agent_id: uuid.UUID,
        site_id: uuid.UUID,
        max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取代理下线结构（递归 CTE）
        
        Args:
            agent_id: 代理用户ID
            site_id: 站点ID
            max_depth: 最大深度限制
        
        Returns:
            [
                {
                    "agent_id": "...",
                    "parent_id": "...",
                    "depth": 1,
                    "path": "/root/agent/",
                    "total_customers": 10,  # 占位，后续接入统计
                },
                ...
            ]
        """
        with connection.cursor() as cursor:
            # 递归 CTE 查询下线
            query = """
                WITH RECURSIVE downline AS (
                    -- 基础查询：直接下线
                    SELECT
                        tree_id,
                        site_id,
                        agent,
                        parent,
                        depth,
                        path,
                        active,
                        1 as level
                    FROM agent_trees
                    WHERE parent = %s
                      AND site_id = %s
                      AND active = true
                    
                    UNION ALL
                    
                    -- 递归查询：下线的下线
                    SELECT
                        at.tree_id,
                        at.site_id,
                        at.agent,
                        at.parent,
                        at.depth,
                        at.path,
                        at.active,
                        d.level + 1 as level
                    FROM agent_trees at
                    INNER JOIN downline d ON at.parent = d.agent
                    WHERE at.site_id = %s
                      AND at.active = true
                      AND d.level < %s
                )
                SELECT
                    agent::text as agent_id,
                    parent::text as parent_id,
                    depth,
                    path,
                    level
                FROM downline
                ORDER BY level, depth, agent;
            """
            
            cursor.execute(query, [str(agent_id), str(site_id), str(site_id), max_depth])
            rows = cursor.fetchall()
            
            # 格式化结果
            results = []
            for row in rows:
                results.append({
                    'agent_id': row[0],
                    'parent_id': row[1],
                    'depth': row[2],
                    'path': row[3],
                    'level': row[4],
                    'total_customers': 0,  # 占位，后续接入统计
                })
            
            return results
    
    @staticmethod
    def get_downline_customers(
        agent_id: uuid.UUID,
        site_id: uuid.UUID,
        scope: str = 'all',  # 'direct' 或 'all'
        level: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取代理客户列表
        
        Args:
            agent_id: 代理用户ID
            site_id: 站点ID
            scope: 范围（'direct'=直接下线，'all'=整条线）
            level: 指定层级（仅当 scope='all' 时有效）
            search: 搜索关键词（邮箱/钱包地址）
            page: 页码
            page_size: 每页大小
        
        Returns:
            {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "customers": [
                    {
                        "user_id": "...",
                        "email": "...",
                        "referral_code": "...",
                        "depth": 1,
                        "total_sales": "1000.00",  # 占位
                        "last_order_at": null,      # 占位
                    },
                    ...
                ]
            }
        """
        offset = (page - 1) * page_size
        
        with connection.cursor() as cursor:
            # 构建查询
            if scope == 'direct':
                # 仅直接下线
                where_clause = "WHERE at.parent = %s AND at.site_id = %s AND at.active = true"
                params = [str(agent_id), str(site_id)]
            else:
                # 整条线（递归）
                where_clause = """
                    WHERE at.agent IN (
                        WITH RECURSIVE downline AS (
                            SELECT agent FROM agent_trees
                            WHERE parent = %s AND site_id = %s AND active = true
                            
                            UNION ALL
                            
                            SELECT at2.agent FROM agent_trees at2
                            INNER JOIN downline d ON at2.parent = d.agent
                            WHERE at2.site_id = %s AND at2.active = true
                        )
                        SELECT agent FROM downline
                    )
                """
                params = [str(agent_id), str(site_id), str(site_id)]
                
                # 层级过滤
                if level:
                    where_clause += " AND at.depth = %s"
                    params.append(level)
            
            # 搜索条件
            if search:
                where_clause += " AND (u.email ILIKE %s OR w.address ILIKE %s)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])
            
            # 总数查询
            count_query = f"""
                SELECT COUNT(DISTINCT at.agent)
                FROM agent_trees at
                LEFT JOIN users u ON u.user_id = at.agent
                LEFT JOIN wallets w ON w.user_id = at.agent AND w.is_primary = true
                {where_clause}
            """
            
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # 数据查询
            data_query = f"""
                SELECT DISTINCT
                    u.user_id::text,
                    u.email,
                    u.referral_code,
                    at.depth,
                    COALESCE(ast.total_sales, 0) as total_sales,
                    ast.last_order_at
                FROM agent_trees at
                LEFT JOIN users u ON u.user_id = at.agent
                LEFT JOIN wallets w ON w.user_id = at.agent AND w.is_primary = true
                LEFT JOIN agent_stats ast ON ast.agent = at.agent AND ast.site_id = at.site_id
                {where_clause}
                ORDER BY ast.last_order_at DESC NULLS LAST, at.created_at DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([page_size, offset])
            cursor.execute(data_query, params)
            rows = cursor.fetchall()
            
            # 格式化结果
            customers = []
            for row in rows:
                customers.append({
                    'user_id': row[0],
                    'email': row[1] or '',
                    'referral_code': row[2] or '',
                    'depth': row[3],
                    'total_sales': str(row[4]) if row[4] else '0.00',
                    'last_order_at': row[5].isoformat() if row[5] else None,
                })
            
            # 分页信息
            total_pages = (total + page_size - 1) // page_size
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'customers': customers,
            }



