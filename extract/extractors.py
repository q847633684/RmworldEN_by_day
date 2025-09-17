"""
RimWorld 翻译提取器模块

本模块提供从 RimWorld 模组中提取可翻译内容的功能，包括：
- 从 Keyed 目录提取键值对翻译
- 从 Defs 目录扫描定义文件中的可翻译字段
- 从 DefInjected 目录提取已注入的翻译结构

主要功能：
- extract_keyed_translations: 提取 Keyed 翻译
- scan_defs_sync: 扫描 Defs 目录中的可翻译内容
- extract_definjected_translations: 提取 DefInjected 翻译结构
"""

import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from colorama import Fore, Style  # type: ignore
from utils.utils import XMLProcessor
from utils.config import (
    get_config,
    get_language_subdir,
)
from utils.filters import ContentFilter


CONFIG = get_config()


def extract_keyed_translations(
    import_dir: str, import_language
) -> List[Tuple[str, str, str, str]]:
    """提取 Keyed 翻译"""
    print(
        f"{Fore.GREEN}正在扫描 Keyed 目录（模组目录：{import_dir}, 语言：{import_language}）...{Style.RESET_ALL}"
    )
    logging.info(
        "正在扫描 Keyed 目录（模组目录：%s, 语言：%s）...", import_dir, import_language
    )
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    keyed_dir = get_language_subdir(
        base_dir=import_dir, language=import_language, subdir_type="keyed"
    )
    print(f"   ✅ 获取 Keyed 目录: {keyed_dir}")
    # 添加调试信息
    logging.debug("Keyed目录: %s", keyed_dir)
    logging.debug("目录是否存在: %s", keyed_dir.exists())

    if not keyed_dir.exists():
        logging.warning("Keyed 目录不存在: %s", keyed_dir)
        return []

    # 查找所有XML文件
    xml_files = list(keyed_dir.rglob("*.xml"))
    logging.debug("找到 %s 个XML文件", len(xml_files))

    for xml_file in xml_files:
        logging.debug("处理文件: %s", xml_file)
        tree = processor.parse_xml(str(xml_file))
        if tree:
            file_translations = []
            for key, text, tag in processor.extract_translations(
                tree, context="Keyed", filter_func=content_filter.filter_content
            ):
                file_translations.append(
                    (key, text, tag, str(xml_file.relative_to(keyed_dir)))
                )
            logging.debug(
                "从 %s 提取到 %s 条翻译", xml_file.name, len(file_translations)
            )
            translations.extend(file_translations)
        else:
            logging.error("无法解析XML文件: %s", xml_file)
    return translations


def scan_defs_sync(import_dir) -> List[Tuple[str, str, str, str]]:
    """扫描 Defs 目录中的可翻译内容（参考 Day_EN 完整实现）"""
    print(
        f"{Fore.GREEN}正在扫描 Defs 目录（模组目录：{import_dir}）...{Style.RESET_ALL}"
    )
    logging.info("正在扫描 Defs 目录（模组目录：%s）...", import_dir)
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    defs_dir = Path(import_dir) / "Defs"
    print(f"   ✅ 获取 Defs 目录: {defs_dir}")
    logging.debug("Defs目录: %s", defs_dir)
    logging.debug("目录是否存在: %s", defs_dir.exists())
    if not defs_dir.exists():
        logging.warning("Defs 目录不存在: %s", defs_dir)
        return []

    # 添加调试信息
    xml_files = list(defs_dir.rglob("*.xml"))
    logging.debug("找到 %s 个Defs XML文件", len(xml_files))

    for xml_file in xml_files:
        logging.debug("处理文件: %s", xml_file)
        tree = processor.parse_xml(str(xml_file))
        if tree:
            root = tree.getroot() if hasattr(tree, "getroot") else tree

            # 查找所有有 defName 的节点（RimWorld 标准）
            def_nodes = []
            for elem in root.iter():
                defname_elem = elem.find("defName")
                if defname_elem is not None and defname_elem.text:
                    def_nodes.append(elem)

            logging.debug("在 %s 中找到 %s 个定义节点", xml_file.name, len(def_nodes))

            for def_node in def_nodes:
                def_type = def_node.tag
                defname_elem = def_node.find("defName")

                if defname_elem is None or not defname_elem.text:
                    continue

                def_name = (
                    defname_elem.text
                )  # 递归提取可翻译字段，传递 def_type 作为初始父标签
                field_translations = _extract_translatable_fields_recursive(
                    def_node, def_type, def_name, content_filter, "", {}, def_type
                )

                # 转换为标准格式，清理重复的 def_type（参考 Day_EN 实现）
                for field_path, text, tag in field_translations:
                    # 清理路径中重复的 def_type 前缀
                    clean_path = field_path
                    if clean_path.startswith(def_type + "."):
                        clean_path = clean_path[len(def_type) + 1 :]

                    full_path = f"{def_type}/{def_name}.{clean_path}"
                    rel_path = str(xml_file.relative_to(defs_dir))
                    translations.append((full_path, text, tag, rel_path))

                logging.debug(
                    "从 %s 提取到 %s 条翻译", def_name, len(field_translations)
                )
        else:
            logging.error("无法解析XML文件: %s", xml_file)
    return translations


def _extract_translatable_fields_recursive(
    node,
    def_type: str,
    def_name: str,
    content_filter: ContentFilter,
    path: str = "",
    list_indices: Optional[Dict[str, int]] = None,
    parent_tag: Optional[str] = None,
) -> List[Tuple[str, str, str]]:
    """递归提取可翻译字段（参考 Day_EN 实现）"""
    if list_indices is None:
        list_indices = {}

    translations: List[Tuple[str, str, str]] = []
    node_tag = node.tag

    # 跳过 defName 节点
    if node_tag == "defName":
        return translations

    # 构建当前路径
    if node_tag == "li":
        # 处理列表项索引
        index_key = f"{path}|li"
        if index_key in list_indices:
            list_indices[index_key] += 1
        else:
            list_indices[index_key] = 0
        current_path = (
            f"{path}.{list_indices[index_key]}"
            if path
            else str(list_indices[index_key])
        )
    else:
        current_path = (
            f"{path}.{node_tag}" if path else node_tag
        )  # 检查当前节点的文本内容 - 使用 Day_EN 的 li 特殊处理逻辑
    if node.text and node.text.strip():
        should_extract = False

        # 安全获取默认字段集合，确保都是字符串
        try:
            default_fields = content_filter.default_fields or set()
            default_fields_lower = set()
            if hasattr(default_fields, "__iter__"):
                for f in default_fields:
                    if isinstance(f, str):
                        default_fields_lower.add(f.lower())
        except (AttributeError, TypeError, ValueError) as e:
            logging.warning("获取 default_fields 失败: %s", e)
            default_fields_lower = set()

        if node_tag == "li":
            # li 节点特殊处理：只有当父标签在默认字段中时才提取
            if (
                parent_tag
                and isinstance(parent_tag, str)
                and parent_tag.lower() in default_fields_lower
            ):
                should_extract = True
        else:
            # 非 li 节点：检查当前标签是否在默认字段中
            if isinstance(node_tag, str) and node_tag.lower() in default_fields_lower:
                should_extract = True

        if should_extract and content_filter.filter_content(
            current_path, node.text.strip(), "DefInjected"
        ):
            translations.append((current_path, node.text.strip(), node_tag))

    # 递归处理子节点 - 传递父标签信息
    for child in node:
        if child.tag == "li":
            # li 子节点传递当前节点作为父标签，但保持 list_indices 引用
            child_translations = _extract_translatable_fields_recursive(
                child,
                def_type,
                def_name,
                content_filter,
                current_path,
                list_indices,
                parent_tag=node_tag,
            )
        else:
            # 非 li 子节点复制 list_indices，传递当前节点作为父标签
            child_translations = _extract_translatable_fields_recursive(
                child,
                def_type,
                def_name,
                content_filter,
                current_path,
                list_indices.copy(),
                parent_tag=node_tag,
            )
        translations.extend(child_translations)

    return translations


def extract_definjected_translations(
    import_dir,
    import_language,
) -> List[Tuple[str, str, str, str, str]]:
    """
    从 DefInjected 目录提取翻译结构，支持提取 EN 注释

    Args:
        mod_dir: 模组目录路径
        language: 语言代码

    Returns:
        返回五元组 List[Tuple[key, test, tag, rel_path, en_test]]
    """
    print(
        f"{Fore.GREEN}正在扫描 DefInjected 目录（模组目录：{import_dir}, 语言：{import_language}）...{Style.RESET_ALL}"
    )
    logging.info(
        "正在扫描 DefInjected 目录（模组目录：%s, 语言：%s）...",
        import_dir,
        import_language,
    )
    translations = []
    definjected_dir = get_language_subdir(
        base_dir=import_dir, language=import_language, subdir_type="defInjected"
    )
    print(f"   ✅ 获取 DefInjected 目录: {definjected_dir}")
    logging.debug("DefInjected目录: %s", definjected_dir)
    logging.debug("目录是否存在: %s", definjected_dir.exists())

    if not definjected_dir.exists():
        return []

    xml_files = list(definjected_dir.rglob("*.xml"))
    for xml_file in xml_files:
        try:
            tree = XMLProcessor().parse_xml(str(xml_file))
            if tree is None:
                logging.warning("无法解析XML文件: %s", xml_file)
                continue
            root = tree.getroot()
            rel_path = str(xml_file.relative_to(definjected_dir))
            last_en_comment = ""
            for elem in root.iter():
                if elem is root:
                    continue  # 跳过根节点
                if type(elem).__name__ == "Comment":
                    text = elem.text or ""
                    if text.strip().startswith("EN:"):
                        last_en_comment = text.strip()[3:].strip()
                elif isinstance(elem.tag, str) and not elem.tag.startswith("{"):
                    # key生成逻辑与原函数一致
                    parent_tags = []
                    # 获取父标签
                    parent = elem.getparent()
                    while parent is not None and parent.tag != root.tag:
                        # 获取父标签 并添加到列表中
                        parent_tags.append(parent.tag)
                        parent = parent.getparent()
                    # 反转列表
                    parent_tags = list(reversed(parent_tags))
                    # 生成key
                    key = (
                        "/".join(parent_tags + [elem.tag]) if parent_tags else elem.tag
                    )
                    # 生成test
                    test = elem.text or ""
                    # 生成tag
                    tag = elem.tag
                    # 添加到列表中，始终返回五元组，包含 EN 注释
                    translations.append((key, test, tag, rel_path, last_en_comment))  # type: ignore
                    # 清空注释
                    last_en_comment = ""
        except (OSError, ValueError, AttributeError) as e:
            logging.error("处理DefInjected文件时发生错误: %s", e)
            continue
    return translations  # type: ignore
