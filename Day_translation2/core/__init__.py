"""
Day Translation 2 - 核心业务逻辑模块

提供翻译处理的核心功能，包括：
- 翻译门面类 (TranslationFacade)
- 模板管理器 (TemplateManager)
- 数据提取器 (extractors)
- 数据导入导出器 (importers, exporters)
- 模板生成器 (generators)
- 主流程控制器 (main)
"""

from .translation_facade import TranslationFacade

__all__ = [
    'TranslationFacade'
]
