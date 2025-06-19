"""
Day Translation 2 - 常量模块

统一管理所有常量定义。
"""

from .field_definitions import (BASIC_FIELDS, DEFAULT_TRANSLATION_FIELDS,
                                FIELD_PRIORITY, OVERRIDE_FIELDS,
                                RIMWORLD_SPECIFIC_FIELDS, get_field_priority,
                                is_basic_field, is_override_field,
                                is_rimworld_specific)

__all__ = [
    "DEFAULT_TRANSLATION_FIELDS",
    "BASIC_FIELDS",
    "RIMWORLD_SPECIFIC_FIELDS",
    "OVERRIDE_FIELDS",
    "FIELD_PRIORITY",
    "get_field_priority",
    "is_override_field",
    "is_basic_field",
    "is_rimworld_specific",
]
