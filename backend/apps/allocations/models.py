"""
Allocation模型 - 代币分配（受RLS保护）
订单支付后创建，通过Fireblocks批量发放
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Allocation(models.Model):
    """
    代币分配模型（受RLS保护，通过order.site_id）
    
    ⚠️ 安全：
    - 通过order关联site_id，受RLS保护
    - fireblocks_tx_id唯一索引（幂等性）
    - order_id一对一（每个订单只有一条分配记录）
    
    状态流转：
    - pending: 待发放（订单paid后创建）
    - processing: 发放中（调用Fireblocks API后）
    - completed: 已完成（Fireblocks webhook确认）
    - failed: 发放失败（需手动重试）
    
    批量限制：
    - 管理员批量发送≤100条/次
    """
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]
    
    allocation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="分配唯一标识"
    )
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='allocation',
        help_text="关联订单（一对一）"
    )
    wallet_address = models.CharField(
        max_length=42,
        help_text="收币钱包地址（快照，lowercase）"
    )
    token_amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="代币数量"
    )
    
    # ========== Task 4: Vesting支持 ⭐ ==========
    released_tokens = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        help_text='已发放到链上的代币数量（累加）'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
        help_text="分配状态"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allocations'
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'completed']),
                name='chk_allocation_status'
            ),
        ]
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'Allocation'
        verbose_name_plural = 'Allocations'
    
    def __str__(self):
        return f"Allocation {self.order_id} - {self.token_amount} ({self.status})"
    
    def save(self, *args, **kwargs):
        """保存前统一钱包地址为lowercase"""
        if self.wallet_address:
            self.wallet_address = self.wallet_address.lower()
        super().save(*args, **kwargs)



