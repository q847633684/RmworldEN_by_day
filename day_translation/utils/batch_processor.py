from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from tqdm import tqdm
from colorama import Fore, Style
from ..utils.config_generator import generate_default_config
from ..core.importers import load_translations_from_csv
from ..utils.utils import XMLProcessor, get_language_folder_path, generate_element_key
from ..utils.config import TranslationConfig
from ..core.filters import ContentFilter

CONFIG = TranslationConfig()

class BatchProcessor:
    """批量处理多个模组的翻译任务"""
    def __init__(self, max_workers: int = 10):
        """
        初始化 BatchProcessor

        Args:
            max_workers (int): 最大并发线程数，默认为 10
        """
        self.max_workers = max_workers
        self.processor = XMLProcessor()
        logging.debug(f"初始化 BatchProcessor: max_workers={max_workers}")

    def process_multiple_mods(self, mod_list: List[str], csv_path: str = None, language: str = CONFIG.default_language) -> None:
        """
        批量处理多个模组，生成配置并更新 XML

        Args:
            mod_list (List[str]): 模组目录列表
            csv_path (str, optional): 翻译 CSV 文件路径，默认为 None
            language (str): 目标语言，默认为 CONFIG.default_language
        """
        logging.info(f"批量处理 {len(mod_list)} 个模组")
        print(f"{Fore.BLUE}开始处理 {len(mod_list)} 个模组...{Style.RESET_ALL}")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for mod_dir in mod_list:
                mod_dir = str(Path(mod_dir).resolve())
                logging.debug(f"提交模组任务: {mod_dir}")
                futures.append(executor.submit(self._process_single_mod, mod_dir, csv_path, language))
            for future in tqdm(futures, desc="处理模组", unit="模组"):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"模组处理失败: {e}")
                    print(f"{Fore.RED}❌ 模组处理失败: {e}{Style.RESET_ALL}")
        logging.info(f"批量处理完成: {len(mod_list)} 个模组")
        print(f"{Fore.GREEN}✅ 批量处理完成: {len(mod_list)} 个模组{Style.RESET_ALL}")

    def _process_single_mod(self, mod_dir: str, csv_path: str, language: str) -> None:
        """
        处理单个模组，生成配置并更新 XML

        Args:
            mod_dir (str): 模组目录
            csv_path (str): 翻译 CSV 文件路径
            language (str): 目标语言
        """
        logging.debug(f"处理模组: {mod_dir}, csv_path={csv_path}")
        generate_default_config(os.path.join(mod_dir, "translation_config.json"))
        if csv_path:
            self._update_mod_xml(mod_dir, csv_path, language)

    def _update_mod_xml(self, mod_dir: str, csv_path: str, language: str) -> None:
        """
        更新模组的 XML 文件以应用翻译

        Args:
            mod_dir (str): 模组目录
            csv_path (str): 翻译 CSV 文件路径
            language (str): 目标语言
        """
        logging.debug(f"更新模组 XML: mod_dir={mod_dir}, csv_path={csv_path}")
        translations = load_translations_from_csv(csv_path)
        content_filter = ContentFilter(CONFIG)
        lang_path = get_language_folder_path(language, mod_dir)
        for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
            dir_path = os.path.join(lang_path, dir_name)
            if not os.path.exists(dir_path):
                logging.debug(f"目录不存在，跳过: {dir_path}")
                continue
            for xml_file in Path(dir_path).rglob("*.xml"):
                logging.debug(f"处理 XML 文件: {xml_file}")
                tree = self.processor.parse_xml(str(xml_file))
                if tree and self.processor.update_translations(tree, translations, generate_element_key):
                    self.processor.save_xml(tree, str(xml_file))
                    logging.debug(f"更新 XML 文件: {xml_file}")