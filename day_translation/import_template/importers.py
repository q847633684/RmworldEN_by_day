"""
导入功能模块 - 实现翻译结果导入到模板的功能
"""

import logging
import os
import csv
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from colorama import Fore, Style

from day_translation.utils.config import get_config
from day_translation.utils.utils import XMLProcessor, get_language_folder_path

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
