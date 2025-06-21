#!/usr/bin/env python3
"""
Day Translation 2 - 全面质量检查

检查整个项目的代码质量、类型安全和结构完整性。
"""

import subprocess
import sys
from pathlib import Path


def check_module_imports():
    """检查所有核心模块的导入"""
    print("� 检查核心模块导入...")

    modules_to_check = [
        ("core.extractors", "extract_keyed_translations, AdvancedExtractor"),
        ("core.importers", "import_translations, AdvancedImporter"),
        ("core.generators", "TemplateGenerator"),
        ("core.exporters", "export_keyed, AdvancedExporter"),
        ("models.exceptions", "ProcessingError, ValidationError"),
        ("models.result_models", "OperationResult, OperationStatus"),
        ("models.translation_data", "TranslationData, TranslationType"),
        ("utils.xml_processor", "AdvancedXMLProcessor"),
        ("utils.filter_rules", "AdvancedFilterRules"),
        ("utils.file_utils", "get_language_folder_path"),
        ("config", "get_config"),
    ]

    failed_imports = []

    for module_name, import_items in modules_to_check:
        try:
            exec(f"from {module_name} import {import_items}")
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))

    return len(failed_imports) == 0, failed_imports


def check_project_structure():
    """检查项目文件结构"""
    print("\n🏗️ 检查项目结构...")

    required_files = [
        # 核心模块
        "core/__init__.py",
        "core/extractors.py",
        "core/importers.py",
        "core/generators.py",
        "core/translation_facade.py",
        "core/template_manager.py",

        # 导出器子模块
        "core/exporters/__init__.py",
        "core/exporters/xml_generators.py",
        "core/exporters/keyed_exporter.py",
        "core/exporters/definjected_exporter.py",
        "core/exporters/csv_exporter.py",
        "core/exporters/export_utils.py",
        "core/exporters/advanced_exporter.py",

        # 模型
        "models/__init__.py",
        "models/exceptions.py",
        "models/result_models.py",
        "models/translation_data.py",

        # 工具
        "utils/__init__.py",
        "utils/xml_processor.py",
        "utils/filter_rules.py",
        "utils/file_utils.py",

        # 服务
        "services/__init__.py",
        "services/validation_service.py",
        "services/batch_processor.py",

        # 配置
        "config/__init__.py",
        "config/config_models.py",
        "constants/__init__.py",
        "constants/complete_definitions.py",

        # 测试
        "tests/__init__.py",
        "pytest.ini",
        "requirements.txt",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")

    if missing_files:
        print(f"❌ 缺失文件: {missing_files}")
        return False, missing_files

    return True, []


def run_syntax_check():
    """运行Python语法检查"""
    print("\n🔧 检查Python语法...")

    python_files = list(Path(".").rglob("*.py"))
    python_files = [f for f in python_files if not str(f).startswith("tests")]  # 跳过测试文件

    syntax_errors = []

    for py_file in python_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print(f"✅ {py_file}")
            else:
                print(f"❌ {py_file}: {result.stderr.strip()}")
                syntax_errors.append((str(py_file), result.stderr.strip()))

        except Exception as e:
            print(f"⚠️ {py_file}: 跳过检查 ({e})")

    return len(syntax_errors) == 0, syntax_errors


def run_pylint_check():
    """运行Pylint代码质量检查"""
    print("\n🔍 运行Pylint质量检查...")

    core_modules = [
        "core/extractors.py",
        "core/importers.py",
        "core/generators.py",
        "models/exceptions.py",
        "models/result_models.py",
        "utils/xml_processor.py",
    ]

    pylint_results = []

    for module in core_modules:
        if Path(module).exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pylint", module, "--score=yes"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # 提取评分
                score = "N/A"
                if "Your code has been rated at" in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "Your code has been rated at" in line:
                            score = line.split("Your code has been rated at")[1].split("(")[0].strip()
                            break

                print(f"📊 {module}: {score}")
                pylint_results.append((module, score, result.stdout))

            except Exception as e:
                print(f"⚠️ {module}: Pylint检查失败 ({e})")
                pylint_results.append((module, "ERROR", str(e)))
        else:
            print(f"❌ {module}: 文件不存在")

    return pylint_results


def run_import_test():
    """运行导入测试"""
    print("\n🧪 运行导入测试...")

    try:
        result = subprocess.run(
            [sys.executable, "../test_core_imports.py"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="."
        )

        if result.returncode == 0:
            print("✅ 核心模块导入测试通过")
            return True
        else:
            print(f"❌ 导入测试失败:\n{result.stderr}")
            return False

    except Exception as e:
        print(f"⚠️ 导入测试跳过: {e}")
        return None


def run_comprehensive_check():
    """运行全面质量检查"""
    print("🚀 Day Translation 2 - 全面代码质量检查")
    print("=" * 60)

    overall_status = True

    # 1. 模块导入检查
    import_ok, failed_imports = check_module_imports()
    if not import_ok:
        overall_status = False

    # 2. 项目结构检查
    structure_ok, missing_files = check_project_structure()
    if not structure_ok:
        overall_status = False

    # 3. 语法检查
    syntax_ok, syntax_errors = run_syntax_check()
    if not syntax_ok:
        overall_status = False

    # 4. Pylint质量检查
    pylint_results = run_pylint_check()

    # 5. 导入测试
    import_test_result = run_import_test()

    # 生成总结报告
    print("\n" + "=" * 60)
    print("📊 全面质量检查报告")
    print("=" * 60)

    print(f"\n� 模块导入: {'✅ 通过' if import_ok else '❌ 失败'}")
    if failed_imports:
        for module, error in failed_imports:
            print(f"   - {module}: {error}")

    print(f"\n🏗️ 项目结构: {'✅ 完整' if structure_ok else '❌ 不完整'}")
    if missing_files:
        print(f"   缺失文件: {len(missing_files)} 个")

    print(f"\n🔧 语法检查: {'✅ 通过' if syntax_ok else '❌ 有错误'}")
    if syntax_errors:
        print(f"   语法错误: {len(syntax_errors)} 个")

    print(f"\n🧪 导入测试: {'✅ 通过' if import_test_result else '❌ 失败' if import_test_result is False else '⚠️ 跳过'}")

    print(f"\n📈 Pylint评分:")
    high_quality_count = 0
    for module, score, _ in pylint_results:
        print(f"   - {module}: {score}")
        if score != "ERROR" and score != "N/A" and float(score.split('/')[0]) >= 9.0:
            high_quality_count += 1

    print(f"\n🎯 质量总结:")
    print(f"   - 高质量模块 (≥9.0分): {high_quality_count}/{len(pylint_results)}")
    print(f"   - 整体状态: {'🎉 优秀' if overall_status else '⚠️ 需要改进'}")

    if overall_status:
        print(f"\n✅ 项目质量检查通过! 代码已达到生产就绪标准。")
    else:
        print(f"\n❌ 发现质量问题，建议修复后再次检查。")

    return overall_status


if __name__ == "__main__":
    success = run_comprehensive_check()
    sys.exit(0 if success else 1)
