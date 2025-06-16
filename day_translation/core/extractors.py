from pathlib import Path
from typing import List, Tuple, Set
import logging
from ..utils.utils import XMLProcessor, get_language_folder_path
from ..utils.config import TranslationConfig
from .filters import ContentFilter
from colorama import Fore, Style

CONFIG = TranslationConfig()

def extract_keyed_translations(mod_dir: str, language: str = CONFIG.source_language) -> List[Tuple[str, str, str, str]]:
    """提取 Keyed 翻译"""
    print(f"{Fore.GREEN}正在提取 Keyed 翻译（模组目录：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    lang_path = get_language_folder_path(language, mod_dir)
    keyed_dir = Path(lang_path) / CONFIG.keyed_dir
    if not keyed_dir.exists():
        print(f"{Fore.YELLOW}Keyed 目录不存在: {keyed_dir}{Style.RESET_ALL}")
        return []
    for xml_file in keyed_dir.rglob("*.xml"):
        tree = processor.parse_xml(str(xml_file))
        if tree:
            for key, text, tag in processor.extract_translations(tree, context="Keyed", filter_func=content_filter.filter_content):
                translations.append((key, text, tag, str(xml_file.relative_to(keyed_dir))))
    print(f"{Fore.GREEN}提取到 {len(translations)} 条 Keyed 翻译{Style.RESET_ALL}")
    return translations

def scan_defs_sync(mod_dir: str, def_types: Set[str] = None, language: str = CONFIG.source_language) -> List[Tuple[str, str, str, str]]:
    """扫描 Defs 目录中的可翻译内容"""
    print(f"{Fore.GREEN}正在扫描 Defs 目录（模组目录：{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")
    processor = XMLProcessor()
    content_filter = ContentFilter(CONFIG)
    translations: List[Tuple[str, str, str, str]] = []
    defs_dir = Path(mod_dir) / "Defs"
    if not defs_dir.exists():
        print(f"{Fore.YELLOW}Defs 目录不存在: {defs_dir}{Style.RESET_ALL}")
        return []
    for xml_file in defs_dir.rglob("*.xml"):
        def_type = xml_file.parent.name.rstrip("Defs")
        if def_types and def_type not in def_types:
            continue
        tree = processor.parse_xml(str(xml_file))
        if tree:
            for key, text, tag in processor.extract_translations(tree, context="DefInjected", filter_func=content_filter.filter_content):
                full_path = f"{def_type}/{key}"
                translations.append((full_path, text, tag, str(xml_file.relative_to(defs_dir))))
    print(f"{Fore.GREEN}提取到 {len(translations)} 条 DefInjected 翻译{Style.RESET_ALL}")
    return translations