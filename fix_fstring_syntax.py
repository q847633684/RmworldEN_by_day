#!/usr/bin/env python3
"""
修复f-string语法错误的脚本

专门修复常见的f-string语法问题，如：
- rf"\{[^}]+\}" 应该是 r"\{[^}]+\}"
- f"{变量{子表达式}}" 嵌套问题
- f"{变量}' 引号不匹配问题
"""

import re
import sys
from pathlib import Path


def fix_fstring_errors(content: str) -> str:
    """修复内容中的f-string语法错误"""

    # 1. 修复 rf"\{[^}]+\}" 问题 - 移除f前缀，因为没有变量插值
    content = re.sub(r'rf"([^"]*\\{[^"]*)"', r'r"\1"', content)

    # 2. 修复 f"{变量}' 引号不匹配
    content = re.sub(r'f"([^"]*)"\'([^\']*)', r'f"\1" + \'\2', content)

    # 3. 修复 f"文本{", '.join(列表)}" 这种嵌套引号问题
    content = re.sub(
        r'f"([^"]*){", \'\.join\(([^)]+)\)}"', r'"\1" + ", ".join(\2)', content
    )

    # 4. 修复 "术语 f"{变量}' 未使用标准翻译" 这种混合问题
    content = re.sub(
        r'"([^"]*) f"{([^}]+)}\' ([^"]*)"', r'f"\1 \'{{{2}}}\' \3"', content
    )

    # 5. 修复其他复杂嵌套情况
    content = re.sub(
        r'f"([^"]*){([^}]*{[^}]*}[^}]*)}([^"]*)"', r'f"\1{{\2}}\3"', content
    )

    return content


def fix_file(file_path: Path) -> bool:
    """修复单个文件中的f-string错误"""
    try:
        print(f"修复文件: {file_path}")

        # 读取原始内容
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # 修复错误
        fixed_content = fix_fstring_errors(original_content)

        # 检查是否有变化
        if original_content != fixed_content:
            # 写入修复后的内容
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            print(f"  ✅ 已修复 {file_path}")
            return True
        else:
            print(f"  ℹ️  {file_path} 无需修复")
            return False

    except Exception as e:
        print(f"  ❌ 修复 {file_path} 失败: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = Path(".")

    print(f"在 {target_path} 中搜索并修复f-string语法错误...")

    fixed_count = 0
    total_count = 0

    # 查找所有Python文件
    for py_file in target_path.rglob("*.py"):
        total_count += 1
        if fix_file(py_file):
            fixed_count += 1

    print(f"\n📊 修复完成: {fixed_count}/{total_count} 个文件已修复")


if __name__ == "__main__":
    main()
