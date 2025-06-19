#!/usr/bin/env python3
"""
Day Translation 2 - 导入测试脚本

测试所有核心模块的导入是否正常
"""

import sys
from pathlib import Path

# 添加当前目录到sys.path以支持独立运行
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def test_imports():
    """测试核心模块导入"""
    results = []
    
    # 测试config模块
    try:
        from config import get_config
        results.append("✅ config模块导入成功")
    except Exception as e:
        results.append(f"❌ config模块导入失败: {e}")
    
    # 测试extractors模块
    try:
        from core.extractors import extract_keyed_translations
        results.append("✅ extractors模块导入成功")
    except Exception as e:
        results.append(f"❌ extractors模块导入失败: {e}")
    
    # 测试exporters模块
    try:
        from core.exporters import export_to_csv
        results.append("✅ exporters模块导入成功")
    except Exception as e:
        results.append(f"❌ exporters模块导入失败: {e}")
    
    # 测试services模块
    try:
        from services import BatchProcessor
        results.append("✅ services模块导入成功")
    except Exception as e:
        results.append(f"❌ services模块导入失败: {e}")
    
    # 测试interaction模块
    try:
        from interaction import UnifiedInteractionManager
        results.append("✅ interaction模块导入成功")
    except Exception as e:
        results.append(f"❌ interaction模块导入失败: {e}")
    
    # 测试utils模块
    try:
        from utils.xml_processor import AdvancedXMLProcessor
        results.append("✅ utils模块导入成功")
    except Exception as e:
        results.append(f"❌ utils模块导入失败: {e}")
    
    return results

if __name__ == "__main__":
    print("Day Translation 2 - 核心模块导入测试")
    print("=" * 50)
    
    results = test_imports()
    for result in results:
        print(result)
    
    success_count = len([r for r in results if r.startswith("✅")])
    total_count = len(results)
    
    print("=" * 50)
    print(f"测试完成: {success_count}/{total_count} 个模块导入成功")
    
    if success_count == total_count:
        print("🎉 所有核心模块导入正常！")
    else:
        print("⚠️  存在导入问题，需要进一步修复")
