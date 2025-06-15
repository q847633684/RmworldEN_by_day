"""
day_translation 主程序运行入口
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from day_translation.core.main import main
    
    if __name__ == "__main__":
        print("启动 RimWorld 模组翻译工具...")
        main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖模块都已正确安装")
    input("按回车键退出...")
except KeyboardInterrupt:
    print("\n程序被用户中断")
except Exception as e:
    print(f"程序运行错误: {e}")
    input("按回车键退出...")
