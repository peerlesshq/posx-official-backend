"""
Tier模型 - 档位/套餐（受RLS保护）
每个站点独立配置档位，支持库存并发控制（乐观锁）
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Tier(models.Model):
    """
    档位模型（受RLS保护）
    
    ⚠️ 安全：
    - site_id受RLS策略保护
    - site_id不可变（触发器保护）
    
    并发控制：
    - version字段实现乐观锁
    - 锁定库存时需检查version
    
    库存计算：
    - available_units = total_units - sold_units
    """
    tier_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="档位唯一标识"
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='tiers',
        help_text="所属站点"
    )
    name = models.CharField(
        max_length=100,
        help_text="档位名称"
    )
    description = models.TextField(
        blank=True,
        help_text="档位描述"
    )
    list_price_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="单价（USD）"
    )
    tokens_per_unit = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="单位代币数量"
    )
    total_units = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="总库存"
    )
    sold_units = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="已售数量"
    )
    available_units = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="可用库存（计算字段）"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="展示顺序"
    )
    version = models.IntegerField(
        default=0,
        help_text="乐观锁版本号"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="档位激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tiers'
        indexes = [
            models.Index(fields=['site', 'display_order']),
            models.Index(fields=['site', 'is_active']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        verbose_name = 'Tier'
        verbose_name_plural = 'Tiers'
    
    def __str__(self):
        return f"{self.name} ({self.site.code})"
    
    def save(self, *args, **kwargs):
        """保存前同步available_units"""
        self.available_units = self.total_units - self.sold_units
        super().save(*args, **kwargs)



