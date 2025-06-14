import xml.etree.ElementTree as ET
import csv


def inplace_update_xml_etree(xml_path, csv_dict):
    """
    只替换已有key内容，不新增，顺序保留，注释会丢失。
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    changed = False
    for elem in root:
        if elem.tag in csv_dict:
            elem.text = csv_dict[elem.tag]
            changed = True
    if changed:
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

def inplace_update_all_xml(csv_path, mod_root_dir):
    """
    批量遍历 DefInjected 和 Keyed 下所有 xml 文件，调用 inplace_update_xml_etree
    """
    import os
    from pathlib import Path
    # 读取CSV为字典
    csv_dict = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"].split("/")[-1]  # 只取 xxx.label 这种
            value = row.get("translated") or row["text"]
            csv_dict[key] = value
    # DefInjected
    def_injected_dir = os.path.join(mod_root_dir, "Languages", "ChineseSimplified", "DefInjected")
    for xml_file in Path(def_injected_dir).rglob("*.xml"):
        inplace_update_xml_etree(str(xml_file), csv_dict)
    # Keyed
    keyed_dir = os.path.join(mod_root_dir, "Languages", "ChineseSimplified", "Keyed")
    for xml_file in Path(keyed_dir).rglob("*.xml"):
        inplace_update_xml_etree(str(xml_file), csv_dict)

if __name__ == "__main__":
    # 示例用法：批量处理
    inplace_update_all_xml(
        "mod/extracted_translations_zh.csv",
        "mod"
    )
