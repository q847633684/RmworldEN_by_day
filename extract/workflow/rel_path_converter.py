"""
Def rel_path 与 key 转换模块

- 新建：Defs 的 rel_path 转为 def_type/文件名.xml
- 合并：DefInjected 的 key 加 def_type 前缀用于匹配；写出时 key 去除前缀
"""

import os
from typing import List, Tuple, Optional


def convert_def_to_defs_by_type(def_translations: List[Tuple]) -> List[Tuple]:
    """
    新建模式：将 Defs 的 rel_path 转为 def_type/文件名.xml。

    Args:
        def_translations: Def 数据，六元组 (key,...,rel_path,...,def_type)

    Returns:
        转换后，rel_path = def_type/原文件名.xml
    """
    if not def_translations:
        return def_translations

    result = []
    for item in def_translations:
        if len(item) >= 6:
            def_type = item[5]
            orig_rel = item[3] or ""
            filename = os.path.basename(orig_rel.replace("\\", "/")) or f"{def_type}.xml"
            rel_path = f"{def_type}/{filename}"
            base = (item[0], item[1], item[2], rel_path, item[4])
            result.append(base + item[6:] if len(item) > 6 else base + ("",))
        else:
            result.append(item[:5] if len(item) >= 5 else item)
    return result


def normalize_input_rel_path_for_merge(def_translations: List[Tuple]) -> List[Tuple]:
    """
    批量合并前：将输入的 rel_path 转为 def_type/文件名.xml，
    便于与输出的 rel_path 一致，再按 (key, rel_path) 匹配。
    """
    if not def_translations:
        return def_translations
    result = []
    for item in list(def_translations):
        if len(item) < 4:
            result.append(item)
            continue
        key, text, tag, rel_path = item[:4]
        rest = item[4:]
        def_type = (item[5] if len(item) >= 6 else None) or (key.split("/", 1)[0] if "/" in key else "")
        orig_rel = (rel_path or "").replace("\\", "/")
        filename = os.path.basename(orig_rel) or (f"{def_type}.xml" if def_type else "def.xml")
        new_rel = f"{def_type}/{filename}" if def_type else rel_path
        result.append((key, text, tag, new_rel) + tuple(rest))
    return result


def strip_def_type_for_definjected_export(def_translations: List[Tuple]) -> List[Tuple]:
    """
    写出 DefInjected 前：key 去除 def_type 前缀，供 XML 使用 def_name.field_path 格式。
    rel_path 由上游保持 def_type/文件名.xml，本函数不改。
    """
    if not def_translations:
        return def_translations
    result = []
    for item in list(def_translations):
        if len(item) < 4:
            result.append(item)
            continue
        key, text, tag, rel_path = item[:4]
        rest = item[4:]
        if "/" in key:
            key = key.split("/", 1)[-1]
        result.append((key, text, tag, rel_path) + tuple(rest))
    return result


def add_def_type_prefix_to_definjected(def_translations: List[Tuple]) -> List[Tuple]:
    """
    合并前：为 DefInjected 的 key 添加 def_type 前缀（从 rel_path 第一段取）。
    key 变为 def_type/def_name.field_path，便于与 Defs 输入按 key 匹配。
    """
    if not def_translations:
        return def_translations
    result = []
    for item in list(def_translations):
        if len(item) < 4:
            result.append(item)
            continue
        key, text, tag, rel_path = item[:4]
        rest = item[4:]
        rp = (rel_path or "").replace("\\", "/").strip()
        def_type = rp.split("/")[0] if "/" in rp else (rp or "")
        if def_type and "/" not in key:
            key = f"{def_type}/{key}"
        result.append((key, text, tag, rel_path) + tuple(rest))
    return result


def apply_if_defs_by_type(
    def_translations: List[Tuple],
    template_structure: Optional[str],
    *,
    data_source_choice: Optional[str] = None,
) -> List[Tuple]:
    """
    当条件满足时应用 def_type 转换，否则原样返回。

    条件：template_structure == "defs_by_type"
    且（无 data_source 要求，或 data_source_choice == "defs_only"）

    Args:
        def_translations: Def 翻译数据
        template_structure: 模板结构
        data_source_choice: 数据来源，仅 incremental 模式需传入；definjected_only 时不转换

    Returns:
        转换后或原样数据
    """
    if not def_translations or (template_structure or "") != "defs_by_type":
        return def_translations
    if data_source_choice is not None and data_source_choice != "defs_only":
        return def_translations
    return convert_def_to_defs_by_type(def_translations)
