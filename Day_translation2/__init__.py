"""
Day Translation 2 - 新一代翻译工具

一个重构的、模块化的RimWorld模组翻译工具，提供：
- 统一的配置管理系统
- 智能的用户交互界面  
- 模块化的核心业务逻辑
- 完整的服务层架构
- 强大的工具集合
- 规范的数据模型

版本: 2.0.0
作者: Day Translation Team
"""

__version__ = "2.0.0"
__author__ = "Day Translation Team"

# 主要模块导入
from .config import get_config, UnifiedConfig
from .interaction import UnifiedInteractionManager
from .models import (
    TranslationError, ConfigError, ImportError, ExportError,
    TranslationData, KeyedTranslation, DefInjectedTranslation,
    OperationResult, ModProcessResult
)

__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    
    # 配置管理
    'get_config',
    'UnifiedConfig',
    
    # 交互管理
    'UnifiedInteractionManager',
    
    # 异常类
    'TranslationError',
    'ConfigError', 
    'ImportError',
    'ExportError',
    
    # 数据模型
    'TranslationData',
    'KeyedTranslation',
    'DefInjectedTranslation',
    'OperationResult',
    'ModProcessResult'
]
