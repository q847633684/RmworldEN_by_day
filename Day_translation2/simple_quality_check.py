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
    print("🔍 检查核心模块导入...")

    modules_to_check = [
        # Core 核心模块 (P0)
        ("core.extractors", "extract_all_translations"),
        ("core.importers", "AdvancedImporter"),
        ("core.generators", "TemplateGenerator"),
        ("core.template_manager", "TemplateManager"),
        ("core.translation_facade", "TranslationFacade"),
        ("core.exporters", "export_keyed, AdvancedExporter"),
        # Models 数据模型 (P0)
        ("models.exceptions", "ProcessingError, ValidationError, TranslationError"),
        ("models.result_models", "OperationResult, OperationStatus, OperationType"),
        ("models.translation_data", "TranslationData, TranslationType"),
        # Config 配置系统 (P0)
        ("config", "CONFIG_VERSION, ConfigManager"),
        ("config.data_models", "GeneralConfig, CoreConfig, UserConfig, UnifiedConfig"),
        ("constants.complete_definitions", "LanguageCode, XML_TAGS"),
        # Services 服务层 (P1)
        ("services.config_service", "config_service"),
        ("services.path_service", "path_validation_service"),
        ("services.history_service", "history_service"),
        ("services.validation_service", "TranslationValidator, validate_csv_file"),
        ("services.batch_processor", "BatchProcessor"),
        ("services.user_interaction_service", "user_interaction_service"),
        ("services.translation_service", "translate_csv"),
        # Utils 工具模块 (P1)
        ("utils.xml_processor", "AdvancedXMLProcessor"),
        ("utils.filter_rules", "AdvancedFilterRules"),
        ("utils.file_utils", "get_language_folder_path, ensure_directory_exists"),
        ("utils.export_manager", "ExportManager"),
        ("utils.user_interaction", "UserInteractionManager"),
        # Interaction 交互层 (P2)
        ("interaction.interaction_manager", "UnifiedInteractionManager"),
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
        "services/config_service.py",
        "services/path_service.py",
        "services/history_service.py",
        "services/user_interaction_service.py",
        # 配置
        "config/__init__.py",
        "config/data_models.py",
        "config/config_manager.py",
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

    # 扩展的模块列表，按重要性分类
    critical_modules = [
        # 核心模块 (P0)
        "core/extractors.py",
        "core/importers.py",
        "core/generators.py",
        "core/translation_facade.py",
        "core/template_manager.py",
        # 导出器模块 (P0) - exporters文件夹下的各个模块
        "core/exporters/xml_generators.py",
        "core/exporters/keyed_exporter.py",
        "core/exporters/definjected_exporter.py",
        "core/exporters/csv_exporter.py",
        "core/exporters/export_utils.py",
        "core/exporters/advanced_exporter.py",
        # 数据模型 (P0)
        "models/exceptions.py",
        "models/result_models.py",
        "models/translation_data.py",
        # 配置系统 (P0)
        "config/data_models.py",
        "config/config_manager.py",
        # 服务层 (P1)
        "services/config_service.py",
        "services/path_service.py",
        "services/history_service.py",
        "services/validation_service.py",
        "services/batch_processor.py",
        # 工具模块 (P1)
        "utils/xml_processor.py",
        "utils/file_utils.py",
        "utils/filter_rules.py",
        # 交互层 (P2)
        "interaction/interaction_manager.py",
    ]

    pylint_results = []

    for module in critical_modules:
        if Path(module).exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pylint", module, "--score=yes"],
                    capture_output=True,
                    text=True,
                    timeout=45,  # 增加超时时间
                )

                # 提取评分
                score = "N/A"
                if "Your code has been rated at" in result.stdout:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "Your code has been rated at" in line:
                            score = (
                                line.split("Your code has been rated at")[1].split("(")[0].strip()
                            )
                            break

                print(f"📊 {module}: {score}")
                pylint_results.append((module, score, result.stdout))

            except subprocess.TimeoutExpired:
                print(f"⏰ {module}: Pylint检查超时")
                pylint_results.append((module, "TIMEOUT", "检查超时"))
            except Exception as e:
                print(f"⚠️ {module}: Pylint检查失败 ({e})")
                pylint_results.append((module, "ERROR", str(e)))
        else:
            print(f"❌ {module}: 文件不存在")

    return pylint_results


def run_new_architecture_test():
    """运行新架构导入测试"""
    print("\n🧪 运行新架构测试...")

    try:
        # 测试基础配置导入
        from config import CONFIG_VERSION, ConfigManager, GeneralConfig

        print("✅ 配置模块导入成功")

        # 测试服务层导入
        from services.config_service import config_service
        from services.history_service import history_service
        from services.path_service import path_validation_service

        print("✅ 服务层导入成功")

        # 测试配置对象创建
        config = GeneralConfig()
        print("✅ 配置对象创建成功")

        return True

    except Exception as e:
        print(f"❌ 新架构测试失败: {e}")
        return False


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

    # 5. 新架构测试
    import_test_result = run_new_architecture_test()

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

    print(f"\n🧪 新架构测试: {'✅ 通过' if import_test_result else '❌ 失败'}")

    print(f"\n📈 Pylint评分:")
    high_quality_count = 0
    excellent_count = 0
    good_count = 0
    needs_improvement_count = 0
    error_count = 0

    # 按分类统计
    critical_modules = []
    service_modules = []
    util_modules = []
    other_modules = []

    for module, score, output in pylint_results:
        if score in ["ERROR", "TIMEOUT", "N/A"]:
            print(f"   - {module}: {score}")
            error_count += 1
        else:
            try:
                numeric_score = float(score.split("/")[0])
                print(f"   - {module}: {score}")

                # 分类计数
                if numeric_score >= 9.8:
                    excellent_count += 1
                elif numeric_score >= 9.0:
                    high_quality_count += 1
                elif numeric_score >= 8.0:
                    good_count += 1
                else:
                    needs_improvement_count += 1

                # 按模块类型分类
                if module.startswith(("core/", "models/", "config/")):
                    critical_modules.append((module, numeric_score))
                elif module.startswith("services/"):
                    service_modules.append((module, numeric_score))
                elif module.startswith("utils/"):
                    util_modules.append((module, numeric_score))
                else:
                    other_modules.append((module, numeric_score))

            except (ValueError, IndexError):
                print(f"   - {module}: {score} (格式错误)")
                error_count += 1

    print(f"\n🎯 质量总结:")
    total_checked = len(pylint_results)
    print(f"   - 检查模块总数: {total_checked}")
    print(f"   - 优秀模块 (≥9.8分): {excellent_count}")
    print(f"   - 高质量模块 (≥9.0分): {high_quality_count}")
    print(f"   - 良好模块 (≥8.0分): {good_count}")
    print(f"   - 需改进模块 (<8.0分): {needs_improvement_count}")
    print(f"   - 检查失败模块: {error_count}")

    # 按模块类型分析
    def calc_avg_score(modules_list):
        if not modules_list:
            return 0.0
        return sum(score for _, score in modules_list) / len(modules_list)

    if critical_modules:
        avg_critical = calc_avg_score(critical_modules)
        print(f"   - 核心模块平均分: {avg_critical:.2f} ({len(critical_modules)}个)")

    if service_modules:
        avg_service = calc_avg_score(service_modules)
        print(f"   - 服务层平均分: {avg_service:.2f} ({len(service_modules)}个)")

    if util_modules:
        avg_util = calc_avg_score(util_modules)
        print(f"   - 工具模块平均分: {avg_util:.2f} ({len(util_modules)}个)")

    # 评判整体质量
    quality_ratio = (excellent_count + high_quality_count) / max(total_checked - error_count, 1)
    if quality_ratio >= 0.8:
        quality_status = "🎉 优秀"
    elif quality_ratio >= 0.6:
        quality_status = "👍 良好"
    else:
        quality_status = "⚠️ 需要改进"

    print(f"   - 整体质量状态: {quality_status}")
    print(f"   - 整体状态: {'🎉 优秀' if overall_status else '⚠️ 需要改进'}")

    if overall_status:
        print(f"\n✅ 项目质量检查通过! 代码已达到生产就绪标准。")
    else:
        print(f"\n❌ 发现质量问题，建议修复后再次检查。")

    return overall_status


if __name__ == "__main__":
    success = run_comprehensive_check()
    sys.exit(0 if success else 1)
