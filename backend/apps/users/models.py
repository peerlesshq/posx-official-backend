"""
User模型 - 全局表（不受RLS限制）
用户认证支持双模式：Auth0（Email/Passkey）+ 钱包地址
"""
import uuid
from django.db import models


class User(models.Model):
    """
    用户模型（全局）
    
    认证方式：
    - auth0_sub: Auth0统一登录（Email/Passkey）
    - wallet_address: 主钱包地址（通过Wallet关联）
    
    推荐系统：
    - referral_code: 格式 {SITE_CODE}-{RANDOM}
    - referrer: 推荐人（自关联）
    """
    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="用户唯一标识"
    )
    auth0_sub = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Auth0 Subject ID（Email/Passkey登录）"
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="邮箱地址"
    )
    referral_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="推荐码（格式：NA-ABC123）"
    )
    referrer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        help_text="推荐人"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="账户激活状态"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['referral_code']),
            models.Index(fields=['email']),
            models.Index(fields=['auth0_sub']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email or self.auth0_sub or self.user_id}"


class Wallet(models.Model):
    """
    钱包模型（全局）
    
    ⚠️ 重要：
    - address统一存储为lowercase
    - 唯一索引通过LOWER(address)创建（见迁移）
    - 一个用户可以绑定多个钱包
    - is_primary标记主钱包
    """
    wallet_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="钱包唯一标识"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wallets',
        help_text="钱包所有者"
    )
    address = models.CharField(
        max_length=42,
        help_text="钱包地址（统一存储lowercase）"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="是否为主钱包"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wallets'
        indexes = [
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['created_at']),
        ]
        # ⚠️ LOWER(address)唯一索引在迁移中通过CONCURRENTLY创建
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
    
    def save(self, *args, **kwargs):
        """保存前统一转换为lowercase"""
        if self.address:
            self.address = self.address.lower()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.address[:10]}...{'(主)' if self.is_primary else ''}"



