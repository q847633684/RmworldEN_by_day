from pathlib import Path
from typing import Dict
import logging
from ..utils.utils import XMLProcessor, get_language_folder_path, handle_exceptions
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

@handle_exceptions()
def import_translations(csv_path: str, mod_dir: str, language: str = CONFIG.default_language, merge: bool = True) -> None:
    """从 CSV 导入翻译到 XML 文件"""
    logging.info(f"从 {csv_path} 导入翻译到 {mod_dir}, 语言: {language}")
    processor = XMLProcessor()
    translations = load_translations_from_csv(csv_path)
    lang_path = get_language_folder_path(language, mod_dir)
    for dir_name in [CONFIG.def_injected_dir, CONFIG.keyed_dir]:
        dir_path = Path(lang_path) / dir_name
        if not dir_path.exists():
            continue
        for xml_file in dir_path.rglob("*.xml"):
            tree = processor.parse_xml(str(xml_file))
            if tree and processor.update_translations(tree, translations, generate_element_key):
                processor.save_xml(tree, str(xml_file))
                logging.info(f"更新文件: {xml_file}")
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

def generate_element_key(elem: Any, root: Any, parent_map: Dict = None) -> str:
    """生成元素键"""
    key = elem.get("key") or elem.tag
    if parent_map:
        path_parts = []
        current = elem
        while current is not None and current != root:
            if current.tag != "LanguageData":
                path_parts.append(current.tag)
            current = parent_map.get(current)
        path_parts.reverse()
        key = ".".join(path_parts) if path_parts else key
    return key