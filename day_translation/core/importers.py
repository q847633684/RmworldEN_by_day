from pathlib import Path
from typing import Dict
import logging
from ..utils.inplace_update_xml_lxml import update_all_xml as update_all_xml_lxml
from ..utils.inplace_update_xml_etree import update_all_xml as update_all_xml_etree
from ..utils.utils import get_language_folder_path, handle_exceptions
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

@handle_exceptions()
def import_translations(csv_path: str, mod_dir: str, language: str = CONFIG.default_language, merge: bool = True) -> None:
    """从 CSV 导入翻译到 XML 文件"""
    logging.info(f"从 {csv_path} 导入翻译到 {mod_dir}, 语言: {language}")
    translations = load_translations_from_csv(csv_path)
    try:
        update_all_xml_lxml(mod_dir, translations, language, merge)
    except ImportError:
        update_all_xml_etree(mod_dir, translations, language, merge)
    logging.info(f"导入翻译完成: {len(translations)} 条记录")

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
        logging.error(f"CSV 解析失败: {csv_path}: {e}")
    return translations