#!/usr/bin/env python3
"""
Mypy 基础错误修复脚本 - 只修复最关键的 Optional 参数类型错误
"""

import re
from pathlib import Path


def fix_optional_parameters():
    """修复 Optional 参数类型错误 - 保守方法"""

    # 只修复最关键的几个文件
    fixes = [
        (
            "core/template_manager.py",
            [
                (r"output_dir: str = None", "output_dir: Optional[str] = None"),
                (r"en_keyed_dir: str = None", "en_keyed_dir: Optional[str] = None"),
            ],
        ),
    ]

    for file_path, patterns in fixes:
        full_path = Path(file_path)
        if not full_path.exists():
            continue

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            if content != original_content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ 修复文件: {file_path}")

        except Exception as e:
            print(f"❌ 修复失败 {file_path}: {e}")


if __name__ == "__main__":
    fix_optional_parameters()
    print("基础修复完成")
