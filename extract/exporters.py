"""
翻译导出模块 - RimWorld 模组翻译文件生成与更新

主要功能：
1. DefInjected 翻译文件导出
   - 按原始文件路径结构导出
   - 按 DefType 分类导出
   - 按文件目录结构导出
2. Keyed 翻译模板导出
3. 合并翻译文件的智能更新
   - 保留现有翻译内容
   - 记录翻译变更历史
   - 自动添加英文注释

支持的文件格式：XML（DefInjected）
支持的注释类型：英文原文注释、历史变更注释
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict
from utils.logging_config import get_logger
from utils.config import (
    get_config,
    get_language_subdir,
)
from utils.utils import sanitize_xml, XMLProcessor

CONFIG = get_config()


def export_definjected_with_original_structure(
    output_dir,
    output_language,
    def_translations: list,
) -> None:
    """按 file_path 创建目录和文件结构导出 DefInjected 翻译，key 作为标签名，text 作为内容"""
    logger = get_logger(f"{__name__}.export_definjected_with_original_structure")

    logger.debug(
        "按 file_path 结构导出 DefInjected: output_dir=%s, translations_count=%s",
        output_dir,
        len(def_translations),
    )

    def_injected_path = get_language_subdir(
        base_dir=output_dir, language=output_language, subdir_type="defInjected"
    )

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logger.debug("创建文件夹：%s", def_injected_path)
    # 按 file_path 分组翻译数据
    file_groups: Dict[str, List[Tuple[str, str, str]]] = (
        {}
    )  # {file_path: [(key, text, tag), ...]}

    for item in def_translations:
        k, t, g, f = item[:4]
        if f not in file_groups:
            file_groups[f] = []
        file_groups[f].append((k, t, g))

    logger.debug("按 file_path 分组完成: %s 个文件", len(file_groups))

    # 为每个 file_path 生成翻译文件
    for file_path, translations in file_groups.items():
        if not translations:
            continue

        # 创建对应的目录结构
        output_file = os.path.join(def_injected_path, file_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 生成 XML 内容
        processor = XMLProcessor()
        root = processor.create_element("LanguageData")

        # 按键名排序，保持一致性
        for key, text, _ in sorted(translations, key=lambda x: x[0]):  # tag 未使用
            # 添加英文注释
            comment = processor.create_comment(f"EN: {text}")
            root.append(comment)

            # 添加翻译元素
            processor.create_subelement(root, key, text)

        # 保存文件
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logger.debug(
                "生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations)
            )
        else:
            logger.error("写入失败: %s", output_file)


def export_definjected_with_defs_structure(
    output_dir: str,
    output_language: str,
    def_translations: list,
) -> None:
    """按照按DefType分组导出DefInjected翻译"""
    logger = get_logger(f"{__name__}.export_definjected_with_defs_structure")
    logger.debug(
        "按Defs结构导出 DefInjected: output_dir=%s, translations_count=%s",
        output_dir,
        len(def_translations),
    )

    def_injected_path = get_language_subdir(
        base_dir=output_dir, language=output_language, subdir_type="defInjected"
    )

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logger.debug("创建文件夹：%s", def_injected_path)

    # 按DefType分组翻译内容（基于 full_path 中的 def_type 信息）
    file_groups: Dict[str, List[Tuple[str, str, str]]] = {}

    for item in def_translations:
        full_path, text, tag, _ = item[:4]  # rel_path 未使用
        # 从 full_path 生成键名和提取 def_type
        if "/" in full_path:
            def_type_part, field_part = full_path.split("/", 1)
            if "." in field_part:
                def_name, field_path = field_part.split(".", 1)
                full_key = f"{def_name}.{field_path}"
            else:
                full_key = field_part

            # 清理 def_type 名称
            if "." in def_type_part:
                def_type = def_type_part.split(".")[-1]
            else:
                def_type = def_type_part
        else:
            full_key = full_path
            def_type = "UnknownDef"

        # 使用 def_type 作为分组依据
        if def_type not in file_groups:
            file_groups[def_type] = []
        file_groups[def_type].append((full_key, text, tag))

    logger.debug("按DefType分组完成: %s 个类型", len(file_groups))

    # 为每个 DefType 生成 XML 文件
    for def_type, translations in file_groups.items():
        if not translations:
            continue

        # 创建对应的目录结构
        type_dir = os.path.join(def_injected_path, f"{def_type}Defs")
        os.makedirs(type_dir, exist_ok=True)

        output_file = os.path.join(type_dir, f"{def_type}Defs.xml")

        # 生成 XML 内容
        processor = XMLProcessor()
        root = processor.create_element("LanguageData")

        # 按键名排序，保持一致性
        for full_key, text, _ in sorted(translations, key=lambda x: x[0]):  # tag 未使用
            # 添加英文注释
            comment = processor.create_comment(f"EN: {text}")
            root.append(comment)

            # 添加翻译元素
            processor.create_subelement(root, full_key, text)

        # 保存文件
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logger.debug(
                "生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations)
            )
        else:
            logger.error("写入失败: %s", output_file)


def export_definjected_with_file_structure(
    output_dir: str,
    output_language: str,
    def_translations: list,
) -> None:
    """按原始Defs文件目录结构导出DefInjected翻译，key 结构为 DefType/defName.字段，导出时去除 DefType/ 只保留 defName.字段作为标签名，目录结构用 rel_path，内容用 text。"""
    logger = get_logger(f"{__name__}.export_definjected_with_file_structure")
    logger.debug(
        "按文件结构导出 DefInjected: output_dir=%s, translations_count=%s",
        output_dir,
        len(def_translations),
    )

    def_injected_path = get_language_subdir(
        base_dir=output_dir, language=output_language, subdir_type="defInjected"
    )

    if not os.path.exists(def_injected_path):
        os.makedirs(def_injected_path)
        logger.debug("创建文件夹：%s", def_injected_path)

    file_groups: Dict[str, List[Tuple[str, str, str]]] = {}
    for item in def_translations:
        key, text, tag, rel_path = item[:4]
        if rel_path not in file_groups:
            file_groups[rel_path] = []
        file_groups[rel_path].append((key, text, tag))

    logger.debug("按文件结构分组完成: %s 个文件", len(file_groups))

    for rel_path, translations in file_groups.items():
        if not translations:
            continue
        output_file = os.path.join(def_injected_path, rel_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        processor = XMLProcessor()
        root = processor.create_element("LanguageData")

        for key, text, _ in sorted(translations, key=lambda x: x[0]):  # tag 未使用
            if text is None:
                text = ""
            assert isinstance(text, str), f"text 非字符串: {text}"
            # 去除 DefType/ 只保留 defName.字段
            if "/" in key:
                _, tag_name = key.split("/", 1)
            else:
                tag_name = key
            # 合法性修复：只允许字母、数字、下划线、点号，其它替换为点号
            tag_name = re.sub(r"[^A-Za-z0-9_.]", ".", tag_name)
            if not re.match(r"^[A-Za-z_]", tag_name):
                tag_name = "_" + tag_name
            # 添加英文注释
            comment = processor.create_comment(f"EN: {text}")
            root.append(comment)
            # 添加翻译元素
            processor.create_subelement(root, tag_name, text)

        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logger.debug(
                "生成 DefInjected 文件: %s (%s 条翻译)", output_file, len(translations)
            )
        else:
            logger.error("写入失败: %s", output_file)


def export_keyed_template(
    output_dir: str,
    output_language: str,
    def_translations: list,
) -> None:
    """导出 Keyed 翻译模板，按文件分组生成 XML 文件"""
    logger = get_logger(f"{__name__}.export_keyed_template")
    logger.debug(
        "导出 Keyed 翻译模板: output_dir=%s, translations_count=%s",
        output_dir,
        len(def_translations),
    )

    keyed_path = get_language_subdir(
        base_dir=output_dir, language=output_language, subdir_type="keyed"
    )

    if not os.path.exists(keyed_path):
        os.makedirs(keyed_path)
        logger.info("创建文件夹：%s", keyed_path)

    # 按 file_path 分组翻译数据
    file_groups: Dict[str, List[Tuple[str, str, str]]] = (
        {}
    )  # {file_path: [(key, text, tag), ...]}

    for item in def_translations:
        key, text, tag, file_path = item[:4]
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append((key, text, tag))

    logger.debug("按文件分组完成: %s 个文件", len(file_groups))

    # 为每个 file_path 生成翻译文件
    for file_path, translations in file_groups.items():
        if not translations:
            continue

        # 创建目标文件路径（只保留文件名）
        output_file = os.path.join(keyed_path, Path(file_path).name)

        # 生成 XML 内容
        processor = XMLProcessor()
        root = processor.create_element("LanguageData")

        # 按键名排序，保持一致性
        for key, text, _ in sorted(translations, key=lambda x: x[0]):  # tag 未使用
            # 添加英文注释
            comment = processor.create_comment(f"EN: {text}")
            root.append(comment)

            # 添加翻译元素
            processor.create_subelement(root, key, text)

        # 保存文件
        ok = processor.save_xml(root, output_file, pretty_print=True)
        if ok:
            logger.debug(
                "生成 Keyed 文件: %s (%s 条翻译)", output_file, len(translations)
            )
        else:
            logger.error("写入失败: %s", output_file)


def write_merged_translations(merged, output_dir, output_language, sub_dir) -> None:
    """
    通用写回 XML 方法，支持 DefInjected 和 Keyed。
    merged: List[(key, test, tag, rel_path, en_test, history)]
    output_dir: 输出根目录
    sub_dir: 子目录名（DefInjected 或 Keyed）
    """
    logger = get_logger(f"{__name__}.write_merged_translations")

    base_dir = get_language_subdir(
        base_dir=output_dir, language=output_language, subdir_type=sub_dir
    )
    # 1. 按 rel_path 分组
    file_groups: dict[str, list] = {}
    for item in merged:
        rel_path = item[3]
        file_groups.setdefault(rel_path, []).append(item)
    processor = XMLProcessor()
    for rel_path, items in file_groups.items():
        output_file = base_dir / rel_path
        # 检查文件是否已存在
        if output_file.exists():
            # 读取现有XML文件
            existing_tree = processor.parse_xml(str(output_file))
            if existing_tree is not None:
                root = existing_tree.getroot()
                logger.info("更新现有文件: %s", output_file)
            else:
                # 文件存在但解析失败，创建新的
                logger.warning("无法解析现有文件，将重新创建: %s", output_file)
                root = processor.create_element("LanguageData")
                output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # 文件不存在，创建新文件和目录
            logger.info("创建新文件: %s", output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            root = processor.create_element("LanguageData")
        # 更新或添加翻译条目
        for key, test, _, _, en_test, history in sorted(items, key=lambda x: x[0]):
            # 查找现有元素
            existing_elem = root.find(key)
            if existing_elem is not None:
                # 更新现有元素
                original_text = existing_elem.text or ""
                if original_text != test:
                    # 添加历史注释
                    if history and history.strip():
                        history_comment = processor.create_comment(history)  # 创建注释
                        elem_index = list(root).index(existing_elem)
                        root.insert(elem_index, history_comment)
                existing_elem.text = sanitize_xml(test)
            else:
                # 添加新元素
                # 先添加历史注释（如果有，且不为空）
                if history and history.strip():
                    history_comment = processor.create_comment(
                        f"HISTORY: 原翻译内容：{history}，替换于YYYY-MM-DD"
                    )
                    root.append(history_comment)

                # 添加英文注释（如果有）
                if en_test:
                    en_comment = processor.create_comment(f"EN: {en_test}")
                    root.append(en_comment)

                # 创建新的翻译元素
                processor.create_subelement(root, key, test)

        # 保存更新后的文件
        success = processor.save_xml(root, output_file, pretty_print=True)
        if success:
            logger.info("成功保存文件: %s (%s 条翻译)", output_file, len(items))
        else:
            logger.error("保存文件失败: %s", output_file)
