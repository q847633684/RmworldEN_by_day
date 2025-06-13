"""
test_extractors.py
自动化测试 Day_EN.extractors 的部分核心功能。
"""
import os
from Day_EN.extractors import preview_translatable_fields

def test_preview_translatable_fields():
    # 构造一个简单的 Defs 目录和 xml
    mod_root = "tmp_mod"
    defs_dir = os.path.join(mod_root, "Defs")
    os.makedirs(defs_dir, exist_ok=True)
    xml_path = os.path.join(defs_dir, "a.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("""
        <Defs>
            <ThingDef>
                <defName>TestThing</defName>
                <label>测试物品</label>
            </ThingDef>
        </Defs>
        """)
    results = preview_translatable_fields(mod_root, preview=False)
    assert any("TestThing" in r[0] for r in results), "未提取到可翻译字段"
    # 清理
    os.remove(xml_path)
    os.rmdir(defs_dir)
    os.rmdir(mod_root)
    print("test_preview_translatable_fields passed")

if __name__ == "__main__":
    test_preview_translatable_fields()
