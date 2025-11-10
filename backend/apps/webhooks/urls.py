"""
Webhook URLs
"""
from django.urls import path

from apps.webhooks import views

urlpatterns = [
    # Stripe webhook
    path('stripe/', views.stripe_webhook_view, name='stripe_webhook'),
    
    # ⭐ Phase E: Fireblocks webhook
    path('fireblocks/', views.FireblocksWebhookView.as_view(), name='fireblocks_webhook'),
    
    # ⭐ Retool 对接：Webhook 重放
    path('replay/', views.replay_webhook_event, name='webhook-replay'),
]
