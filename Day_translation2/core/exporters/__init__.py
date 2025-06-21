"""
Day Translation 2 - 导出模块统一接口

本模块提供对外统一的导出功能接口，实现向后兼容的import路径。
重构后的子模块按功能分类，提供清晰的功能边界和更好的可维护性。

子模块结构:
- xml_generators: XML生成辅助工具
- keyed_exporter: Keyed目录翻译导出
- definjected_exporter: DefInjected目录翻译导出
- csv_exporter: CSV格式数据导出
- export_utils: 智能导出和批量导出工具
- advanced_exporter: 高级导出器门面类

使用示例:
    from core.exporters import export_keyed, export_to_csv, AdvancedExporter
    from core.exporters.advanced_exporter import AdvancedExporter
"""

# XML生成工具
from .xml_generators import (
    generate_keyed_xml,
    generate_definjected_xml,
    generate_definjected_xml_multi_type,
)

# Keyed导出功能
from .keyed_exporter import (
    export_keyed,
    export_keyed_to_csv,
)

# DefInjected导出功能
from .definjected_exporter import (
    export_definjected,
    export_definjected_with_original_structure,
    export_definjected_with_defs_structure,
    export_definjected_to_csv,
)

# CSV导出功能
from .csv_exporter import (
    export_to_csv,
)

# 高级导出工具
from .export_utils import (
    export_with_smart_merge,
    batch_export_with_smart_merge,
    export_with_user_interaction,
    export_all_with_advanced_features,
)

# 高级导出器门面类
from .advanced_exporter import AdvancedExporter

# 向后兼容的导出函数别名
__all__ = [
    # XML生成
    "generate_keyed_xml",
    "generate_definjected_xml",
    "generate_definjected_xml_multi_type",
    # Keyed导出
    "export_keyed",
    "export_keyed_to_csv",
    # DefInjected导出
    "export_definjected",
    "export_definjected_with_original_structure",
    "export_definjected_with_defs_structure",
    "export_definjected_to_csv",
    # CSV导出
    "export_to_csv",
    # 高级导出工具
    "export_with_smart_merge",
    "batch_export_with_smart_merge",
    "export_with_user_interaction",
    "export_all_with_advanced_features",
    # 高级导出器
    "AdvancedExporter",
]


def get_available_exporters():
    """
    获取所有可用的导出器信息

    Returns:
        dict: 导出器类型和描述的字典
    """
    return {
        "keyed": "Keyed目录翻译导出 - 支持标准和Legacy格式",
        "definjected": "DefInjected目录翻译导出 - 保持原始结构",
        "csv": "CSV格式数据导出 - 支持上下文信息",
        "smart_merge": "智能合并导出 - 自动处理版本差异",
        "batch": "批量导出 - 支持多目录同时导出",
        "interactive": "交互式导出 - 提供用户选择界面",
        "advanced": "高级导出器 - 综合所有导出功能的门面类",
    }


def get_exporter_recommendations():
    """
    获取导出器使用建议

    Returns:
        dict: 使用场景和推荐导出器的字典
    """
    return {
        "新手用户": "建议使用 AdvancedExporter 类，提供完整的导出功能",
        "自动化脚本": "建议使用 export_with_smart_merge 进行智能导出",
        "批量处理": "建议使用 batch_export_with_smart_merge 进行批量导出",
        "自定义需求": "建议直接使用具体的导出函数如 export_keyed, export_definjected",
        "数据分析": "建议使用 export_to_csv 导出为CSV格式",
        "交互式操作": "建议使用 export_with_user_interaction 提供用户界面",
    }
