"""
Webhook URLs
"""
from django.urls import path

from apps.webhooks import views

urlpatterns = [
    path('stripe/', views.stripe_webhook_view, name='stripe_webhook'),
]
