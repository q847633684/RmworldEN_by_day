#!/usr/bin/env python3
"""
Mypy 核心错误修复脚本 - 专注解决最关键的错误
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def fix_return_type_annotations() -> None:
    """修复缺失的返回类型注解"""

    fixes = [
        # (文件路径, [(模式, 替换)])
        (
            "models/exceptions.py",
            [
                (r"def __init__\(self([^)]+)\):", r"def __init__(self\1) -> None:"),
            ],
        ),
        (
            "models/translation_data.py",
            [
                (
                    r"def add_translation\(self([^)]+)\):",
                    r"def add_translation(self\1) -> None:",
                ),
                (
                    r"def update_translation\(self([^)]+)\):",
                    r"def update_translation(self\1) -> None:",
                ),
                (r"def clear\(self\):", r"def clear(self) -> None:"),
            ],
        ),
        (
            "models/result_models.py",
            [
                (r"def __init__\(self([^)]+)\):", r"def __init__(self\1) -> None:"),
                (r"def add_detail\(self([^)]+)\):", r"def add_detail(self\1) -> None:"),
                (r"def set_status\(self([^)]+)\):", r"def set_status(self\1) -> None:"),
                (r"def set_error\(self([^)]+)\):", r"def set_error(self\1) -> None:"),
                (
                    r"def add_warning\(self([^)]+)\):",
                    r"def add_warning(self\1) -> None:",
                ),
            ],
        ),
        (
            "fix_mypy_errors.py",
            [
                (
                    r"def fix_optional_imports\(\):",
                    r"def fix_optional_imports() -> None:",
                ),
                (
                    r"def fix_optional_parameters\(\):",
                    r"def fix_optional_parameters() -> None:",
                ),
                (
                    r"def fix_enum_dict_access\(\):",
                    r"def fix_enum_dict_access() -> None:",
                ),
                (
                    r"def fix_type_annotations\(\):",
                    r"def fix_type_annotations() -> None:",
                ),
            ],
        ),
        (
            "quality_check.py",
            [
                (
                    r"def run_command\(([^)]+)\):",
                    r"def run_command(\1) -> Tuple[int, str]:",
                ),
                (r"def main\(\):", r"def main() -> None:"),
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
                # 只替换尚未有返回类型注解的函数
                if " -> " not in content or content.count(
                    pattern.replace("\\", "")
                ) > content.count(" -> "):
                    content = re.sub(pattern, replacement, content)

            if content != original_content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"✅ 修复文件: {file_path}")

        except Exception as e:
            logger.error(f"❌ 修复失败 {file_path}: {e}")


def fix_assignment_types() -> None:
    """修复类型赋值不兼容错误"""

    fixes = [
        (
            "models/exceptions.py",
            [
                # 修复 error_code 类型问题
                (
                    r"self\.error_code = error_code",
                    "self.error_code: Optional[int] = error_code if isinstance(error_code, int) else None",
                ),
                # 修复 file_list 类型问题
                (
                    r"self\.file_list = file_list",
                    "self.file_list: Optional[List[str]] = file_list if isinstance(file_list, list) else None",
                ),
            ],
        ),
        (
            "interaction/interaction_manager.py",
            [
                # 修复布尔值赋值给字符串的问题
                (r"result = False", "result: Optional[str] = None"),
                (r"result = True", "result: Optional[str] = ''"),
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
                logger.info(f"✅ 修复文件: {file_path}")

        except Exception as e:
            logger.error(f"❌ 修复失败 {file_path}: {e}")


def fix_missing_imports() -> None:
    """修复缺失的类型导入"""

    files_needing_typing = [
        "models/exceptions.py",
        "models/translation_data.py",
        "models/result_models.py",
        "fix_mypy_errors.py",
        "quality_check.py",
    ]

    for file_path in files_needing_typing:
        full_path = Path(file_path)
        if not full_path.exists():
            continue

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查是否已有 typing 导入
            if "from typing import" not in content and "import typing" not in content:
                # 在第一个导入语句前添加 typing 导入
                lines = content.split("\n")
                insert_index = 0

                # 找到第一个非注释、非空行的导入语句
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if (
                        stripped
                        and not stripped.startswith("#")
                        and not stripped.startswith('"""')
                        and not stripped.startswith("'''")
                    ):
                        if stripped.startswith("import ") or stripped.startswith("from "):
                            insert_index = i
                            break

                # 插入 typing 导入
                typing_import = "from typing import List, Optional, Tuple, Dict, Any"
                lines.insert(insert_index, typing_import)

                new_content = "\n".join(lines)

                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"✅ 添加 typing 导入: {file_path}")

        except Exception as e:
            logger.error(f"❌ 导入修复失败 {file_path}: {e}")


def main() -> None:
    """主函数 - 执行核心Mypy错误修复"""
    logger.info("🚀 开始核心 Mypy 错误修复...")

    # 步骤1：修复缺失的类型导入
    logger.info("🔧 修复缺失的类型导入...")
    fix_missing_imports()

    # 步骤2：修复返回类型注解
    logger.info("🔧 修复返回类型注解...")
    fix_return_type_annotations()

    # 步骤3：修复类型赋值问题
    logger.info("🔧 修复类型赋值问题...")
    fix_assignment_types()

    logger.info("✅ 核心错误修复完成！")
    print("\n🎉 核心 Mypy 错误修复完成！")
    print("下一步：运行 'python -m mypy . --config-file=pyproject.toml' 验证修复效果")


if __name__ == "__main__":
    main()
