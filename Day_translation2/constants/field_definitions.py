"""
Day Translation 2 - 字段定义常量

统一管理所有翻译字段的定义，避免重复配置。
遵循提示文件标准：单一数据源，易于维护。
"""

from typing import Set

# 统一的默认翻译字段集合 - RimWorld专用
DEFAULT_TRANSLATION_FIELDS: Set[str] = {
    # 基础字段
    "label",
    "description",
    "labelShort",
    "descriptionShort",
    "title",
    "text",
    "message",
    "tooltip",
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
    # RimWorld 特有字段
    "RMBLabel",
    "rulesStrings",
    "labelNoun",
    "gerund",
    "reportString",
    "skillLabel",
    "pawnLabel",
    "titleShort",
    # 覆盖字段
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

# 字段分类
BASIC_FIELDS: Set[str] = {
    "label",
    "description",
    "labelShort",
    "descriptionShort",
    "title",
    "text",
    "message",
    "tooltip",
}

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

OVERRIDE_FIELDS: Set[str] = {
    field for field in DEFAULT_TRANSLATION_FIELDS if field.startswith("override")
}

# 字段优先级（用于冲突解决）
FIELD_PRIORITY = {
    "label": 10,
    "description": 9,
    "title": 8,
    "text": 7,
    "message": 6,
    "tooltip": 5,
    # 其他字段默认优先级为1
}


def get_field_priority(field_name: str) -> int:
    """获取字段优先级"""
    return FIELD_PRIORITY.get(field_name, 1)


def is_override_field(field_name: str) -> bool:
    """检查是否为覆盖字段"""
    return field_name.startswith("override")


def is_basic_field(field_name: str) -> bool:
    """检查是否为基础字段"""
    return field_name in BASIC_FIELDS


def is_rimworld_specific(field_name: str) -> bool:
    """检查是否为RimWorld特有字段"""
    return field_name in RIMWORLD_SPECIFIC_FIELDS
