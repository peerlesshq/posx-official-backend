"""
认证序列化器（SIWE钱包认证）

⭐ 功能：
- Nonce 生成
- SIWE 钱包认证
- 用户信息查询
"""
from rest_framework import serializers
from decimal import Decimal
from .models import User, Wallet


class NonceRequestSerializer(serializers.Serializer):
    """Nonce 请求序列化器"""
    
    # 无需参数，站点从 request.site 获取
    pass


class NonceResponseSerializer(serializers.Serializer):
    """Nonce 响应序列化器"""
    
    nonce = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="过期时间（秒）")
    issued_at = serializers.DateTimeField()


class WalletAuthRequestSerializer(serializers.Serializer):
    """钱包认证请求序列化器"""
    
    message = serializers.CharField(
        help_text="SIWE 消息（纯文本）"
    )
    signature = serializers.CharField(
        help_text="签名（hex字符串，带0x前缀）"
    )
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        help_text="推荐码（可选，仅新用户注册时使用）"
    )
    
    def validate_signature(self, value):
        """验证签名格式"""
        if not value.startswith('0x'):
            raise serializers.ValidationError("签名必须以 0x 开头")
        
        if len(value) < 130:  # 0x + 128 hex chars (65 bytes)
            raise serializers.ValidationError("签名长度不足")
        
        return value


class WalletAuthResponseSerializer(serializers.Serializer):
    """钱包认证响应序列化器"""
    
    user_id = serializers.UUIDField()
    wallet_address = serializers.CharField()
    referral_code = serializers.CharField()
    is_new_user = serializers.BooleanField(help_text="是否为新注册用户")
    email = serializers.EmailField(allow_null=True, required=False)


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    primary_wallet = serializers.SerializerMethodField()
    wallets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'user_id',
            'email',
            'referral_code',
            'is_active',
            'primary_wallet',
            'wallets_count',
            'created_at',
        ]
        read_only_fields = ['user_id', 'referral_code', 'created_at']
    
    def get_primary_wallet(self, obj):
        """获取主钱包"""
        wallet = obj.wallets.filter(is_primary=True).first()
        if wallet:
            return {
                'address': wallet.address,
                'created_at': wallet.created_at.isoformat()
            }
        return None
    
    def get_wallets_count(self, obj):
        """获取钱包数量"""
        return obj.wallets.count()


class WalletBindRequestSerializer(serializers.Serializer):
    """钱包绑定请求序列化器"""
    
    message = serializers.CharField()
    signature = serializers.CharField()
    is_primary = serializers.BooleanField(default=False)


class WalletSerializer(serializers.ModelSerializer):
    """钱包序列化器"""
    
    class Meta:
        model = Wallet
        fields = [
            'wallet_id',
            'address',
            'is_primary',
            'created_at',
        ]
        read_only_fields = ['wallet_id', 'address', 'created_at']


