"""
Day Translation 2 - 异常定义模块

定义系统中使用的自定义异常类。
"""

class TranslationError(Exception):
    """翻译过程中发生的异常"""
    pass

class ConfigError(Exception):
    """配置相关异常"""
    pass

class ImportError(Exception):
    """导入操作异常"""
    pass

class ExportError(Exception):
    """导出操作异常"""
    pass

class ValidationError(Exception):
    """数据验证异常"""
    pass

class ServiceError(Exception):
    """服务层异常"""
    pass
