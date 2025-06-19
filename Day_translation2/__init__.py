"""
Day Translation 2 - 游戏本地化翻译工具 (全新架构)

新一代游戏本地化翻译工具，采用清洁架构设计。
专注于RimWorld等游戏的中英文本地化翻译。

架构特点:
- 分层设计: models/core/services/utils/interaction/config
- 类型安全: 完整的类型注解
- 异常处理: 具体异常类型+详细上下文
- 测试覆盖: 80%+覆盖率目标
- 性能优化: 多线程+批量处理
"""

__version__ = "2.0.0"
__author__ = "Day汉化项目组"
__description__ = "游戏本地化翻译工具 - 全新架构版本"


# 延迟导入，避免循环依赖
def get_translation_facade():
    """获取翻译门面实例"""
    from .core.translation_facade import TranslationFacade

    return TranslationFacade


# 导入主要组件
from .models.exceptions import (ProcessingError, TranslationError,
                                ValidationError)
from .models.result_models import (OperationResult, OperationStatus,
                                   OperationType)

# 主要功能导出
__all__ = [
    "get_translation_facade",
    "__version__",
    "TranslationError",
    "ValidationError",
    "ProcessingError",
    "OperationResult",
    "OperationStatus",
    "OperationType",
]
