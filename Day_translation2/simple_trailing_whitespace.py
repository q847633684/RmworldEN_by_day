#!/usr/bin/env python3
"""
简单的尾随空格移除脚本
"""
import os
from pathlib import Path


def main():
    """移除Python文件的尾随空格"""
    project_root = Path(__file__).parent
    py_files = list(project_root.glob("**/*.py"))

    cleaned_count = 0

    for py_file in py_files:
        # 跳过某些目录
        if any(
            part in py_file.parts
            for part in ["__pycache__", ".pytest_cache", "venv", "env"]
        ):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 移除每行的尾随空格
            cleaned_lines = [line.rstrip() + "\n" for line in lines]

            # 如果有变化，写回文件
            if cleaned_lines != lines:
                with open(py_file, "w", encoding="utf-8") as f:
                    f.writelines(cleaned_lines)
                cleaned_count += 1
                print(f"已清理: {py_file.name}")

        except Exception as e:
            print(f"处理文件 {py_file} 时出错: {e}")

    print(f"共处理了 {cleaned_count} 个文件")


if __name__ == "__main__":
    main()
