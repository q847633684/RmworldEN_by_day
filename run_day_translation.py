import sys
import os
import argparse
from pathlib import Path
from day_translation.core.main import main

def parse_args():
    """
    解析命令行参数

    Returns:
        argparse.Namespace: 包含 mod_dir 和 mode 的参数对象
    """
    parser = argparse.ArgumentParser(description="Day Translation 模组翻译工具")
    parser.add_argument('--mod-dir', help="模组目录路径")
    parser.add_argument('--mode', choices=['1', '2', '3', '4', '5', '6'], help="运行模式 (1-6)")
    return parser.parse_args()

if __name__ == "__main__":
    """程序入口，运行主工作流"""
    try:
        args = parse_args()
        # 动态添加项目根目录到 sys.path
        project_root = str(Path(__file__).parent.resolve())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        main()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖模块都已正确安装")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        input("按回车键退出...")
