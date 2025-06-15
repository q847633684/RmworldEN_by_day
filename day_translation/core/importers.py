import logging
import os
import csv
from pathlib import Path
from typing import Dict
from ..utils.config import TranslationConfig
from ..utils.utils import get_language_folder_path
from ..utils.inplace_update_xml_lxml import inplace_update_all_xml as update_lxml
from ..utils.inplace_update_xml_etree import inplace_update_all_xml as update_etree

CONFIG = TranslationConfig()

def import_translations(
    csv_path: str,
    mod_dir: str,
    language: str = CONFIG.default_language,
    merge: bool = True
) -> None:
    """
    从翻译后的 CSV 导入到 DefInjected 和 Keyed。

    Args:
        csv_path: 翻译后的 CSV 文件路径
        mod_dir: 模组根目录
        language: 目标语言
        merge: 是否合并已有翻译
    """
    logging.info(f"导入翻译: csv_path={csv_path}, mod_dir={mod_dir}, language={language}, merge={merge}")
    mod_dir = str(Path(mod_dir).resolve())
    csv_path = str(Path(csv_path).resolve())
    if not os.path.exists(csv_path):
        logging.error(f"CSV 文件不存在: {csv_path}")
        raise FileNotFoundError(f"CSV 文件 {csv_path} 不存在")

    translations: Dict[str, str] = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("key", "").strip()
                value = row.get("translated", row.get("text", "")).strip()
                if key and value:
                    translations[key] = value
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {csv_path}: {e}")
        raise
    except OSError as e:
        logging.error(f"无法读取 CSV: {csv_path}: {e}")
        raise

    lang_path = get_language_folder_path(language, mod_dir)
    def_injected_path = os.path.join(lang_path, CONFIG.def_injected_dir)
    def_injured_path = os.path.join(lang_path, "DefInjured")
    keyed_path = os.path.join(lang_path, CONFIG.keyed_dir)

    if not os.path.exists(def_injected_path) and os.path.exists(def_injured_path):
        def_injected_path = def_injured_path

    if not merge:
        for path in [def_injected_path, keyed_path]:
            if os.path.exists(path):
                for xml_file in Path(path).rglob("*.xml"):
                    try:
                        os.remove(xml_file)
                        logging.info(f"删除文件: {xml_file}")
                    except OSError as e:
                        logging.error(f"无法删除 {xml_file}: {e}")

    if os.path.exists(def_injected_path):
        try:
            update_lxml(csv_path, mod_dir)
            logging.info(f"更新 DefInjected: {def_injected_path}")
        except Exception as e:
            logging.warning(f"LXML 更新 DefInjected 失败: {e}，尝试使用 ElementTree")
            update_etree(csv_path, mod_dir)
            logging.info(f"使用 ElementTree 更新 DefInjected: {def_injected_path}")
    else:
        logging.warning(f"未找到 DefInjected 或 DefInjured 目录: {def_injected_path}")

    if os.path.exists(keyed_path):
        try:
            update_lxml(csv_path, mod_dir)
            logging.info(f"更新 Keyed: {keyed_path}")
        except Exception as e:
            logging.warning(f"LXML 更新 Keyed 失败: {e}，尝试使用 ElementTree")
            update_etree(csv_path, mod_dir)
            logging.info(f"使用 ElementTree 更新 Keyed: {keyed_path}")
    else:
        logging.warning(f"未找到 Keyed 目录: {keyed_path}")

    logging.info("导入翻译完成")