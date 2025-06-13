import xml.etree.ElementTree as ET
import csv

def inplace_update_xml_etree(xml_path, csv_path):
    """
    只替换已有key内容，不新增，顺序保留，注释会丢失。
    """
    # 读取CSV为字典
    csv_dict = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"].split("/")[-1]  # 只取 xxx.label 这种
            value = row.get("translated") or row["text"]
            csv_dict[key] = value

    tree = ET.parse(xml_path)
    root = tree.getroot()
    for elem in root:
        if elem.tag in csv_dict:
            elem.text = csv_dict[elem.tag]
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    # 示例用法
    inplace_update_xml_etree(
        "mod/Languages/ChineseSimplified/DefInjected/ApparelLayerDefs/ApparelLayerDefs.xml",
        "mod/extracted_translations_zh.csv"
    )
