import os
import logging
import csv
from pathlib import Path
from typing import Dict, List
from ..utils.config import TranslationConfig
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
    csv_path = str(Path(csv_path).resolve())  # 解析绝对路径
    mod_dir = str(Path(mod_dir).resolve())
    if not os.path.exists(csv_path):
        logging.error(f"CSV 文件不存在: {csv_path}")
        return
    translations: Dict[str, str] = {}
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["key"]
                value = row.get("translated") or row["text"]
                translations[key] = value
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {csv_path}, 错误: {e}")
        return
    except OSError as e:
        logging.error(f"无法读取 CSV: {csv_path}, 错误: {e}")
        return
    def_injected_path = Path(mod_dir) / "Languages" / language / CONFIG.def_injected_dir
    if not def_injected_path.exists():
        def_injured_path = Path(mod_dir) / "Languages" / language / "DefInjured"
        if def_injured_path.exists():
            def_injected_path = def_injured_path
        else:
            logging.error(f"未找到 DefInjected 或 DefInjured 目录: {def_injected_path}")
            return
    keyed_path = Path(mod_dir) / "Languages" / language / CONFIG.keyed_dir
    try:
        if merge:
            update_lxml(csv_path, mod_dir)
        else:
            for xml_file in def_injected_path.rglob("*.xml"):
                os.remove(xml_file)
                logging.info(f"删除文件: {xml_file}")
            for xml_file in keyed_path.rglob("*.xml"):
                os.remove(xml_file)
                logging.info(f"删除文件: {xml_file}")
            update_etree(csv_path, mod_dir)
        logging.info("导入翻译完成")
    except OSError as e:
        logging.error(f"导入翻译失败: {e}")