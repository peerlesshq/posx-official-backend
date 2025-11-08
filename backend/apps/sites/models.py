"""
Site模型 - 多站点元数据（不受RLS限制）
支持按地理区域隔离：NA（北美）、ASIA（亚洲）等
"""
import uuid
from django.db import models


class Site(models.Model):
    """
    站点模型（全局元数据）
    
    用途：
    - 多租户隔离基础
    - RLS策略通过site_id过滤
    - X-Site-Code头映射到site_id
    
    示例：
    - code: "NA", name: "North America"
    - code: "ASIA", name: "Asia Pacific"
    """
    site_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="站点唯一标识"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="站点代码（NA/ASIA）"
    )
    name = models.CharField(
        max_length=100,
        help_text="站点名称"
    )
    domain = models.CharField(
        max_length=255,
        unique=True,
        help_text="站点域名"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="站点激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sites'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'
    
    def __str__(self):
        return f"{self.code} - {self.name}"



