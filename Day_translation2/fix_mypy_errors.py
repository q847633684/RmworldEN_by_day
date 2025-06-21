#!/usr/bin/env python3
"""
Day Translation 2 - Mypy 类型错误修复脚本

根据专业AI建议，采用渐进式类型检查优化策略：
1. 优先修复高频错误 (Optional参数)
2. 逐步完善类型注解
3. 保持代码可读性和维护性
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MypyErrorFixer:
    """Mypy 错误修复器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixed_files = []
        self.errors_fixed = 0

    def fix_optional_parameters(self):
        """修复 Optional 参数类型错误"""
        logger.info("🔧 开始修复 Optional 参数类型错误...")

        # 需要修复的文件和模式
        fixes = [
            # template_manager.py
            {
                "file": "core/template_manager.py",
                "patterns": [
                    (r"language: str = None", "language: Optional[str] = None"),
                    (r"output_dir: str = None", "output_dir: Optional[str] = None"),
                    (r"en_keyed_dir: str = None", "en_keyed_dir: Optional[str] = None"),
                ],
            },
            # exporters.py
            {
                "file": "core/exporters.py",
                "patterns": [
                    (r"output_dir: str = None", "output_dir: Optional[str] = None"),
                    (r"language: str = None", "language: Optional[str] = None"),
                ],
            },
            # importers.py
            {
                "file": "core/importers.py",
                "patterns": [
                    (r"language: str = None", "language: Optional[str] = None"),
                ],
            },
            # translation_facade.py
            {
                "file": "core/translation_facade.py",
                "patterns": [
                    (r"language: str = None", "language: Optional[str] = None"),
                    (r"en_keyed_dir: str = None", "en_keyed_dir: Optional[str] = None"),
                    (r"output_csv: str = None", "output_csv: Optional[str] = None"),
                    (r"output_dir: str = None", "output_dir: Optional[str] = None"),
                    (
                        r"translations: list\[Any\] = None",
                        "translations: Optional[List[Any]] = None",
                    ),
                ],
            },
            # extractors.py
            {
                "file": "core/extractors.py",
                "patterns": [
                    (r"language: str = None", "language: Optional[str] = None"),
                ],
            },
            # filter_rules.py
            {
                "file": "utils/filter_rules.py",
                "patterns": [
                    (r"field_name: str = None", "field_name: Optional[str] = None"),
                ],
            },
            # config_models.py
            {
                "file": "config/config_models.py",
                "patterns": [
                    (r"config_path: str = None", "config_path: Optional[str] = None"),
                ],
            },
        ]

        for fix_spec in fixes:
            self._apply_file_fixes(fix_spec)

    def fix_enum_dict_access(self):
        """修复枚举类型字典访问错误"""
        logger.info("🔧 开始修复枚举类型字典访问错误...")

        # 修复模式：将枚举.value传递给字典get方法
        fixes = [
            {
                "file": "constants/complete_definitions.py",
                "patterns": [
                    (r"\.get\(([A-Za-z_]+), ", r".get(\1.value, "),
                ],
            },
            {
                "file": "models/translation_data.py",
                "patterns": [
                    (r"\.get\(([A-Za-z_]+), ", r".get(\1.value, "),
                ],
            },
            {
                "file": "models/result_models.py",
                "patterns": [
                    (r"\.get\(([A-Za-z_]+), ", r".get(\1.value, "),
                ],
            },
        ]

        for fix_spec in fixes:
            self._apply_file_fixes(fix_spec)

    def fix_type_annotations(self):
        """修复类型注解错误"""
        logger.info("🔧 开始修复类型注解错误...")

        fixes = [
            # corpus_generator.py - 修复 any 为 Any
            {
                "file": "services/corpus_generator.py",
                "patterns": [
                    (r": any\b", ": Any"),
                ],
            },
            # 修复 Path 类型错误
            {
                "file": "core/template_manager.py",
                "patterns": [
                    (
                        r"original_mod_dir = self\.generator\.mod_dir",
                        "original_mod_dir: str = self.generator.mod_dir",
                    ),
                ],
            },
        ]

        for fix_spec in fixes:
            self._apply_file_fixes(fix_spec)

    def add_missing_imports(self):
        """添加缺失的导入"""
        logger.info("🔧 开始添加缺失的 Optional 导入...")

        # 需要添加 Optional 导入的文件
        files_need_optional = [
            "core/template_manager.py",
            "core/exporters.py",
            "core/importers.py",
            "core/translation_facade.py",
            "core/extractors.py",
            "utils/filter_rules.py",
            "config/config_models.py",
        ]

        for file_path in files_need_optional:
            self._add_optional_import(file_path)

    def _apply_file_fixes(self, fix_spec: dict):
        """应用文件修复"""
        file_path = self.project_root / fix_spec["file"]

        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            for pattern, replacement in fix_spec["patterns"]:
                content = re.sub(pattern, replacement, content)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.fixed_files.append(str(file_path))
                self.errors_fixed += len(fix_spec["patterns"])
                logger.info(f"✅ 修复文件: {file_path}")

        except Exception as e:
            logger.error(f"❌ 修复文件失败 {file_path}: {e}")

    def _add_optional_import(self, file_path: str):
        """添加 Optional 导入"""
        full_path = self.project_root / file_path

        if not full_path.exists():
            return

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查是否已经导入了 Optional
            if "Optional" in content and "from typing import" in content:
                return

            # 查找 typing 导入行
            import_pattern = r"from typing import (.+)"
            match = re.search(import_pattern, content)

            if match:
                imports = match.group(1)
                if "Optional" not in imports:
                    new_imports = imports.rstrip() + ", Optional"
                    new_line = f"from typing import {new_imports}"
                    content = re.sub(import_pattern, new_line, content)

                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    logger.info(f"✅ 添加 Optional 导入: {full_path}")

        except Exception as e:
            logger.error(f"❌ 添加导入失败 {full_path}: {e}")

    def run_all_fixes(self):
        """运行所有修复"""
        logger.info("🚀 开始 Mypy 类型错误批量修复...")

        self.add_missing_imports()
        self.fix_optional_parameters()
        self.fix_enum_dict_access()
        self.fix_type_annotations()

        logger.info("✅ 修复完成！")
        logger.info(f"   - 修复文件数: {len(set(self.fixed_files))}")
        logger.info(f"   - 修复错误数: {self.errors_fixed}")

        return len(set(self.fixed_files)), self.errors_fixed


def main():
    """主函数"""
    project_root = os.getcwd()

    fixer = MypyErrorFixer(project_root)
    files_fixed, errors_fixed = fixer.run_all_fixes()

    print("\n🎉 Mypy 类型错误修复完成！")
    print(f"📁 修复文件: {files_fixed} 个")
    print(f"🔧 修复错误: {errors_fixed} 个")
    print(
        "\n下一步：运行 'python -m mypy core utils services --config-file=mypy.ini' 验证修复效果"
    )


if __name__ == "__main__":
    main()