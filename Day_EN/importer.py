import os
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from .utils import save_xml_to_file, get_language_folder_path
import logging
from functools import lru_cache

@lru_cache(maxsize=128)
def parse_xml(path: str) -> ET.ElementTree:
    return ET.parse(path)

def import_translations(
    csv_path: str,
    mod_root_dir: str,
    language: str = "ChineseSimplified",
    merge: bool = False
) -> None:
    """
    从 CSV 文件批量导入翻译并写入 Keyed/DefInjected 目录。
    """
    def_injected_path = os.path.join(mod_root_dir, "Languages", language, "DefInjected")
    keyed_path = os.path.join(mod_root_dir, "Languages", language, "Keyed")
    translations = defaultdict(list)
    keyed_translations = {}
    if not os.path.exists(csv_path):
        logging.error(f"CSV 文件不存在: {csv_path}")
        return
    if not merge:
        if os.path.isdir(def_injected_path):
            for root_dir, _, files in os.walk(def_injected_path):
                for file in files:
                    if file.endswith(".xml"):
                        try:
                            os.remove(os.path.join(root_dir, file))
                            logging.info(f"删除 DefInjected 文件: {file}")
                        except OSError as e:
                            logging.error(f"无法删除 {file}: {e}")
        autoimported_xml = os.path.join(keyed_path, "AutoImported.xml")
        if os.path.isfile(autoimported_xml):
            try:
                os.remove(autoimported_xml)
                logging.info(f"删除 Keyed 文件: {autoimported_xml}")
            except OSError as e:
                logging.error(f"无法删除 {autoimported_xml}: {e}")
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required_fields = ["key", "text"]
            if not all(field in reader.fieldnames for field in required_fields):
                logging.error(f"CSV 缺少必需字段: {required_fields}")
                return
            for row in reader:
                key = row["key"]
                translated = row.get("translated") or row["text"]
                if not translated.strip():
                    logging.warning(f"跳过空翻译: key={key}")
                    continue
                tag = row.get("tag", "")
                if "/" in key and "." in key:
                    def_type, rest = key.split("/", 1)
                    def_name, field_path = rest.split(".", 1)
                    translations[(def_type, def_name)].append((field_path, translated, tag))
                elif "/" not in key and "." not in key:
                    keyed_translations[key] = translated
    except FileNotFoundError as e:
        logging.error(f"CSV 文件未找到: {csv_path}，错误: {e}")
        return
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {csv_path}，错误: {e}")
        return
    for (def_type, def_name), fields in translations.items():
        out_dir = os.path.join(def_injected_path, def_type)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{def_name}.xml")
        merged_dict = {}
        if merge and os.path.exists(out_path):
            try:
                tree = parse_xml(out_path)
                root0 = tree.getroot()
                for elem in root0:
                    merged_dict[elem.tag] = elem.text
            except ET.ParseError as e:
                logging.error(f"解析现有 XML 失败: {out_path}，错误: {e}")
        for field_path, translated, tag in fields:
            key_name = f"{def_name}.{field_path}"
            if not merge:
                merged_dict[key_name] = translated
            elif key_name in merged_dict:
                merged_dict[key_name] = translated
        root = ET.Element("LanguageData")
        for tag, text in merged_dict.items():
            elem = ET.SubElement(root, tag)
            elem.text = text
        save_xml_to_file(root, out_path)
        logging.info(f"写入 DefInjected: {out_path}")
        print(f"写入 {out_path}")
    if keyed_translations:
        os.makedirs(keyed_path, exist_ok=True)
        out_path = os.path.join(keyed_path, "AutoImported.xml")
        merged_dict = {}
        if merge and os.path.exists(out_path):
            try:
                tree = parse_xml(out_path)
                root0 = tree.getroot()
                for elem in root0:
                    merged_dict[elem.tag] = elem.text
            except ET.ParseError as e:
                logging.error(f"解析现有 Keyed XML 失败: {out_path}，错误: {e}")
        for k, v in keyed_translations.items():
            if not merge:
                merged_dict[k] = v
            elif k in merged_dict:
                merged_dict[k] = v
        root = ET.Element("LanguageData")
        for k, v in sorted(merged_dict.items()):
            elem = ET.SubElement(root, k)
            elem.text = v
        save_xml_to_file(root, out_path)
        logging.info(f"写入 Keyed: {out_path}")
        print(f"写入 {out_path}")