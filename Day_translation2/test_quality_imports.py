#!/usr/bin/env python3
"""
测试质量检查脚本的导入方式
"""

import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_import(module_name, import_items):
    """测试单个模块的导入"""
    try:
        module = __import__(module_name, fromlist=import_items.split(", "))
        for item in import_items.split(", "):
            item = item.strip()
            if hasattr(module, item):
                print(f"✅ {module_name}.{item}")
            else:
                print(f"❌ {module_name}.{item} - 属性不存在")
        return True
    except Exception as e:
        print(f"❌ {module_name}: {e}")
        return False


# 测试最有问题的模块
test_cases = [
    ("core.extractors", "extract_all_translations"),
    ("interaction.interaction_manager", "UnifiedInteractionManager"),
]

print("测试质量检查脚本的导入方式：")
for module_name, import_items in test_cases:
    test_import(module_name, import_items)
