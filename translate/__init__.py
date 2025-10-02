"""
统一翻译模块
提供多种翻译方式的统一接口
"""

from .core.unified_translator import UnifiedTranslator
from .core.translator_factory import TranslatorFactory

# 翻译配置已迁移到新配置系统

__all__ = [
    "UnifiedTranslator",
    "TranslatorFactory",
]
