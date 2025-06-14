from lxml import etree
import csv


def inplace_update_xml_lxml(xml_path, csv_dict):
    """
    只替换已有key内容，不新增，顺序、注释、缩进等格式全部保留（需安装lxml）。
    """
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(xml_path, parser)
    root = tree.getroot()
    changed = False
    for elem in root:
        if isinstance(elem.tag, str) and elem.tag in csv_dict:
            elem.text = csv_dict[elem.tag]
            changed = True
    if changed:
        tree.write(xml_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

def inplace_update_all_xml(csv_path, mod_root_dir):
    """
    批量遍历 DefInjected 和 Keyed 下所有 xml 文件，调用 inplace_update_xml_lxml
    """
    import os
    from pathlib import Path
    # 读取CSV为字典
    csv_dict = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"].split("/")[-1]
            value = row.get("translated") or row["text"]
            csv_dict[key] = value
    # DefInjected
    def_injected_dir = os.path.join(mod_root_dir, "Languages", "ChineseSimplified", "DefInjected")
    for xml_file in Path(def_injected_dir).rglob("*.xml"):
        inplace_update_xml_lxml(str(xml_file), csv_dict)
    # Keyed
    keyed_dir = os.path.join(mod_root_dir, "Languages", "ChineseSimplified", "Keyed")
    for xml_file in Path(keyed_dir).rglob("*.xml"):
        inplace_update_xml_lxml(str(xml_file), csv_dict)

if __name__ == "__main__":
    # 示例用法：批量处理
    inplace_update_all_xml(
        "mod/extracted_translations_zh.csv",
        "mod"
    )
