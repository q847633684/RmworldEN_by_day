"""
Day Translation 2 - 常量定义模块

统一导出所有常量定义，包括字段定义、配置常量等。
"""

from .complete_definitions import (  # 语言相关; 字段定义; 字段分类和优先级; 内容过滤; 配置默认值; 辅助函数
    BASIC_TRANSLATION_FIELDS,
    CUSTOM_FIELDS,
    DEFAULT_CONFIG,
    DEFAULT_IGNORE_FIELDS,
    DEFAULT_TRANSLATION_FIELDS,
    FIELD_GROUPS,
    FIELD_PRIORITY,
    FIELD_TYPES,
    NON_TEXT_PATTERNS,
    OVERRIDE_FIELDS,
    RIMWORLD_SPECIFIC_FIELDS,
    LanguageCode,
    get_all_ignore_fields,
    get_all_translation_fields,
    get_field_group,
    get_field_priority,
    get_field_statistics,
    get_field_type,
    is_custom_field,
    is_ignore_field,
    is_override_field,
    is_translation_field,
    validate_field_name,
)

__all__ = [
    # 语言相关
    "LanguageCode",
    # 字段定义
    "DEFAULT_TRANSLATION_FIELDS",
    "BASIC_TRANSLATION_FIELDS",
    "RIMWORLD_SPECIFIC_FIELDS",
    "OVERRIDE_FIELDS",
    "CUSTOM_FIELDS",
    "DEFAULT_IGNORE_FIELDS",
    # 字段分类
    "FIELD_PRIORITY",
    "FIELD_GROUPS",
    "FIELD_TYPES",
    # 过滤相关
    "NON_TEXT_PATTERNS",
    # 配置常量
    "DEFAULT_CONFIG",
    # 辅助函数
    "get_field_priority",
    "is_override_field",
    "is_custom_field",
    "is_translation_field",
    "is_ignore_field",
    "get_field_group",
    "get_field_type",
    "validate_field_name",
    "get_field_statistics",
    "get_all_translation_fields",
    "get_all_ignore_fields",
]
