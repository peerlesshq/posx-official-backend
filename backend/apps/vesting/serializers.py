"""
Vesting API 序列化器（Retool 对接）
"""
from decimal import Decimal
from rest_framework import serializers

from apps.vesting.models import VestingSchedule, VestingRelease


class VestingReleaseListSerializer(serializers.ModelSerializer):
    """
    VestingRelease 列表序列化器（Retool 专用）
    
    ⭐ 包含 Retool 需要的关联字段：
    - order_id
    - user_email
    - chain
    - token_decimals
    """
    
    # 关联字段
    order_id = serializers.UUIDField(
        source='schedule.allocation.order.order_id', 
        read_only=True
    )
    
    user_email = serializers.EmailField(
        source='schedule.allocation.order.buyer.email',  # ⭐ 从 buyer 读取
        read_only=True
    )
    
    # 链信息
    chain = serializers.CharField(
        source='schedule.allocation.order.chain',  # ⭐ 从 Order.chain 读取
        read_only=True,
        default='ETH'
    )
    
    token_decimals = serializers.SerializerMethodField()
    
    # 金额字段（字符串化，保持精度）
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        coerce_to_string=True
    )
    
    chain_amount = serializers.DecimalField(
        max_digits=24,
        decimal_places=6,
        coerce_to_string=True,
        allow_null=True
    )
    
    class Meta:
        model = VestingRelease
        fields = [
            'release_id',
            'schedule_id',
            'order_id',
            'user_email',
            'period_no',
            'release_date',
            'amount',
            'chain_amount',
            'status',
            'fireblocks_tx_id',
            'tx_hash',
            'unlocked_at',
            'released_at',
            'chain',
            'token_decimals',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_token_decimals(self, obj):
        """从 ChainAssetConfig 读取精度"""
        try:
            from apps.sites.models import ChainAssetConfig
            
            config = ChainAssetConfig.objects.get(
                site=obj.schedule.allocation.order.site,
                chain=obj.schedule.allocation.order.chain or 'ETH',
                token_symbol='POSX',
                is_active=True
            )
            return config.token_decimals
        except ChainAssetConfig.DoesNotExist:
            return 6  # 默认 6 位小数


class VestingScheduleSerializer(serializers.ModelSerializer):
    """VestingSchedule 序列化器"""
    
    allocation_id = serializers.UUIDField(
        source='allocation.allocation_id',
        read_only=True
    )
    
    total_tokens = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        coerce_to_string=True
    )
    
    total_periods = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = VestingSchedule
        fields = [
            'schedule_id',
            'allocation_id',
            'total_tokens',
            'total_periods',
            'cliff_months',
            'vesting_months',
            'tge_percent',
            'unlock_start_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = '__all__'

