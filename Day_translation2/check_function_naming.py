#!/usr/bin/env python3
"""
PEP 8 函数命名检查器
专门检查驼峰命名法违规
"""

import ast
import os
import re
from pathlib import Path


def is_camel_case(name):
    """检查是否是驼峰命名法（违反PEP 8）"""
    # 跳过特殊方法（__init__, __str__等）
    if name.startswith("__") and name.endswith("__"):
        return False

    # 跳过私有方法（_method）
    if name.startswith("_"):
        return False

    # 真正的驼峰命名：包含大写字母，且不是全大写
    if re.match(r"^[a-z]+[A-Z][a-zA-Z]*$", name):
        return True

    return False


def check_file(file_path):
    """检查单个文件中的函数命名"""
    violations = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if is_camel_case(node.name):
                    violations.append(
                        {
                            "file": file_path,
                            "function": node.name,
                            "line": node.lineno,
                            "type": "function",
                        }
                    )
            elif isinstance(node, ast.AsyncFunctionDef):
                if is_camel_case(node.name):
                    violations.append(
                        {
                            "file": file_path,
                            "function": node.name,
                            "line": node.lineno,
                            "type": "async_function",
                        }
                    )

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return violations


def main():
    """主函数"""
    root_dir = Path(".")
    all_violations = []

    # 遍历所有Python文件
    for py_file in root_dir.rglob("*.py"):
        if py_file.is_file():
            violations = check_file(py_file)
            all_violations.extend(violations)

    # 输出结果
    if all_violations:
        print("🚨 发现PEP 8函数命名违规：")
        print("=" * 60)

        for violation in all_violations:
            print(f"文件: {violation['file']}")
            print(f"函数: {violation['function']} (行 {violation['line']})")
            print(f"类型: {violation['type']}")
            print(f"建议: {violation['function']} -> {camel_to_snake(violation['function'])}")
            print("-" * 40)
    else:
        print("✅ 未发现PEP 8函数命名违规")
        print("所有函数都正确使用了snake_case命名规范")


def camel_to_snake(name):
    """将驼峰命名转换为蛇形命名"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


if __name__ == "__main__":
    main()
