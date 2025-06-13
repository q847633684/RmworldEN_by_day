from lxml import etree
import csv

def inplace_update_xml_lxml(xml_path, csv_path):
    """
    只替换已有key内容，不新增，顺序、注释、缩进等格式全部保留（需安装lxml）。
    """
    csv_dict = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"].split("/")[-1]
            value = row.get("translated") or row["text"]
            csv_dict[key] = value

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(xml_path, parser)
    root = tree.getroot()
    for elem in root:
        if isinstance(elem.tag, str) and elem.tag in csv_dict:
            elem.text = csv_dict[elem.tag]
    tree.write(xml_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    # 示例用法
    inplace_update_xml_lxml(
        "mod/Languages/ChineseSimplified/DefInjected/ApparelLayerDefs/ApparelLayerDefs.xml",
        "mod/extracted_translations_zh.csv"
    )
