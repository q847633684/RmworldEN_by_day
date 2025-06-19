"""
Day Translation 2 - 完整字段定义和配置常量

统一管理所有翻译字段的定义、配置常量和验证规则。
整合了AdvancedFilterRules中的所有字段定义、模式和规则。
遵循提示文件标准：单一数据源，易于维护，完整的类型注解。
"""

import re
from enum import Enum
from typing import Any, Dict, List, Set, Tuple

# ==================== 语言和编码常量 ====================


class LanguageCode(Enum):
    """支持的语言代码"""

    ENGLISH = "English"
    CHINESE_SIMPLIFIED = "ChineseSimplified"
    CHINESE_TRADITIONAL = "ChineseTraditional"
    JAPANESE = "Japanese"
    KOREAN = "Korean"

    def __str__(self) -> str:
        """返回用户友好的语言名称"""
        language_names = {
            self.ENGLISH: "英语",
            self.CHINESE_SIMPLIFIED: "简体中文",
            self.CHINESE_TRADITIONAL: "繁体中文",
            self.JAPANESE: "日语",
            self.KOREAN: "韩语",
        }
        return language_names.get(self, self.value)


# ==================== 翻译字段定义 ====================

# 基础翻译字段
BASIC_TRANSLATION_FIELDS: Set[str] = {
    "label",
    "description",
    "labelShort",
    "descriptionShort",
    "title",
    "text",
    "message",
    "tooltip",
}

# RimWorld游戏特有字段
RIMWORLD_SPECIFIC_FIELDS: Set[str] = {
    "baseDesc",
    "skillDescription",
    "backstoryDesc",
    "jobString",
    "gerundLabel",
    "verb",
    "deathMessage",
    "summary",
    "note",
    "flavor",
    "quote",
    "caption",
    "RMBLabel",
    "rulesStrings",
    "labelNoun",
    "gerund",
    "reportString",
    "skillLabel",
    "pawnLabel",
    "titleShort",
}

# 覆盖字段（override前缀）
OVERRIDE_FIELDS: Set[str] = {
    "reportStringOverride",
    "overrideReportString",
    "overrideTooltip",
    "overrideLabel",
    "overrideDescription",
    "overrideLabelShort",
    "overrideDescriptionShort",
    "overrideTitle",
    "overrideText",
    "overrideMessage",
    "overrideBaseDesc",
    "overrideSkillDescription",
    "overrideBackstoryDesc",
    "overrideJobString",
    "overrideGerundLabel",
    "overrideVerb",
    "overrideDeathMessage",
    "overrideSummary",
    "overrideNote",
    "overrideFlavor",
    "overrideQuote",
    "overrideCaption",
}

# 自定义字段（custom前缀）
CUSTOM_FIELDS: Set[str] = {
    "customLabel",
    "customDescription",
    "customTooltip",
    "customMessage",
    "customText",
    "customTitle",
    "customBaseDesc",
    "customSkillDescription",
    "customBackstoryDesc",
    "customJobString",
    "customGerundLabel",
    "customVerb",
    "customDeathMessage",
    "customSummary",
    "customNote",
    "customFlavor",
    "customQuote",
    "customCaption",
}

# 统一的默认翻译字段集合
DEFAULT_TRANSLATION_FIELDS: Set[str] = (
    BASIC_TRANSLATION_FIELDS | RIMWORLD_SPECIFIC_FIELDS | OVERRIDE_FIELDS | CUSTOM_FIELDS
)

# ==================== 忽略字段定义 ====================

# 扩展忽略字段（与AdvancedFilterRules完全一致）
IGNORE_FIELDS: Set[str] = {
    # 基础字段
    "defName",
    "id",
    "cost",
    "damage",
    "x",
    "y",
    "z",
    "width",
    "height",
    "priority",
    "count",
    "index",
    "version",
    "url",
    "path",
    "file",
    "hash",
    "key",
    # 数值字段
    "order",
    "weight",
    "value",
    "amount",
    "quantity",
    "duration",
    "cooldown",
    "range",
    "radius",
    "angle",
    "speed",
    "force",
    "power",
    "energy",
    "health",
    "armor",
    "shield",
    "resistance",
    "penetration",
    "accuracy",
    "evasion",
    "critChance",
    "critDamage",
    "dodgeChance",
    "blockChance",
    "parryChance",
    # 技术字段
    "guid",
    "uuid",
    "timestamp",
    "date",
    "time",
    "checksum",
    "signature",
    "token",
    "secret",
    "password",
    "salt",
    "encryption",
    "compression",
    "encoding",
    "format",
    "type",
    "category",
    "tag",
    "group",
    "class",
    "style",
}

# 默认忽略字段（对外接口，保持向后兼容）
DEFAULT_IGNORE_FIELDS: Set[str] = IGNORE_FIELDS

# ==================== 非文本模式定义 ====================

# 非文本模式 - 智能识别（与AdvancedFilterRules完全一致）
NON_TEXT_PATTERNS: List[str] = [
    # 数字模式
    r"^\d+$",  # 整数
    r"^-?\d+\.\d+$",  # 浮点数
    r"^[0-9a-fA-F]+$",  # 十六进制
    r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$",  # 科学计数法
    r"^\d+[kKmMgGtT]?$",  # 带单位的数字
    # 空白模式
    r"^\s*$",  # 纯空白
    r"^[\s\-_]+$",  # 分隔符
    # 布尔值
    r"^(true|false)$",  # 布尔值
    r"^(yes|no)$",  # 是/否
    r"^(on|off)$",  # 开/关
    # 路径模式
    r"^[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-]+$",  # 文件名
    r"^[A-Za-z0-9_\-/\\\.]+[/\\][A-Za-z0-9_\-\.]+$",  # 路径
    # URL模式
    r'https?://[^\s<>"]+',  # HTTP URL
    r'www\.[^\s<>"]+',  # www链接
    # 标识符模式
    r"^[A-Za-z0-9_\-]+#[A-Za-z0-9_\-]+$",  # 带#的标识符
    r"^[A-Za-z0-9_\-]+@[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-]+$",  # 邮箱格式
    r"^[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+$",  # 带:的标识符
]

# ==================== 字段类型定义 ====================

# 字段类型定义（与AdvancedFilterRules完全一致）
FIELD_TYPES: Dict[str, str] = {
    "translatable": "需要翻译的字段",
    "ignored": "忽略的字段",
    "conditional": "条件性翻译的字段",
    "reference": "引用类型的字段",
    "format": "格式化字符串字段",
    "plural": "复数形式字段",
    "gender": "性别相关字段",
    "context": "上下文相关字段",
}

# ==================== 字段分组定义 ====================

# 字段分组定义（与AdvancedFilterRules完全一致）
FIELD_GROUPS: Dict[str, Dict[str, Any]] = {
    "basic": {
        "name": "基础字段",
        "description": "基本的文本字段",
        "fields": {"label", "description", "text", "message"},
    },
    "ui": {
        "name": "界面字段",
        "description": "用户界面相关字段",
        "fields": {"tooltip", "title", "caption", "button", "menu"},
    },
    "game": {
        "name": "游戏字段",
        "description": "游戏内容相关字段",
        "fields": {"skillDescription", "backstoryDesc", "jobString", "deathMessage"},
    },
    "override": {
        "name": "覆盖字段",
        "description": "覆盖默认值的字段",
        "fields": OVERRIDE_FIELDS,
    },
    "custom": {
        "name": "自定义字段",
        "description": "用户自定义字段",
        "fields": CUSTOM_FIELDS,
    },
}

# ==================== 优先级定义 ====================

# 规则优先级定义（与AdvancedFilterRules完全一致）
PRIORITY_LEVELS: Dict[str, int] = {
    "highest": 100,  # 最高优先级
    "high": 75,  # 高优先级
    "normal": 50,  # 普通优先级
    "low": 25,  # 低优先级
    "lowest": 0,  # 最低优先级
}

# 字段优先级（用于冲突解决）
FIELD_PRIORITY: Dict[str, int] = {
    # 核心字段 - 最高优先级
    "label": 10,
    "description": 9,
    "title": 8,
    # 重要字段
    "text": 7,
    "message": 6,
    "tooltip": 5,
    # 游戏特有字段
    "baseDesc": 4,
    "skillDescription": 4,
    "backstoryDesc": 3,
    "jobString": 3,
    "gerundLabel": 2,
    "verb": 2,
    "deathMessage": 2,
    # 一般字段
    "summary": 1,
    "note": 1,
    "flavor": 1,
    "quote": 1,
    "caption": 1,
    # 默认优先级（未在上述列表中的字段）
    "default": 0,
}

# ==================== 配置常量 ====================

# === 编码设置 ===
ENCODING_SETTINGS: Dict[str, str] = {
    "xml": "utf-8",
    "csv": "utf-8-sig",
    "default": "utf-8"
}

# === 默认目录结构 ===
DEFAULT_DIRECTORIES: Dict[str, str] = {
    "keyed": "Keyed",
    "definjected": "DefInjected", 
    "logs": "logs",
    "output": "output",
    "backup": "backup"
}

# === 默认文件名 ===
DEFAULT_FILENAMES: Dict[str, str] = {
    "output_csv": "extracted_translations.csv",
    "config": "day_translation_config.json",
    "log": "day_translation.log"
}

# 默认配置值
DEFAULT_CONFIG: Dict[str, Any] = {
    "source_language": LanguageCode.ENGLISH.value,
    "target_language": LanguageCode.CHINESE_SIMPLIFIED.value,
    "translation_fields": DEFAULT_TRANSLATION_FIELDS,
    "ignore_fields": DEFAULT_IGNORE_FIELDS,
    "non_text_patterns": NON_TEXT_PATTERNS,
    "field_priority": FIELD_PRIORITY,
    "field_types": FIELD_TYPES,
    "field_groups": FIELD_GROUPS,
    "priority_levels": PRIORITY_LEVELS,
    "enable_validation": True,
    "enable_backup": True,
    "batch_size": 100,
    "max_retries": 3,
    "timeout": 30,
}

# 验证规则
VALIDATION_RULES: Dict[str, Dict[str, Any]] = {
    "field_name": {
        "pattern": r"^[A-Za-z][A-Za-z0-9_]*$",
        "max_length": 64,
        "min_length": 1,
    },
    "field_value": {
        "max_length": 10000,
        "min_length": 0,
    },
    "language_code": {
        "valid_values": [lang.value for lang in LanguageCode],
    },
    "priority_level": {
        "valid_values": list(PRIORITY_LEVELS.keys()),
    },
    "field_type": {
        "valid_values": list(FIELD_TYPES.keys()),
    },
}

# ==================== 辅助函数 ====================


def is_translation_field(field_name: str) -> bool:
    """检查字段是否为翻译字段"""
    return field_name in DEFAULT_TRANSLATION_FIELDS


def is_ignore_field(field_name: str) -> bool:
    """检查字段是否为忽略字段"""
    return field_name in DEFAULT_IGNORE_FIELDS


def is_override_field(field_name: str) -> bool:
    """检查字段是否为覆盖字段"""
    return field_name in OVERRIDE_FIELDS or field_name.startswith("override")


def is_custom_field(field_name: str) -> bool:
    """检查字段是否为自定义字段"""
    return field_name in CUSTOM_FIELDS or field_name.startswith("custom")


def get_field_priority(field_name: str) -> int:
    """获取字段优先级"""
    return FIELD_PRIORITY.get(field_name, FIELD_PRIORITY["default"])


def get_field_type(field_name: str) -> str:
    """获取字段类型"""
    if is_ignore_field(field_name):
        return "ignored"
    elif is_translation_field(field_name):
        return "translatable"
    else:
        return "unknown"


def get_field_group(field_name: str) -> str:
    """获取字段所属的分组"""
    for group_id, group_info in FIELD_GROUPS.items():
        if field_name in group_info["fields"]:
            return group_id
    return "unknown"


def is_non_text_content(content: str) -> bool:
    """检查内容是否为非文本内容"""
    if not content or not isinstance(content, str):
        return True

    content = content.strip()
    if not content:
        return True

    # 检查非文本模式
    for pattern in NON_TEXT_PATTERNS:
        try:
            if re.match(pattern, content, re.IGNORECASE):
                return True
        except re.error:
            continue

    return False


def validate_field_name(field_name: str) -> bool:
    """验证字段名格式"""
    rules = VALIDATION_RULES["field_name"]
    if not isinstance(field_name, str):
        return False
    if not (rules["min_length"] <= len(field_name) <= rules["max_length"]):
        return False
    return bool(re.match(rules["pattern"], field_name))


def get_all_translation_fields() -> Set[str]:
    """获取所有翻译字段"""
    return DEFAULT_TRANSLATION_FIELDS.copy()


def get_all_ignore_fields() -> Set[str]:
    """获取所有忽略字段"""
    return DEFAULT_IGNORE_FIELDS.copy()


def get_field_statistics() -> Dict[str, int]:
    """获取字段统计信息"""
    return {
        "total_translation_fields": len(DEFAULT_TRANSLATION_FIELDS),
        "basic_fields": len(BASIC_TRANSLATION_FIELDS),
        "rimworld_fields": len(RIMWORLD_SPECIFIC_FIELDS),
        "override_fields": len(OVERRIDE_FIELDS),
        "custom_fields": len(CUSTOM_FIELDS),
        "ignore_fields": len(DEFAULT_IGNORE_FIELDS),
        "field_groups": len(FIELD_GROUPS),
        "priority_levels": len(PRIORITY_LEVELS),
        "field_types": len(FIELD_TYPES),
        "non_text_patterns": len(NON_TEXT_PATTERNS),
    }


# ==================== 向后兼容性接口 ====================

# 保持与旧系统的兼容性
ALL_TRANSLATION_FIELDS = DEFAULT_TRANSLATION_FIELDS
ALL_IGNORE_FIELDS = DEFAULT_IGNORE_FIELDS
FIELD_PATTERNS = NON_TEXT_PATTERNS

# 导出所有常量和函数
__all__ = [
    # 枚举
    "LanguageCode",
    # 字段集合
    "BASIC_TRANSLATION_FIELDS",
    "RIMWORLD_SPECIFIC_FIELDS",
    "OVERRIDE_FIELDS",
    "CUSTOM_FIELDS",
    "DEFAULT_TRANSLATION_FIELDS",
    "IGNORE_FIELDS",
    "DEFAULT_IGNORE_FIELDS",
    # 模式和规则
    "NON_TEXT_PATTERNS",
    "FIELD_TYPES",
    "FIELD_GROUPS",
    "PRIORITY_LEVELS",
    "FIELD_PRIORITY",    # 配置
    "ENCODING_SETTINGS",
    "DEFAULT_DIRECTORIES", 
    "DEFAULT_FILENAMES",
    "DEFAULT_CONFIG",
    "VALIDATION_RULES",
    # 辅助函数
    "is_translation_field",
    "is_ignore_field",
    "is_override_field",
    "is_custom_field",
    "get_field_priority",
    "get_field_type",
    "get_field_group",
    "is_non_text_content",
    "validate_field_name",
    "get_all_translation_fields",
    "get_all_ignore_fields",
    "get_field_statistics",
    # 向后兼容
    "ALL_TRANSLATION_FIELDS",
    "ALL_IGNORE_FIELDS",
    "FIELD_PATTERNS",
]
