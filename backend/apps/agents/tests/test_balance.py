"""
Agent 余额服务测试（Phase F）
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError

from apps.agents.models import AgentProfile
from apps.agents.services.balance import (
    get_or_create_agent_profile,
    update_balance_on_commission_paid,
    deduct_balance_for_withdrawal,
    refund_balance_for_withdrawal,
    complete_withdrawal
)


@pytest.mark.django_db
class TestAgentBalance:
    """测试 Agent 余额管理"""
    
    def test_get_or_create_agent_profile(self, user, site):
        """测试创建 Agent Profile"""
        profile = get_or_create_agent_profile(user, site)
        
        assert profile.user == user
        assert profile.site == site
        assert profile.balance_usd == Decimal('0')
        assert profile.agent_level == 'bronze'
        assert profile.is_active == True
    
    def test_update_balance_on_commission_paid(self, commission_paid):
        """测试佣金结算后余额更新"""
        commission = commission_paid
        initial_balance = Decimal('0')
        
        # 更新余额
        profile = update_balance_on_commission_paid(commission)
        
        # 验证
        assert profile.balance_usd == commission.commission_amount_usd
        assert profile.total_earned_usd == commission.commission_amount_usd
    
    def test_deduct_balance_for_withdrawal_success(self, agent_profile_with_balance):
        """测试余额充足时扣减成功"""
        profile = agent_profile_with_balance
        profile.balance_usd = Decimal('100.00')
        profile.save()
        
        # 扣减余额
        result = deduct_balance_for_withdrawal(profile, Decimal('50.00'))
        
        # 验证
        assert result == True
        profile.refresh_from_db()
        assert profile.balance_usd == Decimal('50.00')
    
    def test_deduct_balance_insufficient(self, agent_profile_with_balance):
        """测试余额不足时扣减失败"""
        profile = agent_profile_with_balance
        profile.balance_usd = Decimal('30.00')
        profile.save()
        
        # 扣减余额
        result = deduct_balance_for_withdrawal(profile, Decimal('50.00'))
        
        # 验证
        assert result == False
        profile.refresh_from_db()
        assert profile.balance_usd == Decimal('30.00')  # 未扣减
    
    def test_refund_balance_for_withdrawal(self, agent_profile):
        """测试提现拒绝后返还余额"""
        profile = agent_profile
        profile.balance_usd = Decimal('50.00')
        profile.save()
        
        # 返还余额
        refund_balance_for_withdrawal(profile, Decimal('20.00'), 'withdrawal_rejected')
        
        # 验证
        profile.refresh_from_db()
        assert profile.balance_usd == Decimal('70.00')
    
    def test_balance_non_negative_constraint(self, agent_profile):
        """测试余额非负约束"""
        profile = agent_profile
        
        # 尝试设置负余额
        profile.balance_usd = Decimal('-10.00')
        
        with pytest.raises(IntegrityError):
            profile.save()
    
    def test_concurrent_balance_update(self, agent_profile):
        """测试并发余额更新（悲观锁）"""
        # TODO: 使用多线程测试并发安全性
        pass

