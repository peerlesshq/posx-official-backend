"""
认证 URL 路由
"""
from django.urls import path
from . import views_auth

app_name = 'auth'

urlpatterns = [
    path('nonce/', views_auth.nonce, name='nonce'),
    path('wallet/', views_auth.wallet_auth, name='wallet-auth'),
    path('me/', views_auth.me, name='me'),
    path('wallet/bind/', views_auth.bind_wallet, name='bind-wallet'),
]


