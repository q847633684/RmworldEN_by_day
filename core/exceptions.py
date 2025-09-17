"""
异常类定义模块
定义所有翻译相关的异常类
"""

class TranslationError(Exception):
    """翻译操作的基础异常类"""
    pass

class TranslationImportError(TranslationError):
    """导入相关错误"""
    pass

class ExportError(TranslationError):
    """导出相关错误"""
    pass 