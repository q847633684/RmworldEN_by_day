"""
Day Translation 框架启动脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入并运行主程序
if __name__ == "__main__":
    try:
        from day_translation.core.main import main
        main()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保 day_translation 包安装正确")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        sys.exit(1)
