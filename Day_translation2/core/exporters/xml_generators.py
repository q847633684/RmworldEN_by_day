"""
Day Translation 2 - XML生成辅助函数

负责生成各种格式的XML内容，支持Keyed和DefInjected格式。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。
"""

from typing import Dict, List

from models.translation_data import TranslationData


def generate_keyed_xml(translations: List[TranslationData]) -> str:
    """
    生成Keyed XML内容

    Args:
        translations: 翻译条目列表

    Returns:
        XML内容字符串
    """
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]

    for translation in translations:
        comment = (
            f"  <!-- EN: {translation.original_text} -->"
            if translation.original_text
            else ""
        )
        if comment:
            lines.append(comment)

        # 使用translated_text如果存在，否则使用original_text作为模板
        text = translation.translated_text or translation.original_text
        lines.append(f"  <{translation.key}>{text}</{translation.key}>")

    lines.append("</LanguageData>")
    return "\n".join(lines)


def generate_definjected_xml(translations: List[TranslationData], def_type: str) -> str:
    """
    生成DefInjected XML内容

    Args:
        translations: 翻译条目列表
        def_type: 定义类型

    Returns:
        XML内容字符串
    """
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]

    # 按def_name分组
    name_groups: Dict[str, List[TranslationData]] = {}
    for translation in translations:
        def_name = translation.metadata.get("def_name", "Unknown")
        if def_name not in name_groups:
            name_groups[def_name] = []
        name_groups[def_name].append(translation)

    for def_name, group_translations in name_groups.items():
        lines.append(f"  <!-- {def_type}: {def_name} -->")
        for translation in group_translations:
            # 生成DefInjected格式的key
            field_path = translation.metadata.get("field_path", translation.key)
            full_key = f"{def_type}.{def_name}.{field_path}"

            # 使用translated_text如果存在，否则使用original_text作为模板
            text = translation.translated_text or translation.original_text
            lines.append(f"  <{full_key}>{text}</{full_key}>")

    lines.append("</LanguageData>")
    return "\n".join(lines)


def generate_definjected_xml_multi_type(
    type_groups: Dict[str, List[TranslationData]],
) -> str:
    """
    生成包含多个def_type的DefInjected XML内容

    Args:
        type_groups: 按类型分组的翻译数据

    Returns:
        XML内容字符串
    """
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]

    for def_type, type_translations in type_groups.items():
        lines.append(f"  <!-- {def_type} Definitions -->")

        # 按def_name分组
        name_groups: Dict[str, List[TranslationData]] = {}
        for translation in type_translations:
            def_name = translation.metadata.get("def_name", "Unknown")
            if def_name not in name_groups:
                name_groups[def_name] = []
            name_groups[def_name].append(translation)

        for def_name, group_translations in name_groups.items():
            lines.append(f"  <!-- {def_type}: {def_name} -->")
            for translation in group_translations:
                # 生成DefInjected格式的key
                field_path = translation.metadata.get("field_path", translation.key)
                full_key = f"{def_type}.{def_name}.{field_path}"

                # 使用translated_text如果存在，否则使用original_text作为模板
                text = translation.translated_text or translation.original_text
                lines.append(f"  <{full_key}>{text}</{full_key}>")

    lines.append("</LanguageData>")
    return "\n".join(lines)
