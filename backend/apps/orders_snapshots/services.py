"""
订单快照服务

⭐ 功能：
- 订单创建时自动保存佣金计划快照
- 查询某时点生效的佣金计划
"""
from typing import Optional
from django.utils import timezone
from django.db.models import Q
from apps.commission_plans.models import CommissionPlan
from .models import OrderCommissionPolicySnapshot
import uuid


class OrderSnapshotService:
    """订单快照服务"""
    
    @staticmethod
    def create_snapshot_for_order(order_id: uuid.UUID, site_id: uuid.UUID) -> Optional[OrderCommissionPolicySnapshot]:
        """
        为订单创建佣金计划快照
        
        流程：
        1. 查询当前生效的佣金计划（按 effective_from/to 和 is_active）
        2. 序列化计划和层级配置为 JSONB
        3. 创建快照记录
        
        Args:
            order_id: 订单ID
            site_id: 站点ID
        
        Returns:
            OrderCommissionPolicySnapshot 实例或 None
        """
        # 查询当前生效的计划
        now = timezone.now()
        
        try:
            plan = CommissionPlan.objects.filter(
                site_id=site_id,
                is_active=True,
                # 时间范围检查
            ).filter(
                Q(effective_from__isnull=True) | Q(effective_from__lte=now),
                Q(effective_to__isnull=True) | Q(effective_to__gte=now),
            ).prefetch_related('tiers').first()
            
            if not plan:
                # 无生效计划，返回 None（订单创建逻辑可决定是否允许）
                return None
            
            # 序列化层级配置
            tiers_data = []
            for tier in plan.tiers.all():
                tiers_data.append({
                    'level': tier.level,
                    'rate_percent': str(tier.rate_percent),
                    'min_sales': str(tier.min_sales),
                    'diff_cap_percent': str(tier.diff_cap_percent) if tier.diff_cap_percent else None,
                    'hold_days': tier.hold_days,
                })
            
            # 创建快照
            snapshot = OrderCommissionPolicySnapshot.objects.create(
                order_id=order_id,
                plan_id=plan.plan_id,
                plan_name=plan.name,
                plan_version=plan.version,
                plan_mode=plan.mode,
                diff_reward_enabled=plan.diff_reward_enabled,
                tiers_json=tiers_data,
            )
            
            return snapshot
            
        except Exception as e:
            # 记录错误（可用日志）
            print(f"Failed to create snapshot for order {order_id}: {e}")
            return None
    
    @staticmethod
    def get_snapshot_by_order(order_id: uuid.UUID) -> Optional[OrderCommissionPolicySnapshot]:
        """
        根据订单ID获取快照
        
        Args:
            order_id: 订单ID
        
        Returns:
            OrderCommissionPolicySnapshot 实例或 None
        """
        try:
            return OrderCommissionPolicySnapshot.objects.get(order_id=order_id)
        except OrderCommissionPolicySnapshot.DoesNotExist:
            return None



