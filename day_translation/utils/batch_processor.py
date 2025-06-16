from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from ..utils.config_generator import generate_default_config
from ..core.importers import load_translations_from_csv
from ..utils.utils import XMLProcessor, get_language_folder_path, generate_element_key
from ..utils.config import TranslationConfig
from ..core.filters import ContentFilter

CONFIG = TranslationConfig()

class BatchProcessor:
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.processor = XMLProcessor()

    def process_multiple_mods(self, mod_list: List[str], csv_path: str = None, language: str = CONFIG.default_language) -> None:
        """批量处理多个模组"""
        logging.info(f"批量处理 {len(mod_list)} 个模组")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for mod_dir in mod_list:
                mod_dir = str(Path(mod_dir).resolve())
                executor.submit(generate_default_config, os.path.join(mod_dir, "translation_config.json"))
                if csv_path:
                    executor.submit(self._update_mod_xml, mod_dir, csv_path, language)
        logging.info(f"批量处理完成: {len(mod_list)} 个模组")

    def _update_mod_xml(self, mod_dir: str, csv_path: str, language: str) -> None:
        """更新单个模组的 XML 文件"""
        translations = load_translations_from_csv(csv_path)
        content_filter = ContentFilter(CONFIG)
        lang_path = get_language_folder_path(language, mod_dir)
        for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
            dir_path = os.path.join(lang_path, dir_name)
            if not os.path.exists(dir_path):
                continue
            for xml_file in Path(dir_path).rglob("*.xml"):
                tree = self.processor.parse_xml(str(xml_file))
                if tree and self.processor.update_translations(tree, translations, generate_element_key):
                    self.processor.save_xml(tree, str(xml_file))