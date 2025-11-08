"""
Core应用配置

⭐ 启动时校验：
- Auth0 配置完整性
- 打印配置摘要（去敏）
"""
import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = '核心功能'
    
    def ready(self):
        """应用启动时执行"""
        self._validate_auth0_config()
    
    def _validate_auth0_config(self):
        """
        验证 Auth0 配置完整性
        
        ⚠️ 缺少必要配置时警告（不阻止启动，允许本地开发）
        """
        required = getattr(settings, 'AUTH0_REQUIRED_SETTINGS', [])
        missing = []
        
        for setting_name in required:
            value = getattr(settings, setting_name, '')
            if not value:
                missing.append(setting_name)
        
        if missing:
            logger.warning(
                f"⚠️ Auth0 配置缺失: {', '.join(missing)}. "
                "JWT 认证将失败，请检查环境变量。"
            )
        else:
            # 打印配置摘要（去敏）
            domain = getattr(settings, 'AUTH0_DOMAIN', '')
            audience = getattr(settings, 'AUTH0_AUDIENCE', '')
            
            # 去敏处理：只显示域名前缀
            domain_display = domain.split('.')[0] + '.***' if domain else 'NOT_SET'
            audience_display = audience[:20] + '...' if len(audience) > 20 else audience
            
            logger.info(
                f"✅ Auth0 配置已加载: "
                f"Domain={domain_display}, "
                f"Audience={audience_display}, "
                f"JWKS_TTL={getattr(settings, 'AUTH0_JWKS_CACHE_TTL', 3600)}s"
            )



