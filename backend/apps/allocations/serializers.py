"""
Allocation Serializers
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Allocation


class AllocationSerializer(serializers.ModelSerializer):
    """
    分配记录序列化器
    
    用于用户查看代币分配详情
    """
    order_id = serializers.UUIDField(source='order.order_id', read_only=True)
    site_id = serializers.UUIDField(source='order.site_id', read_only=True)
    buyer_id = serializers.UUIDField(source='order.buyer_id', read_only=True)
    
    # 计算字段
    pending_tokens = serializers.SerializerMethodField()
    release_progress = serializers.SerializerMethodField()
    
    # 订单信息（可选展开）
    order_status = serializers.CharField(source='order.status', read_only=True)
    order_created_at = serializers.DateTimeField(source='order.created_at', read_only=True)
    
    class Meta:
        model = Allocation
        fields = [
            'allocation_id',
            'order_id',
            'site_id',
            'buyer_id',
            'wallet_address',
            'token_amount',
            'released_tokens',
            'pending_tokens',
            'release_progress',
            'status',
            'order_status',
            'order_created_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_pending_tokens(self, obj):
        """计算待释放代币数量"""
        pending = obj.token_amount - obj.released_tokens
        return str(pending)
    
    def get_release_progress(self, obj):
        """计算释放进度（百分比）"""
        if obj.token_amount == 0:
            return "0.00"
        progress = (obj.released_tokens / obj.token_amount) * 100
        return f"{progress:.2f}"


class AllocationListSerializer(serializers.ModelSerializer):
    """
    分配记录列表序列化器（简化版）
    """
    order_id = serializers.UUIDField(source='order.order_id', read_only=True)
    pending_tokens = serializers.SerializerMethodField()
    release_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Allocation
        fields = [
            'allocation_id',
            'order_id',
            'wallet_address',
            'token_amount',
            'released_tokens',
            'pending_tokens',
            'release_progress',
            'status',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_pending_tokens(self, obj):
        """计算待释放代币数量"""
        pending = obj.token_amount - obj.released_tokens
        return str(pending)
    
    def get_release_progress(self, obj):
        """计算释放进度（百分比）"""
        if obj.token_amount == 0:
            return "0.00"
        progress = (obj.released_tokens / obj.token_amount) * 100
        return f"{progress:.2f}"


class AllocationBalanceSerializer(serializers.Serializer):
    """
    代币余额统计序列化器
    """
    total_tokens = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="总代币数量"
    )
    released_tokens = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="已释放代币"
    )
    pending_tokens = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="待释放代币"
    )
    active_allocations = serializers.IntegerField(
        help_text="活跃分配记录数"
    )
    completed_allocations = serializers.IntegerField(
        help_text="已完成分配记录数"
    )
    release_progress = serializers.CharField(
        help_text="总体释放进度（百分比）"
    )

