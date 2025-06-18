"""
Day Translation 2 - 数据模型模块

提供统一的数据模型定义，包括：
- 异常类定义
- 翻译数据模型
- 配置数据模型
- 结果数据模型
"""

from .exceptions import *
from .translation_data import *
from .config_models import *
from .result_models import *

__all__ = [
    # 异常类
    'TranslationError', 'ConfigError', 'ImportError', 'ExportError',
    
    # 翻译数据模型
    'TranslationData', 'KeyedTranslation', 'DefInjectedTranslation',
    
    # 配置数据模型
    'CoreConfig', 'UserConfig', 'PathValidationResult',
    
    # 结果数据模型
    'ModProcessResult', 'OperationResult'
]
