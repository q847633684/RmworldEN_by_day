from pathlib import Path
from typing import List, Tuple, Set
import logging
from ..utils.utils import XMLProcessor, get_language_folder_path
from ..utils.config import get_config
from ..utils.filters import ContentFilter
from colorama import Fore, Style

CONFIG = get_config()

def extract_keyed_translations(mod_dir: str, language: str = CONFIG.source_language) -> List[Tuple[str, str, str, str]]:
    """提取 Keyed 翻译"""
    print(f"{Fore.GREEN}正在提取 Keyed 翻译（模组目录：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    lang_path = get_language_folder_path(language, mod_dir)
    keyed_dir = Path(lang_path) / CONFIG.keyed_dir
    # 添加调试信息  
    logging.debug("语言路径: %s", lang_path)
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
            for key, text, tag in processor.extract_translations(tree, context="Keyed", filter_func=content_filter.filter_content):
                file_translations.append((key, text, tag, str(xml_file.relative_to(keyed_dir))))
            logging.debug("从 %s 提取到 %s 条翻译", xml_file.name, len(file_translations))
            translations.extend(file_translations)
        else:
            logging.error("无法解析XML文件: %s", xml_file)

    print(f"{Fore.GREEN}提取到 {len(translations)} 条 Keyed 翻译{Style.RESET_ALL}")
    return translations

def scan_defs_sync(mod_dir: str, def_types: Set[str] = None, language: str = CONFIG.source_language) -> List[Tuple[str, str, str, str]]:
    """扫描 Defs 目录中的可翻译内容（参考 Day_EN 完整实现）"""
    print(f"{Fore.GREEN}正在扫描 Defs 目录（模组目录：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    defs_dir = Path(mod_dir) / "Defs"

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
            root = tree.getroot() if hasattr(tree, 'getroot') else tree

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

                def_name = defname_elem.text                # 递归提取可翻译字段，传递 def_type 作为初始父标签
                field_translations = _extract_translatable_fields_recursive(def_node, def_type, def_name, content_filter, "", None, def_type)

                # 转换为标准格式，清理重复的 def_type（参考 Day_EN 实现）
                for field_path, text, tag in field_translations:
                    # 清理路径中重复的 def_type 前缀
                    clean_path = field_path
                    if clean_path.startswith(def_type + "."):
                        clean_path = clean_path[len(def_type) + 1:]

                    full_path = f"{def_type}/{def_name}.{clean_path}"
                    translations.append((full_path, text, tag, str(xml_file.relative_to(defs_dir))))

                logging.debug("从 %s 提取到 %s 条翻译", def_name, len(field_translations))
        else:
            logging.error("无法解析XML文件: %s", xml_file)

    print(f"{Fore.GREEN}提取到 {len(translations)} 条 DefInjected 翻译{Style.RESET_ALL}")
    return translations

def _extract_translatable_fields_recursive(node, def_type: str, def_name: str, content_filter: ContentFilter,
                                         path: str = "", list_indices: dict = None, parent_tag: str = None) -> List[Tuple[str, str, str]]:
    """递归提取可翻译字段（参考 Day_EN 实现）"""
    if list_indices is None:
        list_indices = {}

    translations = []
    node_tag = node.tag

    # 跳过 defName 节点
    if node_tag == 'defName':
        return translations

    # 构建当前路径
    if node_tag == 'li':
        # 处理列表项索引
        index_key = f"{path}|li"
        if index_key in list_indices:
            list_indices[index_key] += 1
        else:
            list_indices[index_key] = 0
        current_path = f"{path}.{list_indices[index_key]}" if path else str(list_indices[index_key])
    else:
        current_path = f"{path}.{node_tag}" if path else node_tag    # 检查当前节点的文本内容 - 使用 Day_EN 的 li 特殊处理逻辑
    if node.text and node.text.strip():
        should_extract = False

        # 安全获取默认字段集合，确保都是字符串
        try:
            default_fields = content_filter.default_fields or set()
            default_fields_lower = set()
            if hasattr(default_fields, '__iter__'):
                for f in default_fields:
                    if isinstance(f, str):
                        default_fields_lower.add(f.lower())
        except Exception as e:
            logging.warning("获取 default_fields 失败: %s", e)
            default_fields_lower = set()

        if node_tag == 'li':
            # li 节点特殊处理：只有当父标签在默认字段中时才提取
            if parent_tag and isinstance(parent_tag, str) and parent_tag.lower() in default_fields_lower:
                should_extract = True
        else:
            # 非 li 节点：检查当前标签是否在默认字段中
            if isinstance(node_tag, str) and node_tag.lower() in default_fields_lower:
                should_extract = True

        if should_extract and content_filter.filter_content(current_path, node.text.strip(), "DefInjected"):
            translations.append((current_path, node.text.strip(), node_tag))

    # 递归处理子节点 - 传递父标签信息
    for child in node:
        if child.tag == 'li':
            # li 子节点传递当前节点作为父标签，但保持 list_indices 引用
            child_translations = _extract_translatable_fields_recursive(
                child, def_type, def_name, content_filter, current_path, list_indices, parent_tag=node_tag
            )
        else:
            # 非 li 子节点复制 list_indices，传递当前节点作为父标签
            child_translations = _extract_translatable_fields_recursive(
                child, def_type, def_name, content_filter, current_path, list_indices.copy(), parent_tag=node_tag
            )
        translations.extend(child_translations)

    return translations

def extract_definjected_translations(mod_dir: str, language: str = CONFIG.source_language) -> List[Tuple[str, str, str, str]]:
    """
    从 DefInjected 目录提取翻译结构，生成模板数据

    这个函数的目的是以英文DefInjected的结构为基础，生成翻译模板的占位符数据。
    提供两种模式：
    1. 保留英文原文作为参考（带标记）
    2. 生成空白占位符（便于翻译）
    """
    print(f"{Fore.GREEN}正在以英文 DefInjected 结构为基础生成模板（模组目录：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    lang_path = get_language_folder_path(language, mod_dir)
    definjected_dir = Path(lang_path) / CONFIG.def_injected_dir

    logging.debug("语言路径: %s", lang_path)
    logging.debug("DefInjected目录: %s", definjected_dir)
    logging.debug("目录是否存在: %s", definjected_dir.exists())

    if not definjected_dir.exists():
        logging.warning("DefInjected 目录不存在: %s", definjected_dir)
        return []

    # 查找所有XML文件
    xml_files = list(definjected_dir.rglob("*.xml"))
    logging.debug("找到 %s 个DefInjected XML文件", len(xml_files))

    for xml_file in xml_files:
        logging.debug("处理DefInjected文件: %s", xml_file)
        tree = processor.parse_xml(str(xml_file))
        if tree:
            file_translations = []
            # DefInjected 文件的结构和 Keyed 文件不同，需要特殊处理
            for key, text, tag in processor.extract_translations(tree, context="DefInjected", filter_func=content_filter.filter_content):
                # 构建相对路径，包含 DefInjected 子目录结构
                rel_path = str(xml_file.relative_to(definjected_dir))

                # 生成模板内容：保留英文原文作为翻译参考，同时明确标记为待翻译
                # 格式："[待翻译] 英文原文" - 这样用户能清楚看到原文并知道需要翻译
                template_text = f"[待翻译] {text}"
                file_translations.append((key, template_text, tag, rel_path))
            logging.debug("从 %s 提取到 %s 条DefInjected模板", xml_file.name, len(file_translations))
            translations.extend(file_translations)
        else:
            logging.error("无法解析DefInjected XML文件: %s", xml_file)

    print(f"{Fore.GREEN}以英文DefInjected结构为基础生成 {len(translations)} 条模板{Style.RESET_ALL}")
    return translations
