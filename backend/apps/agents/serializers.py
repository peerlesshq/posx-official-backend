"""
代理序列化器
"""
from rest_framework import serializers


class AgentStructureNodeSerializer(serializers.Serializer):
    """代理结构节点序列化器"""
    
    agent_id = serializers.UUIDField()
    parent_id = serializers.UUIDField(allow_null=True)
    depth = serializers.IntegerField()
    path = serializers.CharField()
    level = serializers.IntegerField()
    total_customers = serializers.IntegerField()


class AgentCustomerSerializer(serializers.Serializer):
    """代理客户序列化器"""
    
    user_id = serializers.UUIDField()
    email = serializers.EmailField(allow_blank=True)
    referral_code = serializers.CharField()
    depth = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=18, decimal_places=6)
    last_order_at = serializers.DateTimeField(allow_null=True)


class AgentCustomerListSerializer(serializers.Serializer):
    """代理客户列表响应序列化器"""
    
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    customers = AgentCustomerSerializer(many=True)



