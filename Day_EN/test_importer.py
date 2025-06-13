"""
test_importer.py
自动化测试 Day_EN.importer 的核心功能。
"""
import os
import shutil
from Day_EN.importer import import_translations

def test_import_translations():
    # 构造一个简单的 CSV 和目标目录
    csv_content = "key,text,tag\nTestKey,测试文本,TestTag\n"
    csv_path = "tmp_test.csv"
    mod_root = "tmp_mod"
    os.makedirs(mod_root, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    # 调用导入
    import_translations(csv_path, mod_root)
    # 检查 XML 是否生成
    zh_keyed = os.path.join(mod_root, "Languages", "ChineseSimplified", "Keyed")
    found = False
    for root, _, files in os.walk(zh_keyed):
        for file in files:
            if file.endswith(".xml"):
                found = True
    assert found, "未生成 Keyed XML"
    # 清理
    shutil.rmtree(mod_root)
    os.remove(csv_path)
    print("test_import_translations passed")

if __name__ == "__main__":
    test_import_translations()
