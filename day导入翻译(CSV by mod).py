import os
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict

def import_translations(csv_path, mod_root_dir, language="ChineseSimplified"):
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
        tree = ET.ElementTree(root)
        tree.write(out_path, encoding="utf-8", xml_declaration=True)
        print(f"写入 {out_path}")

    # 导出 Keyed
    if keyed_translations:
        os.makedirs(keyed_path, exist_ok=True)
        out_path = os.path.join(keyed_path, "AutoImported.xml")
        root = ET.Element("LanguageData")
        for k, v in keyed_translations.items():
            elem = ET.SubElement(root, k)
            elem.text = v
        tree = ET.ElementTree(root)
        tree.write(out_path, encoding="utf-8", xml_declaration=True)
        print(f"写入 {out_path}")

# 用法
import_translations("extracted_translations.csv", "你的mod根目录路径")