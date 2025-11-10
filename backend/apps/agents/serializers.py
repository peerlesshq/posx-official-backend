"""
Agent API 序列化器（Phase F）
"""
from decimal import Decimal
from rest_framework import serializers
from django.conf import settings

from apps.agents.models import (
    AgentProfile,
    WithdrawalRequest,
    CommissionStatement,
    AgentTree,
    AgentStats
)


class AgentProfileSerializer(serializers.ModelSerializer):
    """Agent 资料序列化器"""
    
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    site_code = serializers.CharField(source='site.code', read_only=True)
    
    # Decimal 字符串化（2位小数）
    balance_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    total_earned_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    total_withdrawn_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    
    class Meta:
        model = AgentProfile
        fields = [
            'profile_id', 'user_id', 'user_email', 'site_code',
            'agent_level', 'balance_usd', 'total_earned_usd',
            'total_withdrawn_usd', 'kyc_status', 'kyc_submitted_at',
            'kyc_approved_at', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'profile_id', 'balance_usd', 'total_earned_usd',
            'total_withdrawn_usd', 'created_at', 'updated_at'
        ]


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """提现申请序列化器"""
    
    agent_email = serializers.EmailField(
        source='agent_profile.user.email',
        read_only=True
    )
    amount_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True
    )
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'request_id', 'agent_email', 'amount_usd', 'status',
            'withdrawal_method', 'account_info', 'admin_note',
            'approved_by', 'approved_at', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'request_id', 'status', 'admin_note', 'approved_by',
            'approved_at', 'completed_at', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'account_info': {'write_only': True}  # 敏感信息不返回
        }
    
    def validate_amount_usd(self, value):
        """验证提现金额"""
        # 最小提现金额
        min_amount = Decimal(settings.WITHDRAWAL_MIN_AMOUNT)
        if value < min_amount:
            raise serializers.ValidationError(
                f"最小提现金额为 ${min_amount}"
            )
        return value
    
    def validate(self, attrs):
        """验证余额充足"""
        user = self.context['request'].user
        amount = attrs['amount_usd']
        
        # 获取 Agent Profile
        try:
            profile = AgentProfile.objects.get(
                user=user,
                site=self.context['request'].site
            )
        except AgentProfile.DoesNotExist:
            raise serializers.ValidationError("Agent profile not found")
        
        # 验证余额
        if profile.balance_usd < amount:
            raise serializers.ValidationError(
                f"余额不足。可用余额：${profile.balance_usd}"
            )
        
        # 添加 profile 到 validated_data
        attrs['agent_profile'] = profile
        
        return attrs


class CommissionStatementSerializer(serializers.ModelSerializer):
    """对账单序列化器"""
    
    agent_email = serializers.EmailField(
        source='agent_profile.user.email',
        read_only=True
    )
    
    # Decimal 字符串化
    total_commissions_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    paid_commissions_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    pending_commissions_usd = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    
    class Meta:
        model = CommissionStatement
        fields = [
            'statement_id', 'agent_email', 'period_start', 'period_end',
            'total_commissions_usd', 'paid_commissions_usd',
            'pending_commissions_usd', 'order_count', 'customer_count',
            'pdf_url', 'generated_at'
        ]
        read_only_fields = '__all__'


class AgentStatsSerializer(serializers.ModelSerializer):
    """代理统计序列化器"""
    
    total_sales = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    total_commissions = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True
    )
    
    class Meta:
        model = AgentStats
        fields = [
            'stat_id', 'agent', 'total_customers', 'direct_customers',
            'total_sales', 'total_commissions', 'last_order_at', 'updated_at'
        ]
        read_only_fields = '__all__'


class AgentStructureNodeSerializer(serializers.Serializer):
    """代理下线结构节点序列化器"""
    
    agent_id = serializers.UUIDField()
    parent_id = serializers.UUIDField(allow_null=True)
    depth = serializers.IntegerField()
    path = serializers.CharField()
    total_customers = serializers.IntegerField()


class AgentCustomerSerializer(serializers.Serializer):
    """代理客户节点序列化器"""
    
    user_id = serializers.UUIDField()
    email = serializers.EmailField()
    referral_code = serializers.CharField()
    depth = serializers.IntegerField()
    total_sales = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        coerce_to_string=True
    )
    last_order_at = serializers.DateTimeField(allow_null=True)


class AgentCustomerListSerializer(serializers.Serializer):
    """代理客户列表序列化器（带分页）"""
    
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    customers = AgentCustomerSerializer(many=True)