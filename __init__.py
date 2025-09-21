"""
Day Translation 包初始化
"""

from .utils.config import TranslationConfig

# UnifiedFilterRules 已整合到 utils.config 中
from .core.translation_facade import TranslationFacade

__all__ = ["TranslationConfig", "TranslationFacade"]
