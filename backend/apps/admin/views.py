"""
Admin 报表视图（Phase F）

⚠️ 安全：
- 使用 Admin 数据库连接（绕过 RLS）
- 仅超级管理员可访问
- 完整审计日志
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import connections
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
import logging

from apps.orders.models import Order
from apps.commissions.models import Commission
from apps.agents.models import AgentProfile, AgentStats
from apps.allocations.models import Allocation

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def overview_report(request):
    """
    全站业绩概览报表（Phase F）
    
    Query Params:
    - site_code: NA/ASIA/all（默认 all）
    - date_from: YYYY-MM-DD（默认本月1号）
    - date_to: YYYY-MM-DD（默认今天）
    
    Response:
    {
        "period": {"from": "...", "to": "..."},
        "total_sales": "100000.00",
        "total_orders": 500,
        "total_commissions_paid": "12000.00",
        "total_commissions_pending": "3000.00",
        "active_agents": 50,
        "top_agents": [...]
    }
    
    ⚠️ 使用 Admin 连接（绕过 RLS）
    """
    # 参数解析
    site_code = request.query_params.get('site_code', 'all')
    
    # 日期范围（默认本月）
    now = timezone.now()
    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_from = date_from.replace(tzinfo=now.tzinfo)
        except ValueError:
            date_from = first_day_of_month
    else:
        date_from = first_day_of_month
    
    date_to = request.query_params.get('date_to')
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to.replace(hour=23, minute=59, second=59, tzinfo=now.tzinfo)
        except ValueError:
            date_to = now
    else:
        date_to = now
    
    # 使用 Admin 连接查询（绕过 RLS）⭐
    with connections['admin'].cursor() as cursor:
        # 查询订单统计
        site_filter = ""
        if site_code != 'all':
            site_filter = f"AND s.code = '{site_code}'"
        
        cursor.execute(f"""
            SELECT 
                COUNT(o.order_id) AS total_orders,
                COALESCE(SUM(o.final_price_usd), 0) AS total_sales
            FROM orders o
            JOIN sites s ON o.site_id = s.site_id
            WHERE o.status = 'paid'
              AND o.created_at >= %s
              AND o.created_at <= %s
              {site_filter}
        """, [date_from, date_to])
        
        row = cursor.fetchone()
        total_orders = row[0] or 0
        total_sales = row[1] or Decimal('0')
        
        # 查询佣金统计
        cursor.execute(f"""
            SELECT 
                COALESCE(SUM(CASE WHEN c.status = 'paid' THEN c.commission_amount_usd ELSE 0 END), 0) AS paid,
                COALESCE(SUM(CASE WHEN c.status IN ('hold', 'ready') THEN c.commission_amount_usd ELSE 0 END), 0) AS pending
            FROM commissions c
            JOIN orders o ON c.order_id = o.order_id
            JOIN sites s ON o.site_id = s.site_id
            WHERE c.created_at >= %s
              AND c.created_at <= %s
              {site_filter}
        """, [date_from, date_to])
        
        row = cursor.fetchone()
        commissions_paid = row[0] or Decimal('0')
        commissions_pending = row[1] or Decimal('0')
        
        # 查询活跃 Agent 数量
        cursor.execute(f"""
            SELECT COUNT(DISTINCT c.agent_id)
            FROM commissions c
            JOIN orders o ON c.order_id = o.order_id
            JOIN sites s ON o.site_id = s.site_id
            WHERE c.created_at >= %s
              AND c.created_at <= %s
              {site_filter}
        """, [date_from, date_to])
        
        active_agents = cursor.fetchone()[0] or 0
        
        # 查询 Top 10 Agents
        cursor.execute(f"""
            SELECT 
                u.email AS agent_email,
                COUNT(DISTINCT o.order_id) AS order_count,
                COALESCE(SUM(o.final_price_usd), 0) AS total_sales,
                COALESCE(SUM(c.commission_amount_usd), 0) AS total_commissions
            FROM commissions c
            JOIN orders o ON c.order_id = o.order_id
            JOIN sites s ON o.site_id = s.site_id
            JOIN users u ON c.agent_id = u.user_id
            WHERE c.created_at >= %s
              AND c.created_at <= %s
              {site_filter}
            GROUP BY u.user_id, u.email
            ORDER BY total_sales DESC
            LIMIT 10
        """, [date_from, date_to])
        
        columns = [col[0] for col in cursor.description]
        top_agents = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # 格式化响应
    return Response({
        'period': {
            'from': date_from.strftime('%Y-%m-%d'),
            'to': date_to.strftime('%Y-%m-%d')
        },
        'total_sales': f"{total_sales:.2f}",
        'total_orders': total_orders,
        'total_commissions_paid': f"{commissions_paid:.2f}",
        'total_commissions_pending': f"{commissions_pending:.2f}",
        'active_agents': active_agents,
        'top_agents': [
            {
                'agent_email': agent['agent_email'],
                'order_count': agent['order_count'],
                'total_sales': f"{agent['total_sales']:.2f}",
                'total_commissions': f"{agent['total_commissions']:.2f}"
            }
            for agent in top_agents
        ]
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def agent_leaderboard(request):
    """
    Agent 排行榜报表（Phase F）
    
    Query Params:
    - period: this_month/last_month/this_quarter（默认 this_month）
    - metric: total_sales/total_commissions/new_customers（默认 total_sales）
    - limit: 10-100（默认 20）
    
    Response:
    [
        {
            "rank": 1,
            "agent_id": "...",
            "agent_email": "...",
            "total_sales": "50000.00",
            "total_commissions": "6000.00",
            "customer_count": 100
        },
        ...
    ]
    
    ⚠️ 使用 Admin 连接（绕过 RLS）
    """
    # 参数
    period = request.query_params.get('period', 'this_month')
    metric = request.query_params.get('metric', 'total_sales')
    limit = int(request.query_params.get('limit', 20))
    
    if limit < 10:
        limit = 10
    elif limit > 100:
        limit = 100
    
    # 计算日期范围
    now = timezone.now()
    if period == 'this_month':
        date_from = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        date_to = now
    elif period == 'last_month':
        first_day_this_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        date_from = datetime(last_day_last_month.year, last_day_last_month.month, 1, tzinfo=now.tzinfo)
        date_to = last_day_last_month.replace(hour=23, minute=59, second=59)
    elif period == 'this_quarter':
        quarter = (now.month - 1) // 3
        date_from = datetime(now.year, quarter * 3 + 1, 1, tzinfo=now.tzinfo)
        date_to = now
    else:
        date_from = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        date_to = now
    
    # 排序字段映射
    order_by_map = {
        'total_sales': 'total_sales DESC',
        'total_commissions': 'total_commissions DESC',
        'new_customers': 'customer_count DESC',
    }
    order_by = order_by_map.get(metric, 'total_sales DESC')
    
    # 使用 Admin 连接查询
    with connections['admin'].cursor() as cursor:
        cursor.execute(f"""
            SELECT 
                u.user_id AS agent_id,
                u.email AS agent_email,
                COUNT(DISTINCT o.order_id) AS order_count,
                COALESCE(SUM(o.final_price_usd), 0) AS total_sales,
                COALESCE(SUM(c.commission_amount_usd), 0) AS total_commissions,
                COUNT(DISTINCT o.buyer_id) AS customer_count
            FROM commissions c
            JOIN orders o ON c.order_id = o.order_id
            JOIN users u ON c.agent_id = u.user_id
            WHERE c.created_at >= %s
              AND c.created_at <= %s
            GROUP BY u.user_id, u.email
            ORDER BY {order_by}
            LIMIT %s
        """, [date_from, date_to, limit])
        
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # 添加排名
    leaderboard = [
        {
            'rank': idx + 1,
            'agent_id': str(agent['agent_id']),
            'agent_email': agent['agent_email'],
            'total_sales': f"{agent['total_sales']:.2f}",
            'total_commissions': f"{agent['total_commissions']:.2f}",
            'customer_count': agent['customer_count']
        }
        for idx, agent in enumerate(results)
    ]
    
    return Response(leaderboard)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def commission_reconciliation(request):
    """
    佣金对账报表（Phase F）
    
    Query Params:
    - period: YYYY-MM（默认当月）
    - site_code: NA/ASIA/all（默认 all）
    
    Response:
    {
        "period": "2025-11",
        "site_code": "NA",
        "total_generated": "15000.00",
        "total_paid": "8000.00",
        "total_pending": "5000.00",
        "total_cancelled": "2000.00",
        "by_status": {...},
        "by_level": {...}
    }
    
    ⚠️ 使用 Admin 连接（绕过 RLS）
    """
    # 参数
    period = request.query_params.get('period')
    site_code = request.query_params.get('site_code', 'all')
    
    # 解析期间
    now = timezone.now()
    if period:
        try:
            year, month = period.split('-')
            period_start = datetime(int(year), int(month), 1, tzinfo=now.tzinfo)
        except ValueError:
            period_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    else:
        period_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    
    # 计算期间结束
    if period_start.month == 12:
        period_end = datetime(period_start.year + 1, 1, 1, tzinfo=now.tzinfo) - timedelta(seconds=1)
    else:
        period_end = datetime(period_start.year, period_start.month + 1, 1, tzinfo=now.tzinfo) - timedelta(seconds=1)
    
    # 使用 Admin 连接
    with connections['admin'].cursor() as cursor:
        site_filter = ""
        if site_code != 'all':
            site_filter = f"AND s.code = '{site_code}'"
        
        # 按状态统计
        cursor.execute(f"""
            SELECT 
                c.status,
                COUNT(c.commission_id) AS count,
                COALESCE(SUM(c.commission_amount_usd), 0) AS amount
            FROM commissions c
            JOIN orders o ON c.order_id = o.order_id
            JOIN sites s ON o.site_id = s.site_id
            WHERE c.created_at >= %s
              AND c.created_at <= %s
              {site_filter}
            GROUP BY c.status
        """, [period_start, period_end])
        
        by_status = {}
        total_generated = Decimal('0')
        total_paid = Decimal('0')
        total_pending = Decimal('0')
        total_cancelled = Decimal('0')
        
        for row in cursor.fetchall():
            status_name, count, amount = row
            by_status[status_name] = {
                'count': count,
                'amount': f"{amount:.2f}"
            }
            total_generated += amount
            
            if status_name == 'paid':
                total_paid = amount
            elif status_name in ['hold', 'ready']:
                total_pending += amount
            elif status_name == 'cancelled':
                total_cancelled = amount
        
        # 按层级统计
        cursor.execute(f"""
            SELECT 
                c.level,
                COUNT(c.commission_id) AS count,
                COALESCE(SUM(c.commission_amount_usd), 0) AS amount
            FROM commissions c
            JOIN orders o ON c.order_id = o.order_id
            JOIN sites s ON o.site_id = s.site_id
            WHERE c.created_at >= %s
              AND c.created_at <= %s
              {site_filter}
            GROUP BY c.level
            ORDER BY c.level
        """, [period_start, period_end])
        
        by_level = {}
        for row in cursor.fetchall():
            level, count, amount = row
            by_level[f"L{level}"] = {
                'count': count,
                'amount': f"{amount:.2f}"
            }
    
    return Response({
        'period': period_start.strftime('%Y-%m'),
        'site_code': site_code,
        'total_generated': f"{total_generated:.2f}",
        'total_paid': f"{total_paid:.2f}",
        'total_pending': f"{total_pending:.2f}",
        'total_cancelled': f"{total_cancelled:.2f}",
        'by_status': by_status,
        'by_level': by_level
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def anomaly_report(request):
    """
    异常监控报表（Phase F）
    
    Response:
    {
        "stuck_commissions": 10,
        "failed_allocations": 5,
        "disputed_orders": 2,
        "inactive_agents": 20,
        "pending_withdrawals": 8
    }
    
    ⚠️ 使用 Admin 连接（绕过 RLS）
    """
    now = timezone.now()
    
    # 1. 卡住的佣金（hold 超过 14 天）
    stuck_threshold = now - timedelta(days=14)
    stuck_commissions = Commission.objects.filter(
        status='hold',
        hold_until__lt=stuck_threshold
    ).count()
    
    # 2. 失败的分配
    failed_allocations = Allocation.objects.filter(
        status='failed'
    ).count()
    
    # 3. 争议订单
    disputed_orders = Order.objects.filter(
        disputed=True
    ).count()
    
    # 4. 不活跃的 Agent（90 天无订单）
    inactive_threshold = now - timedelta(days=90)
    with connections['admin'].cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT ap.profile_id)
            FROM agent_profiles ap
            LEFT JOIN (
                SELECT DISTINCT c.agent_id, MAX(o.created_at) AS last_order_at
                FROM commissions c
                JOIN orders o ON c.order_id = o.order_id
                GROUP BY c.agent_id
            ) recent ON ap.user_id = recent.agent_id
            WHERE ap.is_active = true
              AND (recent.last_order_at IS NULL OR recent.last_order_at < %s)
        """, [inactive_threshold])
        
        inactive_agents = cursor.fetchone()[0] or 0
    
    # 5. 待审核提现
    pending_withdrawals = WithdrawalRequest.objects.filter(
        status='submitted'
    ).count()
    
    return Response({
        'stuck_commissions': stuck_commissions,
        'failed_allocations': failed_allocations,
        'disputed_orders': disputed_orders,
        'inactive_agents': inactive_agents,
        'pending_withdrawals': pending_withdrawals
    })

