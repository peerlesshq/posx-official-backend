"""
代理视图

⭐ 权限：
- IsAuthenticated（所有端点）
- 仅返回当前用户为根的下线

⭐ 站点隔离：
- 通过 request.site 自动隔离
- RLS 策略提供二次保障
"""
from decimal import Decimal
from django.db.models import Sum, Q, Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from .services.tree_query import AgentTreeService
from .services.balance import (
    get_or_create_agent_profile,
    deduct_balance_for_withdrawal,
)
from .models import AgentProfile, WithdrawalRequest, CommissionStatement
from .serializers import (
    AgentStructureNodeSerializer,
    AgentCustomerListSerializer,
    AgentProfileSerializer,
    WithdrawalRequestSerializer,
    CommissionStatementSerializer,
)
from apps.commissions.models import Commission

logger = logging.getLogger(__name__)


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
    
    @action(detail=False, methods=['get'], url_path='me/balance')
    def my_balance(self, request):
        """
        查询我的余额（Phase F）
        
        Response:
        {
            "balance_usd": "1234.56",
            "total_earned_usd": "5000.00",
            "total_withdrawn_usd": "3765.44",
            "pending_commissions": {
                "hold": "100.00",
                "ready": "200.00"
            }
        }
        """
        # 获取 Profile
        profile = get_or_create_agent_profile(request.user, request.site)
        
        # 查询待结算佣金
        pending_commissions = Commission.objects.filter(
            agent=request.user,
            status__in=['hold', 'ready']
        ).aggregate(
            hold=Sum('commission_amount_usd', filter=Q(status='hold')),
            ready=Sum('commission_amount_usd', filter=Q(status='ready')),
        )
        
        return Response({
            'balance_usd': f"{profile.balance_usd:.2f}",
            'total_earned_usd': f"{profile.total_earned_usd:.2f}",
            'total_withdrawn_usd': f"{profile.total_withdrawn_usd:.2f}",
            'pending_commissions': {
                'hold': f"{(pending_commissions['hold'] or Decimal('0')):.2f}",
                'ready': f"{(pending_commissions['ready'] or Decimal('0')):.2f}",
            }
        })
    
    @action(detail=False, methods=['post'], url_path='withdrawal')
    def submit_withdrawal(self, request):
        """
        提交提现申请（Phase F）
        
        Request Body:
        {
            "amount_usd": "100.00",
            "withdrawal_method": "bank_transfer",
            "account_info": {
                "bank_name": "...",
                "account_number": "...",
                "account_holder": "..."
            }
        }
        
        Response:
        {
            "request_id": "...",
            "status": "submitted"
        }
        """
        # 验证与序列化
        serializer = WithdrawalRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # 获取 Profile
        profile = serializer.validated_data['agent_profile']
        amount = serializer.validated_data['amount_usd']
        
        # 扣减余额（悲观锁）
        if not deduct_balance_for_withdrawal(profile, amount):
            return Response({
                'code': 'WITHDRAWAL.INSUFFICIENT_BALANCE',
                'message': f'余额不足。可用余额：${profile.balance_usd}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建申请
        withdrawal = serializer.save(status='submitted')
        
        logger.info(
            f"Withdrawal request created",
            extra={
                'request_id': str(withdrawal.request_id),
                'profile_id': str(profile.profile_id),
                'amount': str(amount),
                'method': withdrawal.withdrawal_method
            }
        )
        
        # TODO: 发送通知邮件
        
        return Response({
            'request_id': str(withdrawal.request_id),
            'status': withdrawal.status,
            'amount_usd': f"{amount:.2f}"
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='withdrawal-requests')
    def my_withdrawals(self, request):
        """
        查询我的提现记录（Phase F）
        
        Response: 提现申请列表
        """
        # 获取 Profile
        profile = get_or_create_agent_profile(request.user, request.site)
        
        # 查询提现记录
        withdrawals = WithdrawalRequest.objects.filter(
            agent_profile=profile
        ).order_by('-created_at')
        
        serializer = WithdrawalRequestSerializer(withdrawals, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Agent Dashboard 汇总数据（Phase F）
        
        Response:
        {
            "balance": {...},
            "performance": {...},
            "team": {...},
            "recent_commissions": [...],
            "recent_orders": [...]
        }
        """
        user = request.user
        site = request.site
        
        # 获取 Profile
        profile = get_or_create_agent_profile(user, site)
        
        # 1. 余额信息
        balance_data = {
            'available': f"{profile.balance_usd:.2f}",
            'pending_commissions': self._get_pending_commissions(user),
        }
        
        # 2. 业绩信息
        performance_data = self._get_performance_stats(user, site)
        
        # 3. 团队信息
        team_data = self._get_team_stats(user, site)
        
        # 4. 最近佣金（最近10条）
        recent_commissions = Commission.objects.filter(
            agent=user
        ).select_related('order').order_by('-created_at')[:10]
        
        recent_commissions_data = [{
            'commission_id': str(c.commission_id),
            'order_id': str(c.order.order_id),
            'amount_usd': f"{c.commission_amount_usd:.2f}",
            'status': c.status,
            'level': c.level,
            'created_at': c.created_at.isoformat()
        } for c in recent_commissions]
        
        # 5. 下线最近订单（最近10条）
        from apps.orders.models import Order
        recent_orders = Order.objects.filter(
            referrer=user,
            status='paid'
        ).order_by('-created_at')[:10]
        
        recent_orders_data = [{
            'order_id': str(o.order_id),
            'buyer_email': o.buyer.email,
            'amount_usd': f"{o.final_price_usd:.2f}",
            'created_at': o.created_at.isoformat()
        } for o in recent_orders]
        
        return Response({
            'balance': balance_data,
            'performance': performance_data,
            'team': team_data,
            'recent_commissions': recent_commissions_data,
            'recent_orders': recent_orders_data
        })
    
    def _get_pending_commissions(self, user):
        """查询待结算佣金"""
        pending = Commission.objects.filter(
            agent=user,
            status__in=['hold', 'ready']
        ).aggregate(
            hold=Sum('commission_amount_usd', filter=Q(status='hold')),
            ready=Sum('commission_amount_usd', filter=Q(status='ready')),
        )
        return {
            'hold': f"{(pending['hold'] or Decimal('0')):.2f}",
            'ready': f"{(pending['ready'] or Decimal('0')):.2f}",
        }
    
    def _get_performance_stats(self, user, site):
        """查询业绩统计"""
        from apps.orders.models import Order
        from datetime import datetime
        
        # 本月起始
        now = timezone.now()
        this_month_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        
        # 累计统计
        total_stats = Order.objects.filter(
            referrer=user,
            status='paid'
        ).aggregate(
            total_sales=Sum('final_price_usd'),
            total_orders=Count('order_id')
        )
        
        # 本月统计
        this_month_stats = Order.objects.filter(
            referrer=user,
            status='paid',
            created_at__gte=this_month_start
        ).aggregate(
            month_sales=Sum('final_price_usd'),
            month_orders=Count('order_id')
        )
        
        return {
            'total_sales': f"{(total_stats['total_sales'] or Decimal('0')):.2f}",
            'total_orders': total_stats['total_orders'] or 0,
            'this_month_sales': f"{(this_month_stats['month_sales'] or Decimal('0')):.2f}",
            'this_month_orders': this_month_stats['month_orders'] or 0,
        }
    
    def _get_team_stats(self, user, site):
        """查询团队统计"""
        from apps.agents.models import AgentTree
        
        # 查询下线数量
        downlines = AgentTree.objects.filter(
            site_id=site.site_id,
            parent=user.user_id,
            active=True
        ).aggregate(
            total=Count('tree_id'),
            max_depth=models.Max('depth')
        )
        
        return {
            'total_downlines': downlines['total'] or 0,
            'max_depth': downlines['max_depth'] or 0,
        }

