#!/usr/bin/env python3
"""简单测试exporters导入"""

import sys
from pathlib import Path

# 添加当前目录到sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from core.exporters import export_to_csv
    print("✅ exporters模块导入成功")
except Exception as e:
    print(f"❌ exporters模块导入失败: {e}")
