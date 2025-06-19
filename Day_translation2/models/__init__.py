"""
Day Translation 2 - 数据模型层

定义系统中使用的所有数据类型、异常类和结果模型。
遵循数据驱动设计原则，确保类型安全和数据完整性。

使用延迟导入模式，避免循环依赖问题。
"""

# 版本信息
__version__ = "2.0.0"


# 延迟导入函数
def get_exceptions():
    """获取异常类"""
    from . import exceptions

    return exceptions


def get_result_models():
    """获取结果模型"""
    from . import result_models

    return result_models


def get_translation_data():
    """获取翻译数据模型"""
    from . import translation_data

    return translation_data


# 主要接口
__all__ = ["get_exceptions", "get_result_models", "get_translation_data"]
