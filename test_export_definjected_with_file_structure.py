import os
from day_translation.extract.exporters import export_definjected_with_file_structure

def test_export_definjected_with_file_structure():
    # 构造模拟数据: (full_path, text, tag, rel_path)
    selected_translations = [
        ("ThingDef/Apple.label", "苹果", "label", "ThingDef/Apple.xml"),
        ("ThingDef/Apple.description", "一种水果", "description", "ThingDef/Apple.xml"),
        ("PawnKindDef/Human.label", "人类", "label", "PawnKindDef/Human.xml"),
        ("PawnKindDef/Human.description", "智慧生物", "description", "PawnKindDef/Human.xml"),
        ("ApparelLayerDef.AnalInsertableBondage.label", "肛塞束缚", "label", "ApparelLayerDef/AnalInsertableBondage.xml"),
        ("ApparelLayerDef.AnalInsertableBondage.description", "特殊道具", "description", "ApparelLayerDef/AnalInsertableBondage.xml"),
        ("ThingDef/非法/标签.label", "非法标签", "label", "ThingDef/非法/标签.xml"),
    ]
    mod_dir = os.getcwd()  # 当前目录即可
    export_dir = os.path.join(os.getcwd(), "test_output")
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    export_definjected_with_file_structure(mod_dir, export_dir, selected_translations)
    print("测试完成，请检查 test_output/DefInjected 目录下的 XML 文件。")

if __name__ == "__main__":
    test_export_definjected_with_file_structure() 