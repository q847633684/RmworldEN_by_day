"""
Day Translation 包初始化
"""

# 直接使用新配置系统
from .user_config import UserConfigManager
from .core.translation_facade import TranslationFacade

__all__ = ["UserConfigManager", "TranslationFacade"]
