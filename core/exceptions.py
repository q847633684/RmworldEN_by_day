"""
核心异常类定义
定义翻译流程中使用的自定义异常
"""


class TranslationError(Exception):
    """翻译相关异常基类"""

    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class TranslationImportError(TranslationError):
    """翻译导入异常"""

    def __init__(self, message: str, details: str = None):
        super().__init__(f"导入失败: {message}", details)


class ExportError(TranslationError):
    """导出异常"""

    def __init__(self, message: str, details: str = None):
        super().__init__(f"导出失败: {message}", details)


class ConfigurationError(TranslationError):
    """配置异常"""

    def __init__(self, message: str, details: str = None):
        super().__init__(f"配置错误: {message}", details)


class ValidationError(TranslationError):
    """验证异常"""

    def __init__(self, message: str, details: str = None):
        super().__init__(f"验证失败: {message}", details)
