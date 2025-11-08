"""
代理树模型

⭐ RLS 安全：
- AgentTree 受 RLS 保护（site_id 隔离）
- 支持递归查询（CTE）

功能：
- 多层级代理结构（树形）
- 记录代理深度（便于查询）
- 支持激活/停用
"""
import uuid
from django.db import models


class AgentTree(models.Model):
    """
    代理树关系表
    
    字段说明：
    - agent: 代理用户（User）
    - parent: 上级代理（自关联）
    - depth: 深度（1=直接推荐，2=二级...）
    - path: 路径（便于快速查询上下线）格式：/root_id/parent_id/agent_id/
    - active: 激活状态
    """
    
    tree_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="关系唯一标识"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID（RLS隔离）"
    )
    agent = models.UUIDField(
        db_index=True,
        help_text="代理用户ID（关联 users.user_id）"
    )
    parent = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="上级代理ID（NULL=根节点）"
    )
    depth = models.PositiveSmallIntegerField(
        default=1,
        help_text="深度（1=直接推荐）"
    )
    path = models.TextField(
        help_text="路径（/root/parent/agent/）"
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_trees'
        indexes = [
            models.Index(fields=['site_id', 'agent']),
            models.Index(fields=['site_id', 'parent']),
            models.Index(fields=['site_id', 'active']),
            models.Index(fields=['depth']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['site_id', 'agent', 'parent'],
                name='unique_site_agent_parent'
            ),
        ]
        verbose_name = 'Agent Tree'
        verbose_name_plural = 'Agent Trees'
    
    def __str__(self):
        return f"Agent {self.agent} (depth={self.depth})"


class AgentStats(models.Model):
    """
    代理统计表（预计算）
    
    ⚠️ 本表数据由定时任务或触发器维护
    用于快速查询代理业绩
    
    字段说明：
    - agent: 代理用户ID
    - total_customers: 累计客户数（下线）
    - direct_customers: 直接客户数
    - total_sales: 累计销售额
    - total_commissions: 累计佣金
    - last_order_at: 最后订单时间
    """
    
    stat_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="统计记录ID"
    )
    site_id = models.UUIDField(
        db_index=True,
        help_text="站点ID（RLS隔离）"
    )
    agent = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="代理用户ID"
    )
    total_customers = models.PositiveIntegerField(
        default=0,
        help_text="累计客户数"
    )
    direct_customers = models.PositiveIntegerField(
        default=0,
        help_text="直接客户数（depth=1）"
    )
    total_sales = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=0,
        help_text="累计销售额（USD）"
    )
    total_commissions = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=0,
        help_text="累计佣金"
    )
    last_order_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="最后订单时间"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_stats'
        indexes = [
            models.Index(fields=['site_id', 'agent']),
            models.Index(fields=['total_sales']),
            models.Index(fields=['last_order_at']),
        ]
        verbose_name = 'Agent Stats'
        verbose_name_plural = 'Agent Stats'
    
    def __str__(self):
        return f"Stats for Agent {self.agent}"



