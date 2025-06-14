import os
from Day_EN.exporters import export_keyed_to_csv

def test_export_keyed_to_csv():
    # 假设你的导出目录结构如下
    export_dir = os.path.abspath("./test_export")
    keyed_dir = os.path.join(export_dir, "Languages", "English", "Keyed")
    csv_path = os.path.join(export_dir, "extracted_translations.csv")
    # 确保测试目录存在
    os.makedirs(keyed_dir, exist_ok=True)
    # 创建一个简单的Keyed XML文件用于测试
    xml_content = '''<LanguageData>\n    <TestKey>Hello World</TestKey>\n    <AnotherKey>你好，世界</AnotherKey>\n</LanguageData>'''
    xml_file = os.path.join(keyed_dir, "test.xml")
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml_content)
    # 调用导出函数
    export_keyed_to_csv(keyed_dir, csv_path)
    # 检查csv内容
    with open(csv_path, "r", encoding="utf-8") as f:
        print(f.read())

if __name__ == "__main__":
    test_export_keyed_to_csv()
