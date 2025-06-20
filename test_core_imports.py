#!/usr/bin/env python3
"""
Day汉化项目 - 核心模块导入测试

测试核心模块是否能够正常导入，确保模块结构正确。
"""

import sys
import traceback
from pathlib import Path


def test_core_imports():
    """测试核心模块导入"""
    print("🔍 开始核心模块导入测试...")

    # 添加Day_translation2到Python路径
    day_translation2_path = Path(__file__).parent / "Day_translation2"
    if str(day_translation2_path) not in sys.path:
        sys.path.insert(0, str(day_translation2_path))

    failed_imports = []
    successful_imports = []
    # 测试核心模块导入
    core_modules = [
        "config",
        "config.config_models",
        "constants.complete_definitions",
        "models.exceptions",
        "models.translation_data",
        "models.result_models",
        "utils.filter_rules",
        "utils.file_utils",
        "utils.xml_processor",
        "core.extractors",
        "core.generators",
        "core.importers",
        "core.exporters",
        "services.validation_service",
        "services.batch_processor",
    ]

    for module_name in core_modules:
        try:
            __import__(module_name)
            successful_imports.append(module_name)
            print(f"  ✅ {module_name}")
        except Exception as e:
            failed_imports.append((module_name, str(e)))
            print(f"  ❌ {module_name}: {e}")
    # 输出测试结果
    print("\n📊 导入测试结果:")
    success_rate = len(successful_imports) / len(core_modules) * 100
    print(
        f"  成功: {len(successful_imports)}/{len(core_modules)} ({success_rate:.1f}%)"
    )
    print(f"  失败: {len(failed_imports)}/{len(core_modules)}")

    if failed_imports:
        print("\n❌ 失败的模块:")
        for module, error in failed_imports:
            print(f"  - {module}: {error}")
        return False
    else:
        print("\n🎉 所有核心模块导入成功！")
        return True


if __name__ == "__main__":
    try:
        success = test_core_imports()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        traceback.print_exc()
        sys.exit(1)
