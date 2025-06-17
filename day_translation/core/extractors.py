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
    
    print(f"{Fore.CYAN}调试信息 - 语言路径: {lang_path}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}调试信息 - Keyed目录: {keyed_dir}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}调试信息 - 目录是否存在: {keyed_dir.exists()}{Style.RESET_ALL}")
    
    if not keyed_dir.exists():
        print(f"{Fore.YELLOW}Keyed 目录不存在: {keyed_dir}{Style.RESET_ALL}")
        return []
        
    # 查找所有XML文件
    xml_files = list(keyed_dir.rglob("*.xml"))
    print(f"{Fore.CYAN}调试信息 - 找到 {len(xml_files)} 个XML文件{Style.RESET_ALL}")
    
    for xml_file in xml_files:
        print(f"{Fore.CYAN}调试信息 - 处理文件: {xml_file}{Style.RESET_ALL}")
        tree = processor.parse_xml(str(xml_file))
        if tree:
            file_translations = []
            for key, text, tag in processor.extract_translations(tree, context="Keyed", filter_func=content_filter.filter_content):
                file_translations.append((key, text, tag, str(xml_file.relative_to(keyed_dir))))
            print(f"{Fore.CYAN}调试信息 - 从 {xml_file.name} 提取到 {len(file_translations)} 条翻译{Style.RESET_ALL}")
            translations.extend(file_translations)
        else:
            print(f"{Fore.RED}调试信息 - 无法解析XML文件: {xml_file}{Style.RESET_ALL}")
    
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
        print(f"{Fore.YELLOW}Defs 目录不存在: {defs_dir}{Style.RESET_ALL}")
        return []
    
    # 添加调试信息
    xml_files = list(defs_dir.rglob("*.xml"))
    print(f"{Fore.CYAN}调试信息 - 找到 {len(xml_files)} 个Defs XML文件{Style.RESET_ALL}")
    
    for xml_file in xml_files:
        print(f"{Fore.CYAN}调试信息 - 处理文件: {xml_file}{Style.RESET_ALL}")
        tree = processor.parse_xml(str(xml_file))
        if tree:
            root = tree.getroot() if hasattr(tree, 'getroot') else tree
            
            # 查找所有有 defName 的节点（RimWorld 标准）
            def_nodes = []
            for elem in root.iter():
                defname_elem = elem.find("defName")
                if defname_elem is not None and defname_elem.text:
                    def_nodes.append(elem)
            
            print(f"{Fore.CYAN}调试信息 - 在 {xml_file.name} 中找到 {len(def_nodes)} 个定义节点{Style.RESET_ALL}")
            
            for def_node in def_nodes:
                def_type = def_node.tag
                defname_elem = def_node.find("defName")
                
                if defname_elem is None or not defname_elem.text:
                    continue
                    
                def_name = defname_elem.text
                
                # 递归提取可翻译字段
                field_translations = _extract_translatable_fields_recursive(def_node, def_type, def_name, content_filter)
                
                # 转换为标准格式
                for field_path, text, tag in field_translations:
                    full_path = f"{def_type}/{def_name}.{field_path}"
                    translations.append((full_path, text, tag, str(xml_file.relative_to(defs_dir))))
                
                print(f"{Fore.CYAN}调试信息 - 从 {def_name} 提取到 {len(field_translations)} 条翻译{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}调试信息 - 无法解析XML文件: {xml_file}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}提取到 {len(translations)} 条 DefInjected 翻译{Style.RESET_ALL}")
    return translations

def _extract_translatable_fields_recursive(node, def_type: str, def_name: str, content_filter: ContentFilter, 
                                         path: str = "", list_indices: dict = None) -> List[Tuple[str, str, str]]:
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
        current_path = f"{path}.{node_tag}" if path else node_tag
    
    # 检查当前节点的文本内容
    if node.text and node.text.strip():
        # 使用过滤器检查是否应该翻译
        if content_filter.filter_content(current_path, node.text.strip(), "DefInjected"):
            translations.append((current_path, node.text.strip(), node_tag))
    
    # 递归处理子节点
    for child in node:
        child_translations = _extract_translatable_fields_recursive(
            child, def_type, def_name, content_filter, current_path, list_indices.copy()
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
    
    print(f"{Fore.CYAN}调试信息 - 语言路径: {lang_path}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}调试信息 - DefInjected目录: {definjected_dir}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}调试信息 - 目录是否存在: {definjected_dir.exists()}{Style.RESET_ALL}")
    
    if not definjected_dir.exists():
        print(f"{Fore.YELLOW}DefInjected 目录不存在: {definjected_dir}{Style.RESET_ALL}")
        return []
        
    # 查找所有XML文件
    xml_files = list(definjected_dir.rglob("*.xml"))
    print(f"{Fore.CYAN}调试信息 - 找到 {len(xml_files)} 个DefInjected XML文件{Style.RESET_ALL}")
    
    for xml_file in xml_files:
        print(f"{Fore.CYAN}调试信息 - 处理DefInjected文件: {xml_file}{Style.RESET_ALL}")
        tree = processor.parse_xml(str(xml_file))
        if tree:
            file_translations = []
            # DefInjected 文件的结构和 Keyed 文件不同，需要特殊处理
            for key, text, tag in processor.extract_translations(tree, context="DefInjected", filter_func=content_filter.filter_content):
                # 构建相对路径，包含 DefInjected 子目录结构
                rel_path = str(xml_file.relative_to(definjected_dir))
                file_translations.append((key, text, tag, rel_path))
            print(f"{Fore.CYAN}调试信息 - 从 {xml_file.name} 提取到 {len(file_translations)} 条DefInjected翻译{Style.RESET_ALL}")
            translations.extend(file_translations)
        else:
            print(f"{Fore.RED}调试信息 - 无法解析DefInjected XML文件: {xml_file}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}从DefInjected目录提取到 {len(translations)} 条翻译{Style.RESET_ALL}")
    return translations
