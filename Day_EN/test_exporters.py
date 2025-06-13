"""
test_exporters.py
自动化测试 Day_EN.exporters 的部分核心功能。
"""
import os
import shutil
from Day_EN.exporters import export_keyed

def test_export_keyed():
    # 构造一个简单的英文 Keyed 目录
    mod_root = "tmp_mod"
    export_dir = "tmp_export"
    en_keyed = os.path.join(mod_root, "Languages", "English", "Keyed")
    os.makedirs(en_keyed, exist_ok=True)
    with open(os.path.join(en_keyed, "test.xml"), "w", encoding="utf-8") as f:
        f.write("<LanguageData><TestKey>Hello</TestKey></LanguageData>")
    # 调用导出
    export_keyed(mod_root, export_dir)
    zh_keyed = os.path.join(export_dir, "Languages", "ChineseSimplified", "Keyed")
    found = False
    for root, _, files in os.walk(zh_keyed):
        for file in files:
            if file.endswith(".xml"):
                found = True
    assert found, "未生成 Keyed XML"
    # 清理
    shutil.rmtree(mod_root)
    shutil.rmtree(export_dir)
    print("test_export_keyed passed")

if __name__ == "__main__":
    test_export_keyed()
