"""
Agent Celery 任务（Phase F）

定时任务：
- 月度对账单生成
- Agent 统计更新
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.db.models import Sum, Count, Q, Max
from django.utils import timezone
from celery import shared_task
import logging

from apps.agents.models import AgentProfile, CommissionStatement, AgentStats, AgentTree
from apps.commissions.models import Commission
from apps.orders.models import Order

logger = logging.getLogger(__name__)


@shared_task
def generate_monthly_statements():
    """
    生成上月佣金对账单
    
    触发时间：每月 1 号凌晨 2 点
    
    逻辑：
    1. 查询所有活跃 Agent
    2. 统计上月佣金数据
    3. 生成 CommissionStatement 记录
    4. 发送邮件通知（可选）
    """
    now = timezone.now()
    
    # 计算上月范围
    first_day_this_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    
    period_start = datetime(
        last_day_last_month.year,
        last_day_last_month.month,
        1,
        tzinfo=now.tzinfo
    )
    period_end = last_day_last_month.replace(hour=23, minute=59, second=59)
    
    logger.info(
        f"Generating statements for period: {period_start.date()} ~ {period_end.date()}"
    )
    
    # 查询所有活跃 Agent
    active_agents = AgentProfile.objects.filter(is_active=True)
    
    generated_count = 0
    skipped_count = 0
    
    for profile in active_agents:
        try:
            # 检查是否已生成
            existing = CommissionStatement.objects.filter(
                agent_profile=profile,
                period_start=period_start.date(),
                period_end=period_end.date()
            ).exists()
            
            if existing:
                skipped_count += 1
                continue
            
            # 统计佣金数据
            commissions = Commission.objects.filter(
                agent=profile.user,
                created_at__gte=period_start,
                created_at__lte=period_end
            )
            
            commission_stats = commissions.aggregate(
                total=Sum('commission_amount_usd'),
                paid=Sum('commission_amount_usd', filter=Q(status='paid')),
                pending=Sum('commission_amount_usd', filter=Q(status__in=['hold', 'ready'])),
            )
            
            # 统计订单数据
            orders = Order.objects.filter(
                referrer=profile.user,
                status='paid',
                created_at__gte=period_start,
                created_at__lte=period_end
            )
            
            order_count = orders.count()
            customer_count = orders.values('buyer').distinct().count()
            
            # ⭐ Phase F 补充：计算期初/期末余额
            # 方法：查询历史变更记录（简化：从当前余额反推）
            
            # 查询本期提现总额
            from apps.agents.models import WithdrawalRequest
            withdrawals_in_period = WithdrawalRequest.objects.filter(
                agent_profile=profile,
                status='completed',
                completed_at__gte=period_start,
                completed_at__lte=period_end
            ).aggregate(
                total=Sum('amount_usd')
            )['total'] or Decimal('0')
            
            # 查询本期已结算佣金（入账金额）
            paid_in_period = commission_stats['paid'] or Decimal('0')
            
            # 计算余额变动
            # 期末余额 = 当前余额
            balance_end = profile.balance_usd
            
            # 期初余额 = 期末余额 - 本期入账 + 本期提现
            balance_start = balance_end - paid_in_period + withdrawals_in_period
            
            # 创建对账单
            statement = CommissionStatement.objects.create(
                agent_profile=profile,
                period_start=period_start.date(),
                period_end=period_end.date(),
                balance_start_of_period=balance_start,
                balance_end_of_period=balance_end,
                total_commissions_usd=commission_stats['total'] or Decimal('0'),
                paid_commissions_usd=paid_in_period,
                pending_commissions_usd=commission_stats['pending'] or Decimal('0'),
                withdrawals_in_period=withdrawals_in_period,
                order_count=order_count,
                customer_count=customer_count
            )
            
            generated_count += 1
            
            logger.info(
                f"Generated statement for {profile.user.email}",
                extra={
                    'statement_id': str(statement.statement_id),
                    'agent_id': str(profile.user.user_id),
                    'total_commissions': str(statement.total_commissions_usd)
                }
            )
            
            # TODO: 发送邮件通知
            
        except Exception as e:
            logger.error(
                f"Failed to generate statement for {profile.user.email}: {e}",
                exc_info=True
            )
    
    logger.info(
        f"Statement generation completed: generated={generated_count}, skipped={skipped_count}"
    )
    
    return {
        'generated': generated_count,
        'skipped': skipped_count,
        'period': f"{period_start.date()} ~ {period_end.date()}"
    }


@shared_task
def update_agent_stats():
    """
    更新 Agent 统计数据
    
    触发时间：每小时
    
    逻辑：
    1. 查询所有 Agent（有佣金记录的用户）
    2. 更新 AgentStats 表
    3. 计算：total_customers, direct_customers, total_sales, total_commissions
    """
    from apps.agents.models import AgentStats, AgentTree
    
    # 查询所有有佣金的 Agent
    agents_with_commissions = Commission.objects.values('agent').distinct()
    
    updated_count = 0
    
    for item in agents_with_commissions:
        agent_id = item['agent']
        
        try:
            # 统计佣金
            commission_stats = Commission.objects.filter(
                agent_id=agent_id
            ).aggregate(
                total_commissions=Sum('commission_amount_usd'),
            )
            
            # 统计订单
            order_stats = Order.objects.filter(
                referrer_id=agent_id,
                status='paid'
            ).aggregate(
                total_sales=Sum('final_price_usd'),
                total_customers=Count('buyer', distinct=True),
                last_order_at=models.Max('created_at')
            )
            
            # 统计直接客户
            direct_customers = AgentTree.objects.filter(
                parent=agent_id,
                depth=1,
                active=True
            ).count()
            
            # 获取 site_id（从第一个佣金）
            first_commission = Commission.objects.filter(
                agent_id=agent_id
            ).select_related('order__site').first()
            
            if not first_commission:
                continue
            
            site_id = first_commission.order.site_id
            
            # 更新或创建统计
            AgentStats.objects.update_or_create(
                site_id=site_id,
                agent=agent_id,
                defaults={
                    'total_customers': order_stats['total_customers'] or 0,
                    'direct_customers': direct_customers,
                    'total_sales': order_stats['total_sales'] or Decimal('0'),
                    'total_commissions': commission_stats['total_commissions'] or Decimal('0'),
                    'last_order_at': order_stats['last_order_at'],
                }
            )
            
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to update stats for agent {agent_id}: {e}")
    
    logger.info(f"Updated stats for {updated_count} agents")
    
    return {'updated': updated_count}

