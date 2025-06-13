import os
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from .utils import save_xml_to_file, get_language_folder_path

def import_translations(
    csv_path: str,
    mod_root_dir: str,
    language: str = "ChineseSimplified"
) -> None:
    """
    从 CSV 文件批量导入翻译并写入 Keyed/DefInjected 目录。

    Args:
        csv_path (str): 翻译 CSV 路径（需包含 key, text, tag 或 translated 列）。
        mod_root_dir (str): 模组根目录。
        language (str): 目标语言（默认 ChineseSimplified）。
    """
    def_injected_path = os.path.join(mod_root_dir, "Languages", language, "DefInjected")
    keyed_path = os.path.join(mod_root_dir, "Languages", language, "Keyed")
    translations = defaultdict(list)
    keyed_translations = {}

    # 读取 CSV
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"]
            translated = row.get("translated") or row["text"]  # 优先用 translated 列
            tag = row.get("tag", "")
            # DefInjected 类型
            if "/" in key and "." in key:
                def_type, rest = key.split("/", 1)
                def_name, field_path = rest.split(".", 1)
                translations[(def_type, def_name)].append((field_path, translated, tag))
            # Keyed 类型
            elif "/" not in key and "." not in key:
                keyed_translations[key] = translated

    # 导出 DefInjected
    for (def_type, def_name), fields in translations.items():
        out_dir = os.path.join(def_injected_path, def_type)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{def_name}.xml")
        root = ET.Element("LanguageData")
        for field_path, translated, tag in fields:
            elem = ET.SubElement(root, f"{def_name}.{field_path}")
            elem.text = translated
        save_xml_to_file(root, out_path)
        print(f"写入 {out_path}")

    # 导出 Keyed
    if keyed_translations:
        os.makedirs(keyed_path, exist_ok=True)
        out_path = os.path.join(keyed_path, "AutoImported.xml")
        root = ET.Element("LanguageData")
        for k, v in keyed_translations.items():
            elem = ET.SubElement(root, k)
            elem.text = v
        save_xml_to_file(root, out_path)
        print(f"写入 {out_path}")
