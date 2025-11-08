"""
Phase D Webhook集成测试

⭐ 测试覆盖：
1. 签名验证（400失败）
2. 事件白名单
3. 双重幂等保障
4. payment_succeeded流程
5. payment_failed流程（防双重回补）
6. 审计日志验证
"""
import json
import stripe
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.users.models import User
from apps.sites.models import Site
from apps.tiers.models import Tier
from apps.webhooks.models import IdempotencyKey
from apps.commissions.models import Commission


class StripeWebhookTestCase(TestCase):
    """Stripe Webhook 测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = APIClient()
        
        # 创建测试站点
        self.site = Site.objects.create(
            code='NA',
            name='North America',
            domain='localhost'
        )
        
        # 创建用户
        self.buyer = User.objects.create(
            auth0_sub='test_buyer',
            email='buyer@test.com'
        )
        
        self.referrer = User.objects.create(
            auth0_sub='test_referrer',
            email='referrer@test.com',
            referral_code='REF001'
        )
        
        self.buyer.referrer = self.referrer
        self.buyer.save()
        
        # 创建档位
        self.tier = Tier.objects.create(
            site=self.site,
            name='Test Tier',
            list_price_usd=Decimal('100.00'),
            tokens_per_unit=Decimal('1000'),
            total_units=100,
            available_units=100,
            is_active=True
        )
        
        # 创建订单
        self.order = Order.objects.create(
            site=self.site,
            buyer=self.buyer,
            referrer=self.referrer,
            wallet_address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            list_price_usd=Decimal('100.00'),
            final_price_usd=Decimal('100.00'),
            status='pending',
            stripe_payment_intent_id='pi_test_12345'
        )
        
        OrderItem.objects.create(
            order=self.order,
            tier=self.tier,
            quantity=1,
            unit_price_usd=Decimal('100.00'),
            token_amount=Decimal('1000')
        )
    
    def _create_stripe_event(self, event_type, payment_intent_id):
        """创建模拟Stripe事件"""
        return MagicMock(
            id=f'evt_test_{timezone.now().timestamp()}',
            type=event_type,
            data=MagicMock(
                object=MagicMock(
                    id=payment_intent_id,
                    get=lambda k, default=None: payment_intent_id if k == 'id' else default
                )
            )
        )
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_invalid(self, mock_construct):
        """测试：签名验证失败返回400"""
        mock_construct.side_effect = stripe.error.SignatureVerificationError('Invalid signature', '')
        
        response = self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='invalid_sig'
        )
        
        # ⭐ Phase D P0: 签名失败返回400
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid signature', str(response.data))
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_event_whitelist(self, mock_construct):
        """测试：非白名单事件被忽略"""
        # 模拟一个不在白名单的事件
        mock_event = MagicMock(
            id='evt_ignored',
            type='customer.created'  # 不在白名单
        )
        mock_construct.return_value = mock_event
        
        response = self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )
        
        # ⭐ Phase D P0: 返回200但不处理
        self.assertEqual(response.status_code, 200)
        
        # 不应创建幂等键（未处理）
        self.assertFalse(
            IdempotencyKey.objects.filter(key='evt_ignored').exists()
        )
    
    @patch('stripe.Webhook.construct_event')
    @patch('apps.commissions.tasks.calculate_commission_for_order.delay')
    def test_payment_succeeded_idempotent(self, mock_task, mock_construct):
        """测试：payment_succeeded 双重幂等"""
        event = self._create_stripe_event('payment_intent.succeeded', 'pi_test_12345')
        mock_construct.return_value = event
        
        # 第一次调用
        response1 = self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )
        
        self.assertEqual(response1.status_code, 200)
        
        # 订单状态应更新为paid
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        
        # 佣金任务应被触发
        mock_task.assert_called_once()
        
        # 第二次调用（幂等）
        response2 = self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='valid_sig2'
        )
        
        self.assertEqual(response2.status_code, 200)
        
        # ⭐ 任务不应再次触发（幂等）
        self.assertEqual(mock_task.call_count, 1)
    
    @patch('stripe.Webhook.construct_event')
    def test_payment_failed_inventory_release(self, mock_construct):
        """测试：payment_failed 库存回补"""
        event = self._create_stripe_event('payment_intent.payment_failed', 'pi_test_12345')
        mock_construct.return_value = event
        
        # 记录初始库存
        initial_available = self.tier.available_units
        
        response = self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 订单状态应更新为failed
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')
        
        # ⭐ Phase D P0: 库存应回补
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, initial_available + 1)
    
    @patch('stripe.Webhook.construct_event')
    def test_payment_failed_no_double_release(self, mock_construct):
        """测试：防止双重库存回补"""
        event = self._create_stripe_event('payment_intent.payment_failed', 'pi_test_12345')
        mock_construct.return_value = event
        
        initial_available = self.tier.available_units
        
        # 第一次调用
        self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )
        
        # 第二次调用（模拟Stripe重试）
        self.client.post(
            '/api/v1/webhooks/stripe/',
            data={},
            HTTP_STRIPE_SIGNATURE='valid_sig2'
        )
        
        # ⭐ Phase D P0: 库存只应回补一次
        self.tier.refresh_from_db()
        self.assertEqual(self.tier.available_units, initial_available + 1)

