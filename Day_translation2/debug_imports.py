#!/usr/bin/env python3
"""详细的导入调试脚本"""

import sys
from pathlib import Path

# 添加当前目录到sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

print("当前工作目录:", Path.cwd())
print("sys.path 前几个路径:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

# 测试services目录
services_dir = current_dir / "services"
print(f"\nservices目录存在: {services_dir.exists()}")
if services_dir.exists():
    print("services目录内容:")
    for f in services_dir.iterdir():
        print(f"  - {f.name}")

# 测试interaction目录
interaction_dir = current_dir / "interaction"
print(f"\ninteraction目录存在: {interaction_dir.exists()}")
if interaction_dir.exists():
    print("interaction目录内容:")
    for f in interaction_dir.iterdir():
        print(f"  - {f.name}")

# 尝试导入
print("\n=== 导入测试 ===")
try:
    import services
    print("✅ services包导入成功")
except Exception as e:
    print(f"❌ services包导入失败: {e}")

try:
    import interaction
    print("✅ interaction包导入成功")
except Exception as e:
    print(f"❌ interaction包导入失败: {e}")

try:
    from services.batch_processor import BatchProcessor
    print("✅ BatchProcessor导入成功")
except Exception as e:
    print(f"❌ BatchProcessor导入失败: {e}")

try:
    from interaction.interaction_manager import UnifiedInteractionManager
    print("✅ UnifiedInteractionManager导入成功")
except Exception as e:
    print(f"❌ UnifiedInteractionManager导入失败: {e}")
