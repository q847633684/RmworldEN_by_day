"""
Day Translation 框架 - RimWorld 模组翻译工具

提供完整的模组翻译工作流：
1. 内容提取 - 从模组文件提取可翻译文本
2. 智能过滤 - 自动识别需要翻译的内容
3. 模板生成 - 生成标准翻译文件模板
4. 机器翻译 - 支持多种翻译引擎
5. 导入导出 - CSV 格式数据交换
6. 语料生成 - 创建平行语料库
"""

__version__ = "2.0.0"
__author__ = "Day Translation Team"

# 导入主要组件
from .core.main import TranslationFacade, main, setup_logging
from .utils.config import TranslationConfig
from .utils.filter_config import UnifiedFilterRules

# 导出主要接口
__all__ = [
    'TranslationFacade',
    'main', 
    'setup_logging',
    'TranslationConfig',
    'UnifiedFilterRules',
    '__version__'
]
