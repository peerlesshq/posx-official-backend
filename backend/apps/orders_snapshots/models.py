"""
订单佣金策略快照模型

⭐ 核心功能：
- 订单创建时保存当时生效的佣金计划
- 避免计划变更影响历史订单
- 存储为 JSONB 格式（包含所有层级配置）

⭐ RLS 安全：
- 通过 order 外键关联，继承 orders 表的 RLS 隔离
- 但为了安全，显式启用 RLS
"""
import uuid
from django.db import models


class OrderCommissionPolicySnapshot(models.Model):
    """
    订单佣金策略快照
    
    字段说明：
    - order: 关联订单（OneToOne）
    - plan_id: 佣金计划ID（快照时）
    - plan_name: 计划名称
    - plan_version: 计划版本
    - plan_mode: 计算模式（'level' 或 'solar_diff'）
    - diff_reward_enabled: 是否启用差额奖励
    - tiers_json: 层级配置（JSONB 格式）
      格式：
      [
          {"level": 1, "rate_percent": "12.00", "hold_days": 7, ...},
          {"level": 2, "rate_percent": "5.00", "hold_days": 7, ...},
          ...
      ]
    """
    
    snapshot_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="快照唯一标识"
    )
    order_id = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="关联订单ID（OneToOne）"
    )
    plan_id = models.UUIDField(
        help_text="佣金计划ID（快照时）"
    )
    plan_name = models.CharField(
        max_length=100,
        help_text="计划名称"
    )
    plan_version = models.PositiveIntegerField(
        help_text="计划版本"
    )
    plan_mode = models.CharField(
        max_length=20,
        help_text="计算模式"
    )
    diff_reward_enabled = models.BooleanField(
        default=False,
        help_text="是否启用差额奖励"
    )
    tiers_json = models.JSONField(
        help_text="层级配置（JSONB 格式）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_commission_policy_snapshots'
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['plan_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Order Commission Policy Snapshot'
        verbose_name_plural = 'Order Commission Policy Snapshots'
    
    def __str__(self):
        return f"Snapshot for Order {self.order_id}"



