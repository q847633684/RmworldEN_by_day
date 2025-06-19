"""
Day Translation 2 - 统一导入模块

解决相对导入和绝对导入的兼容性问题
"""

import os
import sys
from pathlib import Path

# 确保项目根目录在Python路径中
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# 导入检查函数
def ensure_imports():
    """确保所有必要的导入路径都可用"""
    try:
        # 测试关键模块导入
        import config.unified_config
        import models.exceptions
        import models.translation_data
        import utils.enterprise_xml_processor

        return True
    except ImportError as e:
        print(f"导入检查失败: {e}")
        return False


if __name__ == "__main__":
    if ensure_imports():
        print("所有导入检查通过")
    else:
        print("导入检查失败")
