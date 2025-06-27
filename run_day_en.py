#!/usr/bin/env python3
"""
Day_EN 翻译提取工具启动脚本
"""
import sys
import os
from pathlib import Path

def main():
    # 动态添加项目根目录到 sys.path
    project_root = str(Path(__file__).parent.resolve())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 导入并运行 Day_EN 的主函数
    try:
        from Day_EN.main import main as day_en_main
        day_en_main()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保 Day_EN 目录存在并包含必要的文件")
        sys.exit(1)
    except Exception as e:
        print(f"运行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
