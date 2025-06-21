#!/usr/bin/env python3
"""
修复不必要的f-string使用
自动检测并修复代码中不必要的f-string使用
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple


def detect_unnecessary_f_strings(content: str) -> List[Tuple[int, str, str]]:
    """
    检测不必要的f-string使用

    Args:
        content: 文件内容

    Returns:
        List of (line_number, old_line, suggested_fix)
    """
    lines = content.split("\n")
    issues = []

    for i, line in enumerate(lines, 1):
        # 检测不包含任何变量替换的f-string
        fstring_pattern = r'f["\']([^"\']*?)["\']'
        matches = re.finditer(fstring_pattern, line)

        for match in matches:
            fstring_content = match.group(1)
            # 检查是否包含变量替换 (包括 {}, {variable}, {expression})
            if not re.search(r"\{.*?\}", fstring_content):
                old_line = line.strip()
                # 建议修复：移除f前缀
                new_line = line.replace(
                    match.group(0),
                    (
                        f'"{fstring_content}"'
                        if match.group(0).startswith('"')
                        else f"'{fstring_content}'"
                    ),
                )
                issues.append((i, old_line, new_line.strip()))

    return issues


def fix_unnecessary_f_strings_in_file(file_path: str) -> Dict[str, any]:
    """
    修复单个文件中的不必要f-string使用

    Args:
        file_path: 文件路径

    Returns:
        修复结果字典
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        issues = detect_unnecessary_f_strings(original_content)

        if not issues:
            return {"file": file_path, "status": "no_issues", "issues_found": 0, "issues_fixed": 0}

        # 应用修复
        lines = original_content.split("\n")
        fixed_lines = lines.copy()

        # 从后向前修复，避免行号偏移
        for line_num, old_line, new_line in reversed(issues):
            if lines[line_num - 1].strip() == old_line:
                # 保持原有缩进
                indent = len(lines[line_num - 1]) - len(lines[line_num - 1].lstrip())
                fixed_lines[line_num - 1] = " " * indent + new_line

        fixed_content = "\n".join(fixed_lines)

        # 写入修复后的内容
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        return {
            "file": file_path,
            "status": "fixed",
            "issues_found": len(issues),
            "issues_fixed": len(issues),
            "issues": issues,
        }

    except Exception as e:
        return {
            "file": file_path,
            "status": "error",
            "error": str(e),
            "issues_found": 0,
            "issues_fixed": 0,
        }


def fix_unnecessary_f_strings_in_directory(
    directory: str, extensions: List[str] = None
) -> Dict[str, any]:
    """
    修复目录中所有Python文件的不必要f-string使用

    Args:
        directory: 目录路径
        extensions: 文件扩展名列表，默认为['.py']

    Returns:
        修复结果汇总
    """
    if extensions is None:
        extensions = [".py"]

    directory_path = Path(directory)
    if not directory_path.exists():
        return {"error": f"Directory {directory} does not exist"}

    results = []
    total_issues_found = 0
    total_issues_fixed = 0

    # 递归查找所有Python文件
    for ext in extensions:
        for file_path in directory_path.rglob(f"*{ext}"):
            if file_path.is_file():
                result = fix_unnecessary_f_strings_in_file(str(file_path))
                results.append(result)
                total_issues_found += result["issues_found"]
                total_issues_fixed += result["issues_fixed"]

    return {
        "directory": directory,
        "files_processed": len(results),
        "total_issues_found": total_issues_found,
        "total_issues_fixed": total_issues_fixed,
        "results": results,
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="修复不必要的f-string使用")
    parser.add_argument("path", help="要检查的文件或目录路径")
    parser.add_argument("--dry-run", action="store_true", help="只检查不修复")
    parser.add_argument("--extensions", nargs="+", default=[".py"], help="文件扩展名")

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        if args.dry_run:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            issues = detect_unnecessary_f_strings(content)
            print(f"文件 {path} 中发现 {len(issues)} 个不必要的f-string使用:")
            for line_num, old_line, new_line in issues:
                print(f"  行 {line_num}: {old_line}")
                print(f"    建议: {new_line}")
        else:
            result = fix_unnecessary_f_strings_in_file(str(path))
            print(f"文件 {path}: {result['status']}")
            if result["issues_fixed"] > 0:
                print(f"  修复了 {result['issues_fixed']} 个问题")

    elif path.is_dir():
        if args.dry_run:
            print("检查模式暂不支持目录")
        else:
            result = fix_unnecessary_f_strings_in_directory(str(path), args.extensions)
            print(f"目录 {path}:")
            print(f"  处理文件: {result['files_processed']}")
            print(f"  发现问题: {result['total_issues_found']}")
            print(f"  修复问题: {result['total_issues_fixed']}")

            # 显示修复详情
            for file_result in result["results"]:
                if file_result["status"] == "fixed":
                    print(f"  {file_result['file']}: 修复了 {file_result['issues_fixed']} 个问题")
    else:
        print(f"错误: 路径 {path} 不存在")


if __name__ == "__main__":
    main()
