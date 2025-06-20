#!/usr/bin/env python3
"""
批量更新CONFIG引用的工具脚本
"""

import os
import re
from pathlib import Path


def update_config_references(file_path):
    """更新文件中的CONFIG引用"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 替换规则
        replacements = {
            r"CONFIG\.default_language": "CONFIG.core.default_language",
            r"CONFIG\.source_language": "CONFIG.core.source_language",
            r"CONFIG\.keyed_dir": "CONFIG.core.keyed_dir",
            r"CONFIG\.definjected_dir": "CONFIG.core.definjected_dir",
            r"CONFIG\.def_injected_dir": "CONFIG.core.definjected_dir",
            r"CONFIG\.debug_mode": "CONFIG.core.debug_mode",
            r"CONFIG\.log_file": "CONFIG.core.log_file",
            r"CONFIG\.log_format": "CONFIG.core.log_format",
        }

        # 应用替换
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 已更新: {file_path}")
            return True
        else:
            print(f"⭕ 无需更新: {file_path}")
            return False

    except Exception as e:
        print(f"❌ 更新失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    print("=== 批量更新CONFIG引用工具 ===")

    # 需要更新的文件列表
    files_to_update = [
        "day_translation/core/exporters.py",
        "day_translation/core/generators.py",
        "day_translation/utils/batch_processor.py",
        "day_translation/utils/parallel_corpus.py",
        "day_translation/utils/path_manager.py",
        "test_unified_config.py",
    ]

    updated_count = 0

    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_config_references(file_path):
                updated_count += 1
        else:
            print(f"⚠️ 文件不存在: {file_path}")

    print(f"\n=== 更新完成，共更新了 {updated_count} 个文件 ===")


if __name__ == "__main__":
    main()
