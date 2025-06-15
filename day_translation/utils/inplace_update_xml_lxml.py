import os
import logging
from pathlib import Path
from typing import Dict
from lxml import etree
from ..utils.config import TranslationConfig

CONFIG = TranslationConfig()

def inplace_update_all_xml(csv_path: str, mod_dir: str) -> None:
    """
    使用 lxml 更新所有 XML 文件中的翻译。

    Args:
        csv_path: 翻译 CSV 文件路径
        mod_dir: 模组根目录
    """
    logging.info(f"使用 lxml 更新 XML: csv_path={csv_path}, mod_dir={mod_dir}")
    translations: Dict[str, str] = {}
    try:
        import csv
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                translations[row["key"]] = row.get("translated", row["text"])
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {csv_path}, 错误: {e}")
        return
    except OSError as e:
        logging.error(f"无法读取 CSV: {csv_path}, 错误: {e}")
        return
    def_injected_path = os.path.join(mod_dir, "Languages", CONFIG.default_language, CONFIG.def_injected_dir)
    if not os.path.exists(def_injected_path):
        def_injured_path = os.path.join(mod_dir, "Languages", CONFIG.default_language, "DefInjured")
        if os.path.exists(def_injured_path):
            def_injected_path = def_injured_path
        else:
            logging.error(f"未找到 DefInjected 或 DefInjured 目录: {def_injected_path}")
            return
    keyed_path = os.path.join(mod_dir, "Languages", CONFIG.default_language, CONFIG.keyed_dir)
    try:
        parser = etree.XMLParser(remove_comments=False)
        for xml_file in list(Path(def_injected_path).rglob("*.xml")) + list(Path(keyed_path).rglob("*.xml")):
            try:
                tree = etree.parse(xml_file, parser)
                root = tree.getroot()
                modified = False
                for elem in root.xpath(".//*[text()]"):
                    key = elem.get("key")
                    if not key:
                        path = "/".join(elem.xpath("ancestor-or-self::*/@defName | ancestor-or-self::*/name()"))
                        key = f"{path}.{elem.tag}"
                    if key in translations:
                        elem.text = translations[key]
                        modified = True
                if modified:
                    tree.write(xml_file, encoding="utf-8", xml_declaration=True)
                    logging.info(f"更新文件: {xml_file}")
            except etree.ParseError as e:
                logging.error(f"XML 解析失败: {xml_file}: {e}")
            except OSError as e:
                logging.error(f"无法处理 {xml_file}: {e}")
    except Exception as e:
        logging.error(f"更新 XML 失败: {e}")