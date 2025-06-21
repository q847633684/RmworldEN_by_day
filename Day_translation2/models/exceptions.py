"""
Day Translation 2 - 异常定义模块

定义项目中使用的所有异常类，提供具体的错误类型和上下文信息。
遵循提示文件标准：使用具体异常类型，记录详细错误上下文。
"""

from typing import Any, Dict, List, Optional


class TranslationError(Exception):
    """翻译操作的基础异常类

    所有翻译相关的异常都应该继承这个基类。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> None:
        """初始化翻译异常

        Args:
            message: 错误消息
            context: 错误上下文信息
            operation: 操作名称
            stage: 阶段名称
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.operation = operation
        self.stage = stage

    def __str__(self) -> str:
        """返回格式化的错误信息"""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (上下文: {context_str})"
        return self.message


class ConfigError(TranslationError):
    """配置相关错误

    配置文件读取、解析或验证失败时抛出。
    """

    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None,
    ) -> None:
        """初始化配置错误

        Args:
            message: 错误消息
            config_path: 配置文件路径
            config_key: 出错的配置键
            config_value: 配置值
        """
        context = {}
        if config_path:
            context["config_path"] = config_path
        if config_key:
            context["config_key"] = config_key
        if config_value:
            context["config_value"] = config_value

        super().__init__(message, context)
        self.config_path = config_path
        self.config_key = config_key
        self.config_value = config_value


class ImportError(TranslationError):
    """导入操作相关错误

    翻译文件导入、模组目录读取等操作失败时抛出。
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> None:
        """初始化导入错误

        Args:
            message: 错误消息
            file_path: 导致错误的文件路径
            line_number: 错误行号（如果适用）
        """
        context = {}
        if file_path:
            context["file_path"] = file_path
        if line_number:
            context["line_number"] = str(line_number)

        super().__init__(message, context)
        self.file_path = file_path
        self.line_number = line_number


class ExportError(TranslationError):
    """导出操作相关错误

    翻译文件导出、模板生成等操作失败时抛出。
    """

    def __init__(
        self,
        message: str,
        output_path: Optional[str] = None,
        format_type: Optional[str] = None,  # 修改参数名以匹配测试
        export_format: Optional[str] = None,  # 保留旧名称支持
    ) -> None:
        """初始化导出错误

        Args:
            message: 错误消息
            output_path: 输出路径
            format_type: 导出格式类型
            export_format: 导出格式(向后兼容)
        """
        context = {}
        if output_path:
            context["output_path"] = output_path

        # 优先使用format_type，如果没有则使用export_format
        format_value = format_type or export_format
        if format_value:
            context["format_type"] = format_value

        super().__init__(message, context)
        self.output_path = output_path
        self.format_type = format_value
        self.export_format = format_value  # 向后兼容


class ProcessingError(TranslationError):
    """处理过程中的错误

    翻译处理、文件解析等过程中的错误。
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        stage: Optional[str] = None,
        affected_items: Optional[List[str]] = None,
    ) -> None:
        """初始化处理错误

        Args:
            message: 错误消息
            operation: 执行的操作
            stage: 错误发生的阶段
            affected_items: 受影响的项目列表
        """
        context = {}
        if operation:
            context["operation"] = operation
        if stage:
            context["stage"] = stage
        if affected_items:
            context["affected_items"] = ", ".join(affected_items)

        super().__init__(message, context)
        self.operation = operation
        self.stage = stage
        self.affected_items = affected_items or []


class ValidationError(ProcessingError):
    """验证相关错误

    数据验证、格式检查失败时抛出。
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field: Optional[str] = None,  # 添加field参数支持
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
    ) -> None:
        """初始化验证错误

        Args:
            message: 错误消息
            field_name: 验证失败的字段名
            field: 验证失败的字段名（别名）
            expected_type: 期望的类型
            actual_value: 实际值
        """
        context = {}
        # 优先使用field，如果没有则使用field_name
        field_value = field or field_name
        if field_value:
            context["field_name"] = field_value

        if expected_type:
            context["expected_type"] = expected_type
        if actual_value is not None:
            context["actual_value"] = str(actual_value)

        super().__init__(message, context)
        self.field_name = field_value
        self.field = field_value  # 别名支持
        self.expected_type = expected_type
        self.actual_value = actual_value


class NetworkError(TranslationError):
    """网络相关错误

    API调用、网络请求失败时抛出。
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        """初始化网络错误

        Args:
            message: 错误消息
            url: 请求的URL
            status_code: HTTP状态码
            response_text: 响应文本
        """
        context = {}
        if url:
            context["url"] = url
        if status_code:
            context["status_code"] = str(status_code)
        if response_text:
            context["response_text"] = response_text[:200]  # 限制长度

        super().__init__(message, context)
        self.url = url
        self.status_code = status_code
        self.response_text = response_text


# 异常类别名
ConfigurationError = ConfigError
FileError = ImportError
FormatError = ValidationError
APIError = NetworkError
