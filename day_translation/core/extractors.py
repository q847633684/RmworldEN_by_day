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
    
    logging.debug(f"语言路径: {lang_path}")
    logging.debug(f"Keyed目录: {keyed_dir}")
    logging.debug(f"目录是否存在: {keyed_dir.exists()}")
    
    if not keyed_dir.exists():
        logging.warning(f"Keyed 目录不存在: {keyed_dir}")
        return []
        
    # 查找所有XML文件
    xml_files = list(keyed_dir.rglob("*.xml"))
    logging.debug(f"找到 {len(xml_files)} 个XML文件")
    
    for xml_file in xml_files:
        logging.debug(f"处理文件: {xml_file}")
        tree = processor.parse_xml(str(xml_file))
        if tree:
            file_translations = []
            for key, text, tag in processor.extract_translations(tree, context="Keyed", filter_func=content_filter.filter_content):
                file_translations.append((key, text, tag, str(xml_file.relative_to(keyed_dir))))
            logging.debug(f"从 {xml_file.name} 提取到 {len(file_translations)} 条翻译")
            translations.extend(file_translations)
        else:
            logging.error(f"无法解析XML文件: {xml_file}")
    
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
        logging.warning(f"Defs 目录不存在: {defs_dir}")
        return []
    
    # 添加调试信息
    xml_files = list(defs_dir.rglob("*.xml"))
    logging.debug(f"找到 {len(xml_files)} 个Defs XML文件")
    
    for xml_file in xml_files:
        logging.debug(f"处理文件: {xml_file}")
        tree = processor.parse_xml(str(xml_file))
        if tree:
            root = tree.getroot() if hasattr(tree, 'getroot') else tree
            
            # 查找所有有 defName 的节点（RimWorld 标准）
            def_nodes = []
            for elem in root.iter():
                defname_elem = elem.find("defName")
                if defname_elem is not None and defname_elem.text:
                    def_nodes.append(elem)
            
            logging.debug(f"在 {xml_file.name} 中找到 {len(def_nodes)} 个定义节点")
            
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
                
                logging.debug(f"从 {def_name} 提取到 {len(field_translations)} 条翻译")
        else:
            logging.error(f"无法解析XML文件: {xml_file}")
    
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
            logging.warning(f"获取 default_fields 失败: {e}")
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
    """从 DefInjected 目录提取翻译数据"""
    print(f"{Fore.GREEN}正在从 DefInjected 目录提取翻译数据（模组目录：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    lang_path = get_language_folder_path(language, mod_dir)
    definjected_dir = Path(lang_path) / CONFIG.def_injected_dir
    
    logging.debug(f"语言路径: {lang_path}")
    logging.debug(f"DefInjected目录: {definjected_dir}")
    logging.debug(f"目录是否存在: {definjected_dir.exists()}")
    
    if not definjected_dir.exists():
        logging.warning(f"DefInjected 目录不存在: {definjected_dir}")
        return []
        
    # 查找所有XML文件
    xml_files = list(definjected_dir.rglob("*.xml"))
    logging.debug(f"找到 {len(xml_files)} 个DefInjected XML文件")
    
    for xml_file in xml_files:
        logging.debug(f"处理DefInjected文件: {xml_file}")
        tree = processor.parse_xml(str(xml_file))
        if tree:
            file_translations = []
            # DefInjected 文件的结构和 Keyed 文件不同，需要特殊处理
            for key, text, tag in processor.extract_translations(tree, context="DefInjected", filter_func=content_filter.filter_content):
                # 构建相对路径，包含 DefInjected 子目录结构
                rel_path = str(xml_file.relative_to(definjected_dir))
                file_translations.append((key, text, tag, rel_path))
            logging.debug(f"从 {xml_file.name} 提取到 {len(file_translations)} 条DefInjected翻译")
            translations.extend(file_translations)
        else:
            logging.error(f"无法解析DefInjected XML文件: {xml_file}")
    
    print(f"{Fore.GREEN}从DefInjected目录提取到 {len(translations)} 条翻译{Style.RESET_ALL}")
    return translations
