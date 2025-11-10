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


class ChainAssetConfig(models.Model):
    """
    链/资产配置表
    
    用途:
    - 配置不同链的资产小数位
    - 配置Fireblocks Asset ID
    - 支持多链多资产
    """
    config_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    
    # 链信息
    chain = models.CharField(
        max_length=20,
        choices=[
            ('ETH', 'Ethereum'),
            ('POLYGON', 'Polygon'),
            ('BSC', 'BSC'),
            ('TRON', 'TRON'),
        ]
    )
    
    # 资产信息
    token_symbol = models.CharField(max_length=10)
    token_decimals = models.IntegerField()
    
    # Fireblocks配置
    fireblocks_asset_id = models.CharField(max_length=50)
    fireblocks_vault_id = models.CharField(max_length=10, default='0')
    
    # 地址校验类型
    address_type = models.CharField(
        max_length=20,
        choices=[
            ('EVM', 'EVM (0x...)'),
            ('TRON', 'TRON (Base58)'),
        ],
        default='EVM'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chain_asset_configs'
        unique_together = ['site', 'chain', 'token_symbol']
        indexes = [
            models.Index(fields=['site', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.chain} {self.token_symbol} ({self.token_decimals} decimals)"



