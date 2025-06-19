"""
Day Translation 2 - 工具模块

提供各种实用工具，包括：
- XML处理工具
- 文件操作工具
- 内容过滤器（基础和高级）
- 高级过滤规则管理器
"""


# 延迟导入函数
def get_xml_processor():
    """获取XML处理器"""
    from .xml_processor import XMLProcessor

    return XMLProcessor


def get_content_filter():
    """获取基础内容过滤器（已废弃，使用AdvancedFilterRules替代）"""
    raise DeprecationWarning("ContentFilter已废弃，请使用get_advanced_filter_rules()替代")


def get_advanced_filter_rules():
    """获取高级过滤规则管理器"""
    from .filter_rules import AdvancedFilterRules

    return AdvancedFilterRules


def get_file_utils():
    """获取文件工具"""
    from . import file_utils

    return file_utils


__all__ = ["get_xml_processor", "get_content_filter", "get_advanced_filter_rules", "get_file_utils"]
