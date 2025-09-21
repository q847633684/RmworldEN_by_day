"""
RimWorld 翻译提取模块

本模块提供完整的 RimWorld 模组翻译提取功能，包括：
- 从 Defs 目录扫描可翻译内容
- 从 DefInjected/Keyed 目录提取现有翻译
- 智能合并和冲突处理
- 多种模板结构导出
- CSV 格式数据导出

主要组件：
- core.extractors: 翻译内容提取器
- core.exporters: 翻译文件导出器
- core.filters: 内容过滤器
- utils.merger: 智能合并器
- workflow: 工作流程模块

新架构特性：
- 深度模块化设计，职责单一
- 基础抽象类，易于扩展
- 统一的接口和错误处理
- 完整的日志和性能监控

注意：为避免循环导入，模块内部采用延迟导入策略
"""

# 导入核心功能
from .core.extractors import (
    BaseExtractor,
    DefInjectedExtractor,
    KeyedExtractor,
    DefsScanner,
)

from .core.exporters import (
    BaseExporter,
    DefInjectedExporter,
    KeyedExporter,
)

from .core.filters import (
    ContentFilter,
    is_non_text,
    is_valid_translation_text,
    normalize_text,
)

from .utils import SmartMerger
from .workflow import TemplateManager, InteractionManager, handle_extract


__all__ = [
    # 核心提取器
    "BaseExtractor",
    "DefInjectedExtractor",
    "KeyedExtractor",
    "DefsScanner",
    # 核心导出器
    "BaseExporter",
    "DefInjectedExporter",
    "KeyedExporter",
    # 过滤器
    "ContentFilter",
    "is_non_text",
    "is_valid_translation_text",
    "normalize_text",
    # 工具
    "SmartMerger",
    # 工作流程
    "TemplateManager",
    "InteractionManager",
    "handle_extract",
]
