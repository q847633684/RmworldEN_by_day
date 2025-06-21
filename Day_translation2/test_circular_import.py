#!/usr/bin/env python3
"""
测试循环导入问题
"""

import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 测试基本导入
try:
    print("测试导入 services.config_service...")
    from services.config_service import config_service

    print("✅ 成功导入 config_service")
except Exception as e:
    print(f"❌ 导入失败: {e}")

try:
    print("测试导入 core.extractors 模块...")
    import core.extractors

    print("✅ 成功导入 core.extractors 模块")
except Exception as e:
    print(f"❌ 导入失败: {e}")

try:
    print("测试导入具体函数 extract_all_translations...")
    from core.extractors import extract_all_translations

    print("✅ 成功导入 extract_all_translations")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")

try:
    print("测试导入 interaction.interaction_manager...")
    from interaction.interaction_manager import UnifiedInteractionManager

    print("✅ 成功导入 UnifiedInteractionManager")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")

print("测试完成")
