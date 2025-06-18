"""
Day Translation 2 - 核心业务层

包含系统的核心业务逻辑和处理流程。
实现主要的翻译操作: 提取、转换、导入、导出。

使用延迟导入模式，避免循环依赖。
"""

# 延迟导入函数
def get_translation_facade():
    """获取翻译门面类"""
    from .translation_facade import TranslationFacade
    return TranslationFacade

def get_template_manager():
    """获取模板管理器"""
    from .template_manager import TemplateManager
    return TemplateManager

def get_extractors():
    """获取数据提取器"""
    from . import extractors
    return extractors

def get_importers():
    """获取数据导入器"""
    from . import importers
    return importers

def get_exporters():
    """获取数据导出器"""
    from . import exporters
    return exporters

__all__ = [
    'get_translation_facade',
    'get_template_manager',
    'get_extractors',
    'get_importers', 
    'get_exporters'
]
