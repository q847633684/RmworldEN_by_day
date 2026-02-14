#!/usr/bin/env python3
"""
测试 DefsScanner 对 Common/Defs 结构的支持

这个脚本验证修改后的 DefsScanner 是否能正确处理具有 Common/Defs 结构的 mod
"""

from pathlib import Path
from extract.core.extractors import DefsScanner
from user_config import UserConfigManager

def test_defs_scanner():
    """测试 DefsScanner 的 Common/Defs 支持"""
    
    # 初始化
    config = UserConfigManager()
    scanner = DefsScanner(config)
    
    # 测试对象：nudity-matters-more-opinions mod
    mod_path = r"c:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\nudity-matters-more-opinions"
    
    print("=" * 70)
    print("测试 DefsScanner Common/Defs 支持")
    print("=" * 70)
    print(f"\n测试 MOD 路径: {mod_path}")
    
    # 验证目录存在
    mod_root = Path(mod_path)
    if not mod_root.exists():
        print(f"❌ MOD 目录不存在: {mod_path}")
        return False
    
    print(f"✅ MOD 目录存在")
    
    # 检查 Defs 目录位置
    defs_standard = mod_root / "Defs"
    defs_common = mod_root / "Common" / "Defs"
    
    print(f"\n目录检查:")
    print(f"  Defs 存在: {defs_standard.exists()}")
    print(f"  Common/Defs 存在: {defs_common.exists()}")
    
    if defs_common.exists():
        xml_count = len(list(defs_common.rglob("*.xml")))
        print(f"  ✅ 找到 {xml_count} 个 XML 文件在 Common/Defs")
    
    # 测试 _find_defs_directory 方法
    print(f"\n测试 _find_defs_directory 方法:")
    found_defs_dir = scanner._find_defs_directory(mod_path)
    
    if found_defs_dir is None:
        print("❌ 未找到 Defs 目录")
        return False
    
    print(f"✅ 找到 Defs 目录: {found_defs_dir}")
    
    # 测试完整的提取流程
    print(f"\n测试完整的 extract() 方法:")
    try:
        translations = scanner.extract(mod_path)
        print(f"✅ 成功提取 {len(translations)} 条翻译项")
        
        if len(translations) > 0:
            # 显示前5条
            print(f"\n前 5 条翻译示例:")
            for i, (key, text, tag, rel_path, en_text, def_type) in enumerate(translations[:5], 1):
                print(f"  {i}. [{def_type}] {key}")
                print(f"     文本: {text[:50]}..." if len(text) > 50 else f"     文本: {text}")
                print(f"     标签: {tag}, 文件: {rel_path}")
            
            # 统计数据
            def_types = {}
            tags = {}
            for key, text, tag, rel_path, en_text, def_type in translations:
                def_types[def_type] = def_types.get(def_type, 0) + 1
                tags[tag] = tags.get(tag, 0) + 1
            
            print(f"\n统计信息:")
            print(f"  定义类型分布: {dict(sorted(def_types.items()))}")
            print(f"  标签分布: {dict(sorted(tags.items()))}")
        
        return True
    
    except Exception as e:
        print(f"❌ 提取过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_defs_scanner()
    print("\n" + "=" * 70)
    if success:
        print("✅ 测试通过！DefsScanner 成功支持 Common/Defs 结构")
        sys.exit(0)
    else:
        print("❌ 测试失败")
        sys.exit(1)
