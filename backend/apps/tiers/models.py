"""
Tier模型 - 档位/套餐（受RLS保护）
每个站点独立配置档位，支持库存并发控制（乐观锁）

新增促销功能：
- 促销价格配置（时间范围内生效）
- 额外代币奖励
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


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
    
    促销功能：
    - promotional_price_usd: 促销价（时间范围内生效）
    - bonus_tokens_per_unit: 额外赠送代币
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
    
    # 促销配置（新增）
    bonus_tokens_per_unit = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="额外赠送代币（每单位）"
    )
    promotional_price_usd = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="促销价（可选，null=使用原价）"
    )
    promotion_valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="促销生效开始时间"
    )
    promotion_valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="促销生效结束时间"
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
    
    def is_promotion_active(self) -> bool:
        """检查促销是否在有效期内"""
        if not self.promotional_price_usd:
            return False
        
        if not self.promotion_valid_from or not self.promotion_valid_until:
            return False
        
        now = timezone.now()
        return self.promotion_valid_from <= now <= self.promotion_valid_until
    
    def get_current_price(self) -> Decimal:
        """获取当前有效价格（促销价或原价）"""
        if self.is_promotion_active():
            return self.promotional_price_usd
        return self.list_price_usd
    
    def get_total_tokens_per_unit(self) -> Decimal:
        """获取单位总代币数（基础+赠送）"""
        return self.tokens_per_unit + self.bonus_tokens_per_unit



