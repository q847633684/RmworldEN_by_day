#!/usr/bin/env python3
"""
Day汉化项目 - 代码质量检查脚本

自动运行所有代码质量检查工具，包括格式化、静态检查、测试等。
使用工具链: Black + isort + Pylint + Mypy (Flake8已禁用)
支持接口清理检查，移除旧的兼容接口
"""

import ast
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description, continue_on_error=True):
    """运行命令并显示结果"""
    print(f"\n🔄 {description}...")
    print(f"执行命令: {' '.join(command)}")

    try:
        # 获取当前工作目录（应该是Day_translation2）
        current_dir = os.getcwd()
        print(f"当前目录: {current_dir}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=current_dir,
            check=False,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            if result.stdout and result.stdout.strip():
                print("输出:", result.stdout.strip())
            return True
        else:
            print(f"❌ {description} - 失败")
            if result.stderr and result.stderr.strip():
                print("错误:", result.stderr.strip())
            if result.stdout and result.stdout.strip():
                print("输出:", result.stdout.strip())
            if not continue_on_error:
                sys.exit(1)
            return False

    except FileNotFoundError:
        print(f"⚠️ {description} - 工具未安装")
        return False
    except (subprocess.SubprocessError, OSError) as e:
        print(f"❌ {description} - 异常: {e}")
        return False


def check_legacy_interfaces():
    """检查是否存在遗留接口和兼容代码"""
    print("\n🔍 检查遗留接口...")

    legacy_patterns = [
        "# TODO: 兼容",
        "# DEPRECATED",
        "# 旧接口兼容",
        "# Legacy",
        "_legacy_",
        "_compat_",
        "_old_",
        "compatibility",
        "backward_compat",
    ]

    found_legacy = []
    day_translation_dir = Path("Day_translation2")

    if not day_translation_dir.exists():
        print("❌ Day_translation2目录不存在")
        return False

    for py_file in day_translation_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                for i, line in enumerate(content.splitlines(), 1):
                    for pattern in legacy_patterns:
                        if pattern.lower() in line.lower():
                            found_legacy.append(f"{py_file}:{i} - {line.strip()}")
        except Exception as e:
            print(f"⚠️ 读取文件失败 {py_file}: {e}")

    if found_legacy:
        print(f"❌ 发现 {len(found_legacy)} 个遗留接口:")
        for item in found_legacy[:10]:  # 只显示前10个
            print(f"   {item}")
        if len(found_legacy) > 10:
            print(f"   ... 还有 {len(found_legacy) - 10} 个")
        return False
    else:
        print("✅ 未发现遗留接口")
        return True


def check_import_cleanup():
    """检查导入清理情况"""
    print("\n🔍 检查导入清理...")

    unused_patterns = [
        "import.*# unused",
        "from.*# unused",
        "# TODO: remove",
        "# 待移除",
    ]

    found_unused = []
    day_translation_dir = Path("Day_translation2")

    for py_file in day_translation_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                for i, line in enumerate(content.splitlines(), 1):
                    for pattern in unused_patterns:
                        if pattern.lower() in line.lower():
                            found_unused.append(f"{py_file}:{i} - {line.strip()}")
        except Exception as e:
            print(f"⚠️ 读取文件失败 {py_file}: {e}")

    if found_unused:
        print(f"❌ 发现 {len(found_unused)} 个待清理的导入:")
        for item in found_unused:
            print(f"   {item}")
        return False
    else:
        print("✅ 导入已清理")
        return True


def analyze_system_architecture():
    """分析系统架构，详细到模块→类→函数→逻辑→返回值"""
    print("\n🏗️ 系统架构分析...")

    day_translation_dir = Path("Day_translation2")
    if not day_translation_dir.exists():
        print("❌ Day_translation2目录不存在")
        return False

    architecture_analysis = {
        "modules": {},
        "classes": {},
        "functions": {},
        "type_annotations": {"total": 0, "annotated": 0},
        "return_types": {"total": 0, "annotated": 0},
    }

    for py_file in day_translation_dir.rglob("*.py"):
        if py_file.name.startswith("__") and py_file.name.endswith("__.py"):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 分析模块
            module_path = str(py_file.relative_to(day_translation_dir))
            architecture_analysis["modules"][module_path] = {
                "lines": len(content.splitlines()),
                "classes": [],
                "functions": [],
                "imports": [],
            }

            # 分析类、函数、类型注解
            _analyze_python_file(content, py_file, architecture_analysis)

        except Exception as e:
            print(f"⚠️ 分析文件失败 {py_file}: {e}")

    # 生成分析报告
    _generate_architecture_report(architecture_analysis)
    return True


def _analyze_python_file(content, py_file, analysis):
    """分析单个Python文件的架构"""
    import ast
    import re

    try:
        tree = ast.parse(content)
        module_path = str(py_file.relative_to(Path("Day_translation2")))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 分析类
                class_info = {
                    "name": node.name,
                    "methods": [],
                    "type_annotated": False,
                    "file": module_path,
                }

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = _analyze_function(item)
                        class_info["methods"].append(method_info)

                analysis["classes"][f"{module_path}::{node.name}"] = class_info
                analysis["modules"][module_path]["classes"].append(node.name)

            elif isinstance(node, ast.FunctionDef):
                # 分析函数
                func_info = _analyze_function(node)
                func_key = f"{module_path}::{node.name}"
                analysis["functions"][func_key] = func_info
                analysis["modules"][module_path]["functions"].append(node.name)

        # 分析导入语句
        imports = re.findall(r"^(?:from .+ )?import .+$", content, re.MULTILINE)
        analysis["modules"][module_path]["imports"] = imports

    except SyntaxError as e:
        print(f"⚠️ 语法错误 {py_file}: {e}")
    except Exception as e:
        print(f"⚠️ AST分析失败 {py_file}: {e}")


def _analyze_function(func_node):
    """分析函数的类型注解和返回值"""
    func_info = {
        "name": func_node.name,
        "args": len(func_node.args.args),
        "has_return_annotation": func_node.returns is not None,
        "has_arg_annotations": False,
        "is_async": isinstance(func_node, ast.AsyncFunctionDef),
        "complexity": "unknown",
    }

    # 检查参数注解
    for arg in func_node.args.args:
        if arg.annotation:
            func_info["has_arg_annotations"] = True
            break

    # 简单复杂度分析 (行数)
    if hasattr(func_node, "lineno") and hasattr(func_node, "end_lineno"):
        func_info["complexity"] = func_node.end_lineno - func_node.lineno

    return func_info


def _generate_architecture_report(analysis):
    """生成架构分析报告"""
    print("\n📊 系统架构分析报告")
    print("=" * 50)

    # 模块统计
    total_modules = len(analysis["modules"])
    total_classes = len(analysis["classes"])
    total_functions = len(analysis["functions"])

    print("\n📦 模块结构:")
    print(f"  总模块数: {total_modules}")
    print(f"  总类数: {total_classes}")
    print(f"  总函数数: {total_functions}")

    # 类型注解分析
    annotated_functions = sum(
        1
        for f in analysis["functions"].values()
        if f["has_return_annotation"] and f["has_arg_annotations"]
    )
    type_coverage = (
        (annotated_functions / total_functions * 100) if total_functions > 0 else 0
    )

    print("\n🔍 类型安全分析:")
    print(f"  完整类型注解函数: {annotated_functions}/{total_functions}")
    print(f"  类型注解覆盖率: {type_coverage:.1f}%")

    # 核心模块分析
    print("\n🎯 核心模块状态:")
    core_modules = {
        "config/": "配置系统",
        "interaction/": "交互管理",
        "core/": "核心处理",
        "services/": "服务层",
        "models/": "模型定义",
    }

    for module_prefix, description in core_modules.items():
        module_files = [
            m for m in analysis["modules"].keys() if m.startswith(module_prefix)
        ]
        if module_files:
            total_funcs = sum(
                len(analysis["modules"][m]["functions"]) for m in module_files
            )
            print(f"  {description}: {len(module_files)}个文件, {total_funcs}个函数")

    # 复杂度分析
    print("\n⚡ 复杂度分析:")
    complex_functions = [
        f
        for f in analysis["functions"].values()
        if isinstance(f["complexity"], int) and f["complexity"] > 50
    ]
    print(f"  高复杂度函数(>50行): {len(complex_functions)}")

    if complex_functions:
        print("  需要重构的函数:")
        for func in complex_functions[:5]:  # 显示前5个
            print(f"    - {func['name']}: {func['complexity']}行")


def check_mypy_errors_detailed():
    """详细检查Mypy错误分布"""
    print("\n🔍 Mypy错误详细分析...")

    try:
        result = subprocess.run(
            ["python", "-m", "mypy", "Day_translation2/", "--show-error-codes"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0:
            print("✅ 无Mypy错误")
            return True

        # 分析错误类型
        error_types = {}
        error_files = {}

        for line in result.stdout.splitlines():
            if "error:" in line:
                # 提取错误类型
                if "[" in line and "]" in line:
                    error_code = line.split("[")[-1].split("]")[0]
                    error_types[error_code] = error_types.get(error_code, 0) + 1

                # 提取文件路径
                if "Day_translation2/" in line:
                    file_path = line.split("Day_translation2/")[1].split(":")[0]
                    error_files[file_path] = error_files.get(file_path, 0) + 1

        total_errors = sum(error_types.values())
        print(f"❌ 发现 {total_errors} 个Mypy错误")

        # 错误类型分布
        print("\n📊 错误类型分布:")
        for error_type, count in sorted(
            error_types.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {error_type}: {count} ({count/total_errors*100:.1f}%)")

        # 错误文件分布
        print("\n📁 错误文件分布:")
        for file_path, count in sorted(
            error_files.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {file_path}: {count} ({count/total_errors*100:.1f}%)")

        return False

    except Exception as e:
        print(f"❌ Mypy分析失败: {e}")
        return False


def check_unnecessary_f_strings():
    """检查并修复不必要的f-string使用"""
    print("\n🔍 检查不必要的f-string...")

    import re

    day_translation_dir = Path("Day_translation2")
    if not day_translation_dir.exists():
        print("❌ Day_translation2目录不存在")
        return False

    # 包括质量检查脚本本身
    all_files = list(day_translation_dir.rglob("*.py"))
    all_files.append(Path("quality_check.py"))  # 检查自身

    issues_found = []
    files_modified = 0

    # 匹配没有插值的f-string
    # 匹配 "..." 或 '...' 但不包含 {} 的情况
    fstring_pattern = re.compile(r'f(["\'])((?:(?!\1)[^\\]|\\.)*)(\1)')

    for py_file in all_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            lines = content.splitlines()
            modified_lines = []
            file_issues = []

            for line_num, line in enumerate(lines, 1):
                modified_line = line

                # 查找所有f-string
                for match in fstring_pattern.finditer(line):
                    quote_char = match.group(1)
                    string_content = match.group(2)

                    # 检查是否包含插值（{} 或 {{ }}）
                    # 排除转义的花括号 {{}}
                    if "{" not in string_content or (
                        "{" in string_content
                        and string_content.count("{") == string_content.count("}")
                        and "{{" in string_content
                    ):
                        # 这是一个不必要的f-string
                        old_fstring = f"f{quote_char}{string_content}{quote_char}"
                        new_string = f"{quote_char}{string_content}{quote_char}"

                        modified_line = modified_line.replace(
                            old_fstring, new_string, 1
                        )

                        issue_info = {
                            "file": py_file,
                            "line": line_num,
                            "old": old_fstring,
                            "new": new_string,
                            "full_line": line.strip(),
                        }
                        file_issues.append(issue_info)
                        issues_found.append(issue_info)

                modified_lines.append(modified_line)

            # 如果有修改，写入文件
            if file_issues:
                modified_content = "\n".join(modified_lines)
                if modified_content != original_content:
                    with open(py_file, "w", encoding="utf-8") as f:
                        f.write(modified_content)
                    files_modified += 1
                    print(
                        f"✅ 修复了 {py_file} 中的 {len(file_issues)} 个不必要的f-string"
                    )

                    # 显示修复详情
                    for issue in file_issues[:3]:  # 只显示前3个
                        print(
                            f"   第{issue['line']}行: {issue['old']} → {issue['new']}"
                        )
                    if len(file_issues) > 3:
                        print(f"   ... 还修复了 {len(file_issues) - 3} 个")

        except Exception as e:
            print(f"⚠️ 处理文件失败 {py_file}: {e}")

    # 总结
    if issues_found:
        print("\n📊 f-string修复统计:")
        print(f"  修复文件数: {files_modified}")
        print(f"  修复问题数: {len(issues_found)}")
        print("  状态: ✅ 已自动修复")
        return True
    else:
        print("✅ 未发现不必要的f-string")
        return True


def main():
    """主函数"""
    print("🚀 Day汉化项目 - 代码质量检查（系统梳理版）")
    print("=" * 60)

    # 检查是否在正确的目录
    if not Path("Day_translation2").exists():
        print("❌ 错误：请在项目根目录运行此脚本")
        return 1

    results = []

    # 0. 系统架构分析（新增）
    architecture_result = analyze_system_architecture()
    results.append(architecture_result)

    # 1. 接口清理检查
    legacy_result = check_legacy_interfaces()
    results.append(legacy_result)

    import_result = check_import_cleanup()
    results.append(import_result)

    # 1.5. f-string优化检查（新增）
    fstring_result = check_unnecessary_f_strings()
    results.append(fstring_result)

    # 2. Black代码格式化检查
    black_result = run_command(
        ["python", "-m", "black", "--check", "--di", "Day_translation2/"],
        "Black代码格式检查",
        continue_on_error=True,
    )
    results.append(black_result)

    # 3. isort导入排序检查
    isort_result = run_command(
        ["python", "-m", "isort", "--check-only", "--di", "Day_translation2/"],
        "isort导入排序检查",
        continue_on_error=True,
    )
    results.append(isort_result)

    # 4. Pylint代码质量检查
    pylint_result = run_command(
        ["python", "-m", "pylint", "Day_translation2/", "--reports=no"],
        "Pylint代码质量检查",
        continue_on_error=True,
    )
    results.append(pylint_result)

    # 5. Mypy类型检查（详细分析）
    mypy_result = check_mypy_errors_detailed()
    results.append(mypy_result)

    # 6-8. 功能测试
    basic_test_result = run_command(
        ["python", "Day_translation2/test_basic.py"],
        "基础功能测试",
        continue_on_error=True,
    )
    results.append(basic_test_result)

    components_test_result = run_command(
        ["python", "Day_translation2/test_components.py"],
        "组件功能测试",
        continue_on_error=True,
    )
    results.append(components_test_result)

    imports_test_result = run_command(
        ["python", "Day_translation2/test_core_imports.py"],
        "核心模块导入测试",
        continue_on_error=True,
    )
    results.append(imports_test_result)

    # 统计结果
    print("\n" + "=" * 70)
    print("📊 代码质量检查结果汇总（系统梳理版）")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    system_checks = [
        "系统架构分析",
    ]

    cleanup_checks = [
        "遗留接口检查",
        "导入清理检查",
        "f-string优化检查",  # 新增
    ]

    quality_checks = [
        "Black代码格式检查",
        "isort导入排序检查",
        "Pylint代码质量检查",
        "Mypy类型检查（详细）",
    ]

    functional_tests = [
        "基础功能测试",
        "组件功能测试",
        "核心模块导入测试",
    ]

    print("\n🏗️ 系统架构分析:")
    for i, check in enumerate(system_checks):
        status = "✅ 通过" if results[i] else "❌ 失败"
        print(f"  {i + 1}. {check}: {status}")

    print("\n🧹 接口清理检查:")
    for i, check in enumerate(cleanup_checks):
        idx = i + len(system_checks)
        status = "✅ 通过" if results[idx] else "❌ 失败"
        print(f"  {idx + 1}. {check}: {status}")

    print("\n🔍 代码质量检查 (Black + isort + Pylint + Mypy):")
    for i, check in enumerate(quality_checks):
        idx = i + len(system_checks) + len(cleanup_checks)
        status = "✅ 通过" if results[idx] else "❌ 失败"
        print(f"  {idx + 1}. {check}: {status}")

    print("\n🧪 功能测试:")
    for i, check in enumerate(functional_tests):
        idx = i + len(system_checks) + len(cleanup_checks) + len(quality_checks)
        status = "✅ 通过" if results[idx] else "❌ 失败"
        print(f"  {idx + 1}. {check}: {status}")

    # 分层统计
    system_passed = sum(results[: len(system_checks)])
    cleanup_passed = sum(
        results[len(system_checks) : len(system_checks) + len(cleanup_checks)]
    )
    quality_passed = sum(
        results[
            len(system_checks)
            + len(cleanup_checks) : len(system_checks)
            + len(cleanup_checks)
            + len(quality_checks)
        ]
    )
    functional_passed = sum(
        results[len(system_checks) + len(cleanup_checks) + len(quality_checks) :]
    )

    print("\n📈 详细统计:")
    print(
        f"  系统架构: {system_passed}/{len(system_checks)} 通过 ({system_passed / len(system_checks) * 100:.1f}%)"
    )
    print(
        f"  接口清理: {cleanup_passed}/{len(cleanup_checks)} 通过 ({cleanup_passed / len(cleanup_checks) * 100:.1f}%)"
    )
    print(
        f"  代码质量: {quality_passed}/{len(quality_checks)} 通过 ({quality_passed / len(quality_checks) * 100:.1f}%)"
    )
    print(
        f"  功能测试: {functional_passed}/{len(functional_tests)} 通过 ({functional_passed / len(functional_tests) * 100:.1f}%)"
    )
    print(f"  总体结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")

    print("\n🔧 系统梳理说明:")
    print("  🏗️ 架构分析: 详细到模块→类→函数→逻辑→返回值")
    print("  🧹 接口清理: 检查遗留接口和兼容代码")
    print("  🎯 f-string优化: 自动修复不必要的f-string使用")  # 新增
    print("  🔍 质量检查: Black + isort + Pylint + Mypy（详细分析）")
    print("  🧪 功能测试: 基础+组件+导入测试")
    print("  ❌ Flake8: 已禁用（避免工具冲突）")

    # 建议下一步行动
    if not results[0]:  # 架构分析失败
        print("\n⚠️ 系统架构分析失败，请检查代码结构")
    elif not results[6]:  # Mypy检查失败
        print("\n🎯 检测到Mypy错误，建议优先处理类型安全问题")
        print(
            "💡 下一步: 运行 `python -m mypy Day_translation2/ --show-error-codes` 查看详细错误"
        )

    if passed == total:
        print("\n🎉 所有检查通过！系统架构清晰，代码质量优秀！")
        return 0
    elif passed >= total * 0.8:
        print("\n✅ 大部分检查通过，系统状态良好")
        return 0
    else:
        print("\n⚠️ 多项检查失败，请优先处理系统架构和类型安全问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
