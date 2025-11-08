"""
Auth0 JWT 认证模块

⭐ 安全特性：
- 从 Authorization: Bearer <token> 解析 JWT
- 验证 JWKS 签名（RS256）
- 验证 issuer、audience、expiration
- 自动映射/创建本地用户（基于 auth0_sub）
- JWKS 缓存（减少请求）

环境变量：
- AUTH0_DOMAIN: Auth0域名
- AUTH0_AUDIENCE: API标识符
- AUTH0_ISSUER: 发行者URL
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import authentication, exceptions
from apps.users.models import User

logger = logging.getLogger(__name__)


class Auth0JWTAuthentication(authentication.BaseAuthentication):
    """
    Auth0 JWT 认证类

    流程：
    1. 从请求头提取 Bearer token
    2. 从 JWKS 端点获取公钥（带缓存）
    3. 验证 JWT 签名和声明
    4. 根据 sub 映射/创建本地用户
    """

    def authenticate(self, request):
        """
        认证请求

        Returns:
            (user, token): 认证成功
            None: 无需认证（允许匿名）

        Raises:
            AuthenticationFailed: 认证失败
        """
        # 提取 token
        token = self._extract_token(request)
        if not token:
            return None  # 无 token，允许其他认证机制

        # 解码与验证
        try:
            payload = self._decode_and_verify_token(token)
        except Exception as e:
            logger.warning(f"JWT verification failed: {e}")
            raise exceptions.AuthenticationFailed(f"Invalid token: {e}")

        # 提取 sub
        auth0_sub = payload.get("sub")
        if not auth0_sub:
            raise exceptions.AuthenticationFailed("Token missing 'sub' claim")

        # 获取或创建用户
        user = self._get_or_create_user(auth0_sub, payload)

        return (user, token)

    def _extract_token(self, request) -> Optional[str]:
        """从 Authorization 头提取 Bearer token"""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        return auth_header[7:]  # 去掉 "Bearer " 前缀

    def _decode_and_verify_token(self, token: str) -> dict:
        """
        解码并验证 JWT token

        验证项：
        - 签名（RS256）
        - issuer
        - audience
        - expiration

        Returns:
            payload: 解码后的声明
        """
        # 获取 JWKS 公钥
        signing_key = self._get_signing_key(token)

        # 解码
        try:
            # 先解码查看 token 内容（用于调试）
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            token_issuer = unverified_payload.get("iss")
            token_audience = unverified_payload.get("aud")

            logger.debug(
                f"Token issuer: {token_issuer}, Expected: {settings.AUTH0_ISSUER}"
            )
            logger.debug(
                f"Token audience: {token_audience}, Expected: {settings.AUTH0_AUDIENCE}"
            )

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=settings.AUTH0_ALGORITHMS,
                audience=settings.AUTH0_AUDIENCE,
                issuer=settings.AUTH0_ISSUER,
                leeway=settings.AUTH0_JWT_LEEWAY,
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidAudienceError as e:
            logger.warning(
                f"Invalid audience: token={token_audience}, expected={settings.AUTH0_AUDIENCE}"
            )
            raise exceptions.AuthenticationFailed("Invalid audience")
        except jwt.InvalidIssuerError as e:
            logger.warning(
                f"Invalid issuer: token={token_issuer}, expected={settings.AUTH0_ISSUER}"
            )
            raise exceptions.AuthenticationFailed("Invalid issuer")
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed("Token decode error")
        except Exception as e:
            logger.error(f"Token validation failed: {e}", exc_info=True)
            raise exceptions.AuthenticationFailed(f"Token validation failed: {e}")

        return payload

    def _get_signing_key(self, token: str) -> str:
        """
        从 JWKS 端点获取签名公钥（带缓存）

        流程：
        1. 解析 token header 获取 kid
        2. 从缓存或远程获取 JWKS
        3. 匹配 kid 返回公钥
        """
        # 解析 header（不验证）
        try:
            header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed("Invalid token header")

        kid = header.get("kid")
        if not kid:
            raise exceptions.AuthenticationFailed("Token missing 'kid' in header")

        # 获取 JWKS
        jwks = self._get_jwks()

        # 匹配 kid
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # 构造 PyJWT 格式的公钥
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)

        raise exceptions.AuthenticationFailed(f"Public key not found for kid: {kid}")

    def _get_jwks(self) -> dict:
        """
        获取 JWKS（JSON Web Key Set）

        ⭐ 缓存策略：
        - TTL: AUTH0_JWKS_CACHE_TTL（默认1小时）
        - 失败时不缓存，快速返回 401
        """
        cache_key = "auth0_jwks"

        # 尝试缓存
        jwks = cache.get(cache_key)
        if jwks:
            logger.debug("JWKS cache hit")
            return jwks

        # 从 Auth0 获取
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"

        try:
            response = requests.get(jwks_url, timeout=5)
            response.raise_for_status()
            jwks = response.json()
        except requests.RequestException as e:
            # ⚠️ 快速失败，返回 401（不静默降级）
            logger.error(
                f"AUTH.JWKS_FETCH_FAILED: {e}. "
                f"URL={jwks_url}. "
                "请检查网络连接或 Auth0 配置。"
            )
            raise exceptions.AuthenticationFailed(
                "Unable to verify token signature. Auth0 JWKS unavailable."
            )

        # 缓存
        cache.set(cache_key, jwks, settings.AUTH0_JWKS_CACHE_TTL)
        logger.debug("JWKS cached")

        return jwks

    def _get_or_create_user(self, auth0_sub: str, payload: dict) -> User:
        """
        根据 auth0_sub 获取或创建本地用户

        Args:
            auth0_sub: Auth0 subject ID
            payload: JWT payload（可能包含 email 等）

        Returns:
            User 实例
        """
        # 查询现有用户
        try:
            user = User.objects.get(auth0_sub=auth0_sub, is_active=True)
            return user
        except User.DoesNotExist:
            pass

        # 创建新用户
        email = payload.get("email")

        # 生成唯一推荐码（重试直到唯一）
        max_retries = 10
        for attempt in range(max_retries):
            referral_code = self._generate_referral_code()
            if not User.objects.filter(referral_code=referral_code).exists():
                break
            if attempt == max_retries - 1:
                raise ValueError(
                    "Failed to generate unique referral code after multiple attempts"
                )

        try:
            user = User.objects.create(
                auth0_sub=auth0_sub,
                email=email,
                referral_code=referral_code,
                is_active=True,
            )
            logger.info(f"Created new user from Auth0: {auth0_sub}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {e}", exc_info=True)
            raise

    def _generate_referral_code(self) -> str:
        """
        生成唯一推荐码

        格式: G-<8位随机>（总长度10，符合20字符限制）
        后续可改为站点特定：NA-ABC123
        """
        import random
        import string

        # 生成8位随机字符串
        random_str = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )

        return f"G-{random_str}"  # 总长度: 10 字符


class Auth0JWTAuthenticationOptional(Auth0JWTAuthentication):
    """
    可选的 Auth0 JWT 认证

    用于允许匿名访问的端点（如公开查询）
    不会抛出异常，返回 None 即可
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except exceptions.AuthenticationFailed:
            return None  # 允许匿名
