"""
增强的翻译导入功能 - 实现将翻译CSV导入到翻译模板（任务3）
"""

from pathlib import Path
from typing import Dict, Optional
import logging
import os
from colorama import Fore, Style
from ..utils.utils import XMLProcessor, XMLProcessorConfig, get_language_folder_path, handle_exceptions
from ..utils.config import get_config

CONFIG = get_config()

def update_all_xml(mod_dir: str, translations: Dict[str, str], language: str = CONFIG.default_language, merge: bool = True) -> None:
    """
    更新所有 XML 文件中的翻译
    
    Args:
        mod_dir (str): 模组目录
        translations (Dict[str, str]): 翻译字典
        language (str): 目标语言
        merge (bool): 是否合并更新
    """
    try:
        # 尝试使用 lxml
        processor = XMLProcessor(XMLProcessorConfig(use_lxml=True))
    except ImportError:
        # 回退到 ElementTree
        processor = XMLProcessor(XMLProcessorConfig(use_lxml=False))
        
    language_dir = get_language_folder_path(mod_dir, language)
    updated_count = 0
    
    for xml_file in Path(language_dir).rglob("*.xml"):
        try:
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                continue
                
            if processor.update_translations(tree, translations, merge=merge):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1
                print(f"{Fore.GREEN}更新文件: {xml_file}{Style.RESET_ALL}")
        except Exception as e:
            logging.error("处理文件失败: %s: %s", xml_file, e)
            
    print(f"{Fore.GREEN}更新了 {updated_count} 个文件{Style.RESET_ALL}")

@handle_exceptions()
def import_translations(csv_path: str, mod_dir: str, language: str = CONFIG.default_language, merge: bool = True) -> bool:
    """
    将翻译CSV导入到翻译模板
    
    Args:
        csv_path (str): 翻译CSV文件路径
        mod_dir (str): 模组目录路径
        language (str): 目标语言
        merge (bool): 是否合并现有翻译
        
    Returns:
        bool: 导入是否成功
    """
    try:
        # 直接调用本模块的 update_all_xml 函数，统一使用 XMLProcessor 处理 XML 更新
        update_all_xml(mod_dir, load_translations_from_csv(csv_path), language, merge)
        return True
    except Exception as e:
        logging.error("导入翻译时发生错误: %s", e, exc_info=True)
        print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")
        return False

def load_translations_from_csv(csv_path: str) -> Dict[str, str]:
    """从 CSV 加载翻译"""
    import csv
    translations = {}
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("key", "").strip()
                translated = row.get("translated", row.get("text", "")).strip()
                if key and translated:
                    translations[key] = translated
    except Exception as e:
        print(f"{Fore.RED}CSV 解析失败: {csv_path}: {e}{Style.RESET_ALL}")
    return translations