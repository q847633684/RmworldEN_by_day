#!/usr/bin/env python3
"""
修复f-string工具造成的语法错误
修复 f"...{variable}" 被错误处理为 f"...{variable]}" 的问题
"""

import re
import os
from pathlib import Path


def fix_broken_f_strings(content: str) -> str:
    """
    修复被错误处理的f-string，特别是引号不匹配的问题

    Args:
        content: 文件内容

    Returns:
        修复后的内容
    """
    # 修复模式：f"...{variable}..."] -> f"...{variable}..."
    # 处理 {len(results['key'])} 这种错误的格式
    pattern = r'(\{[^}]*\["[^"]*\'[^\}]*\})'

    def fix_quotes(match):
        text = match.group(1)
        # 将 ["key'] 替换为 ['key']
        text = re.sub(r'\["([^"]*)\'\]', r"['\1']", text)
        return text

    content = re.sub(pattern, fix_quotes, content)

    # 修复另一种模式：未正确关闭的字符串
    # "text {variable" 应该是 f"text {variable}"
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # 检查是否有未终止的字符串字面量问题
        if "{" in line and "}" in line:
            # 如果行中有变量替换但没有f前缀，添加f前缀
            if re.search(r'"[^f"]*\{[^}]+\}[^"]*"', line) and not re.search(
                r'f"[^f"]*\{[^}]+\}[^"]*"', line
            ):
                line = re.sub(r'("[^f"]*\{[^}]+\}[^"]*")', r"f\1", line)

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_file(file_path: str) -> bool:
    """
    修复单个文件

    Args:
        file_path: 文件路径

    Returns:
        是否进行了修复
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        fixed_content = fix_broken_f_strings(original_content)

        if fixed_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            return True

        return False

    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="修复f-string工具造成的语法错误")
    parser.add_argument("directory", help="要修复的目录路径")

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"错误: 目录 {directory} 不存在")
        return

    fixed_files = []

    # 递归查找所有Python文件
    for py_file in directory.rglob("*.py"):
        if fix_file(str(py_file)):
            fixed_files.append(str(py_file))

    if fixed_files:
        print(f"修复了以下 {len(fixed_files)} 个文件:")
        for file_path in fixed_files:
            print(f"  - {file_path}")
    else:
        print("没有发现需要修复的文件")


if __name__ == "__main__":
    main()
