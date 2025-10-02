"""
翻译核心模块
包含统一翻译器和相关核心组件
"""

from .unified_translator import UnifiedTranslator
from .translator_factory import TranslatorFactory

# 翻译配置已迁移到新配置系统

__all__ = [
    "UnifiedTranslator",
    "TranslatorFactory",
]
