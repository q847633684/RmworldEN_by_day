"""
配置验证器

提供配置验证功能
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import os
from pathlib import Path
from utils.logging_config import get_logger


class ValidationResult:
    """验证结果"""

    def __init__(
        self,
        is_valid: bool = True,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """添加警告"""
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> None:
        """合并其他验证结果"""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


class ConfigValidator:
    """配置验证器"""

    def __init__(self):
        self.logger = get_logger(f"{__name__}.ConfigValidator")

    def validate_string(
        self,
        value: Any,
        field_name: str,
        required: bool = False,
        min_length: int = 0,
        max_length: int = 1000,
        pattern: Optional[str] = None,
    ) -> ValidationResult:
        """验证字符串字段"""
        result = ValidationResult()

        # 检查类型
        if not isinstance(value, str):
            if required or value is not None:
                result.add_error(f"{field_name} 必须是字符串类型")
                return result
            return result

        # 检查必需字段
        if required and not value.strip():
            result.add_error(f"{field_name} 不能为空")
            return result

        # 检查长度
        if len(value) < min_length:
            result.add_error(f"{field_name} 长度不能少于 {min_length} 个字符")

        if len(value) > max_length:
            result.add_error(f"{field_name} 长度不能超过 {max_length} 个字符")

        # 检查模式
        if pattern and value and not re.match(pattern, value):
            result.add_error(f"{field_name} 格式不正确")

        return result

    def validate_number(
        self,
        value: Any,
        field_name: str,
        required: bool = False,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        is_integer: bool = False,
    ) -> ValidationResult:
        """验证数字字段"""
        result = ValidationResult()

        # 检查类型
        if is_integer:
            if not isinstance(value, int):
                if required or value is not None:
                    result.add_error(f"{field_name} 必须是整数类型")
                    return result
                return result
        else:
            if not isinstance(value, (int, float)):
                if required or value is not None:
                    result.add_error(f"{field_name} 必须是数字类型")
                    return result
                return result

        # 检查范围
        if min_value is not None and value < min_value:
            result.add_error(f"{field_name} 不能小于 {min_value}")

        if max_value is not None and value > max_value:
            result.add_error(f"{field_name} 不能大于 {max_value}")

        return result

    def validate_boolean(
        self, value: Any, field_name: str, required: bool = False
    ) -> ValidationResult:
        """验证布尔字段"""
        result = ValidationResult()

        if not isinstance(value, bool):
            if required or value is not None:
                result.add_error(f"{field_name} 必须是布尔类型")

        return result

    def validate_path(
        self,
        value: Any,
        field_name: str,
        required: bool = False,
        must_exist: bool = False,
        is_file: bool = False,
        is_directory: bool = False,
    ) -> ValidationResult:
        """验证路径字段"""
        result = ValidationResult()

        # 先验证字符串
        string_result = self.validate_string(value, field_name, required)
        result.merge(string_result)

        if not result.is_valid or not value:
            return result

        # 检查路径格式
        try:
            path = Path(value)
        except Exception as e:
            result.add_error(f"{field_name} 路径格式无效: {e}")
            return result

        # 检查路径是否存在
        if must_exist and not path.exists():
            result.add_error(f"{field_name} 路径不存在: {value}")
            return result

        # 检查是否为文件
        if is_file and path.exists() and not path.is_file():
            result.add_error(f"{field_name} 必须是文件: {value}")

        # 检查是否为目录
        if is_directory and path.exists() and not path.is_dir():
            result.add_error(f"{field_name} 必须是目录: {value}")

        # 检查父目录是否存在（对于文件路径）
        if is_file and not path.parent.exists():
            result.add_warning(f"{field_name} 的父目录不存在: {path.parent}")

        return result

    def validate_email(
        self, value: Any, field_name: str, required: bool = False
    ) -> ValidationResult:
        """验证邮箱字段"""
        result = ValidationResult()

        # 先验证字符串
        string_result = self.validate_string(value, field_name, required)
        result.merge(string_result)

        if not result.is_valid or not value:
            return result

        # 简单的邮箱格式验证
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            result.add_error(f"{field_name} 邮箱格式不正确")

        return result

    def validate_url(
        self,
        value: Any,
        field_name: str,
        required: bool = False,
        allowed_schemes: Optional[List[str]] = None,
    ) -> ValidationResult:
        """验证URL字段"""
        result = ValidationResult()

        # 先验证字符串
        string_result = self.validate_string(value, field_name, required)
        result.merge(string_result)

        if not result.is_valid or not value:
            return result

        # URL格式验证
        url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(url_pattern, value):
            result.add_error(f"{field_name} URL格式不正确")
            return result

        # 检查协议
        if allowed_schemes:
            scheme = value.split("://")[0].lower()
            if scheme not in allowed_schemes:
                result.add_error(
                    f"{field_name} 协议不支持，支持的协议: {', '.join(allowed_schemes)}"
                )

        return result

    def validate_choice(
        self, value: Any, field_name: str, choices: List[Any], required: bool = False
    ) -> ValidationResult:
        """验证选择字段"""
        result = ValidationResult()

        if required and value is None:
            result.add_error(f"{field_name} 不能为空")
            return result

        if value is not None and value not in choices:
            result.add_error(
                f"{field_name} 值无效，可选值: {', '.join(map(str, choices))}"
            )

        return result

    def validate_api_key(
        self,
        value: Any,
        field_name: str,
        required: bool = False,
        min_length: int = 10,
        max_length: int = 200,
    ) -> ValidationResult:
        """验证API密钥字段"""
        result = ValidationResult()

        # 先验证字符串
        string_result = self.validate_string(
            value, field_name, required, min_length, max_length
        )
        result.merge(string_result)

        if not result.is_valid or not value:
            return result

        # 检查是否包含空格
        if " " in value:
            result.add_warning(f"{field_name} 包含空格，请确认是否正确")

        # 检查是否为常见的占位符
        placeholders = ["your_key", "your_secret", "placeholder", "example", "test"]
        if value.lower() in placeholders:
            result.add_error(f"{field_name} 似乎是占位符，请输入真实的密钥")

        return result

    def validate_config_schema(
        self, config_data: Dict[str, Any], schema: Dict[str, Any]
    ) -> ValidationResult:
        """根据模式验证配置"""
        result = ValidationResult()

        for field_name, field_schema in schema.items():
            value = config_data.get(field_name)
            field_type = field_schema.get("type", "text")
            required = field_schema.get("required", False)

            if field_type == "text":
                field_result = self.validate_string(
                    value,
                    field_name,
                    required,
                    field_schema.get("min_length", 0),
                    field_schema.get("max_length", 1000),
                    field_schema.get("pattern"),
                )
            elif field_type == "password":
                field_result = self.validate_api_key(
                    value,
                    field_name,
                    required,
                    field_schema.get("min_length", 10),
                    field_schema.get("max_length", 200),
                )
            elif field_type == "number":
                field_result = self.validate_number(
                    value,
                    field_name,
                    required,
                    field_schema.get("min"),
                    field_schema.get("max"),
                    field_schema.get("integer", False),
                )
            elif field_type == "boolean":
                field_result = self.validate_boolean(value, field_name, required)
            elif field_type == "select":
                options = field_schema.get("options", [])
                choices = [
                    opt.get("value") if isinstance(opt, dict) else opt
                    for opt in options
                ]
                field_result = self.validate_choice(
                    value, field_name, choices, required
                )
            elif field_type == "file":
                field_result = self.validate_path(
                    value,
                    field_name,
                    required,
                    field_schema.get("must_exist", False),
                    is_file=True,
                )
            elif field_type == "directory":
                field_result = self.validate_path(
                    value,
                    field_name,
                    required,
                    field_schema.get("must_exist", False),
                    is_directory=True,
                )
            elif field_type == "url":
                field_result = self.validate_url(
                    value, field_name, required, field_schema.get("allowed_schemes")
                )
            elif field_type == "email":
                field_result = self.validate_email(value, field_name, required)
            else:
                field_result = ValidationResult()
                field_result.add_warning(f"未知的字段类型: {field_type}")

            result.merge(field_result)

        return result

    def validate_aliyun_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证阿里云配置"""
        result = ValidationResult()

        # 验证AccessKeyId
        access_key_id = config_data.get("access_key_id")
        if access_key_id:
            if len(access_key_id) < 16 or len(access_key_id) > 30:
                result.add_error("AccessKeyId 长度应在16-30个字符之间")
            if not access_key_id.startswith("LTAI"):
                result.add_warning("AccessKeyId 通常以 'LTAI' 开头")

        # 验证AccessKeySecret
        access_key_secret = config_data.get("access_key_secret")
        if access_key_secret:
            if len(access_key_secret) < 20 or len(access_key_secret) > 50:
                result.add_error("AccessKeySecret 长度应在20-50个字符之间")

        # 验证区域
        region = config_data.get("region")
        valid_regions = [
            "cn-hangzhou",
            "cn-beijing",
            "cn-shanghai",
            "cn-shenzhen",
            "ap-southeast-1",
            "us-west-1",
            "eu-central-1",
        ]
        if region and region not in valid_regions:
            result.add_warning(f"区域 '{region}' 可能不是有效的阿里云区域")

        return result

    def validate_baidu_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证百度配置"""
        result = ValidationResult()

        # 验证APP ID
        app_id = config_data.get("app_id")
        if app_id:
            if not app_id.isdigit():
                result.add_error("百度翻译 APP ID 应该是纯数字")
            if len(app_id) < 10 or len(app_id) > 20:
                result.add_warning("百度翻译 APP ID 长度通常在10-20位之间")

        return result

    def validate_all_configs(self, user_config_manager) -> Dict[str, ValidationResult]:
        """验证所有配置"""
        results = {}

        # 验证API配置
        api_manager = user_config_manager.api_manager
        for api_type, api_config in api_manager.get_all_apis().items():
            if api_config.is_enabled():
                if api_type == "aliyun":
                    results[f"api_{api_type}"] = self.validate_aliyun_config(
                        api_config.to_dict()
                    )
                elif api_type == "baidu":
                    results[f"api_{api_type}"] = self.validate_baidu_config(
                        api_config.to_dict()
                    )
                else:
                    # 使用通用验证
                    schema = api_config.get_schema()
                    results[f"api_{api_type}"] = self.validate_config_schema(
                        api_config.to_dict(), schema
                    )

        # 验证其他配置模块
        for module_name, module in user_config_manager.get_config_modules().items():
            if module_name != "api" and hasattr(module, "get_schema"):
                schema = module.get_schema()
                results[module_name] = self.validate_config_schema(
                    module.to_dict(), schema
                )

        return results
