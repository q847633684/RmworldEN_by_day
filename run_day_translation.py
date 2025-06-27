import sys
import argparse
from pathlib import Path
from typing import Optional
from day_translation.core.main import main

def parse_args() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        argparse.Namespace: 包含 mod_dir 和 mode 的参数对象
    """
    parser = argparse.ArgumentParser(description="Day Translation 模组翻译工具")
    parser.add_argument('--mod-dir', help="模组目录路径")
    parser.add_argument('--mode', choices=['1', '2', '3', '4', '5', '6', '7'], help="运行模式 (1-7)")
    return parser.parse_args()

def setup_environment() -> None:
    """设置运行环境，将项目根目录添加到 sys.path"""
    project_root = str(Path(__file__).parent.resolve())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

if __name__ == "__main__":
    """程序入口，运行主工作流"""
    try:
        args = parse_args()
        setup_environment()
        
        # 调用主函数，传入解析的参数
        # 注意：当前 main() 函数不接受参数，这是一个设计问题
        # 建议未来重构 main() 函数以接受命令行参数
        main()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖模块都已正确安装")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        input("按回车键退出...")
