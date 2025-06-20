#!/usr/bin/env python3
"""
Day汉化项目 - 代码质量检查脚本

自动运行所有代码质量检查工具，包括格式化、静态检查、测试等。
"""

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
            command, capture_output=True, text=True, cwd=current_dir, check=False,
            encoding='utf-8', errors='replace'
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


def main():
    """主函数"""
    print("🚀 Day汉化项目 - 代码质量检查（增强版）")
    print("=" * 60)

    # 检查是否在正确的目录
    if not Path("Day_translation2").exists():
        print("❌ 错误：请在项目根目录运行此脚本")
        return 1

    results = []

    # 1. Black代码格式化检查（不修改文件，只检查）
    black_result = run_command(
        ["python", "-m", "black", "--check", "--diff", "Day_translation2/"],
        "Black代码格式检查",
        continue_on_error=True,
    )
    results.append(black_result)

    # 2. isort导入排序检查
    isort_result = run_command(
        ["python", "-m", "isort", "--check-only", "--diff", "Day_translation2/"],
        "isort导入排序检查",
        continue_on_error=True,
    )
    results.append(isort_result)

    # 3. Flake8语法和风格检查
    flake8_result = run_command(
        ["python", "-m", "flake8", "Day_translation2/"],
        "Flake8语法和风格检查",
        continue_on_error=True,
    )
    results.append(flake8_result)

    # 4. Pylint代码质量检查
    pylint_result = run_command(
        ["python", "-m", "pylint", "Day_translation2/", "--reports=no"],
        "Pylint代码质量检查",
        continue_on_error=True,
    )
    results.append(pylint_result)

    # 5. Mypy类型检查
    mypy_result = run_command(
        ["python", "-m", "mypy", "Day_translation2/"],
        "Mypy类型检查",
        continue_on_error=True,
    )
    results.append(mypy_result)

    # 6. 基础测试
    basic_test_result = run_command(
        ["python", "Day_translation2/test_basic.py"], "基础功能测试", continue_on_error=True
    )
    results.append(basic_test_result)

    # 7. 组件测试
    components_test_result = run_command(
        ["python", "Day_translation2/test_components.py"], "组件功能测试", continue_on_error=True
    )
    results.append(components_test_result)

    # 8. 核心导入测试
    imports_test_result = run_command(
        ["python", "Day_translation2/test_core_imports.py"], "核心模块导入测试", continue_on_error=True
    )
    results.append(imports_test_result)

    # 统计结果
    print("\n" + "=" * 70)
    print("📊 代码质量检查结果汇总（增强版）")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    quality_checks = [
        "Black代码格式检查",
        "isort导入排序检查",
        "Flake8语法和风格检查",
        "Pylint代码质量检查",
        "Mypy类型检查",
    ]

    functional_tests = [
        "基础功能测试",
        "组件功能测试",
        "核心模块导入测试",
    ]

    all_checks = quality_checks + functional_tests

    print("\n🔍 代码质量检查:")
    for i, check in enumerate(quality_checks):
        status = "✅ 通过" if results[i] else "❌ 失败"
        print(f"  {i + 1}. {check}: {status}")

    print("\n🧪 功能测试:")
    for i, check in enumerate(functional_tests):
        idx = i + len(quality_checks)
        status = "✅ 通过" if results[idx] else "❌ 失败"
        print(f"  {idx + 1}. {check}: {status}")

    quality_passed = sum(results[: len(quality_checks)])
    functional_passed = sum(results[len(quality_checks) :])

    print("\n📈 详细统计:")
    print(
        f"  代码质量: {quality_passed}/{len(quality_checks)} 通过 ({quality_passed / len(quality_checks) * 100:.1f}%)"
    )
    print(
        f"  功能测试: {functional_passed}/{len(functional_tests)} 通过 ({functional_passed / len(functional_tests) * 100:.1f}%)"
    )
    print(f"  总体结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")

    if passed == total:
        print("\n🎉 所有检查通过！代码质量优秀！")
        return 0
    elif passed >= total * 0.8:
        print("\n✅ 大部分检查通过，代码质量良好")
        return 0
    else:
        print("\n⚠️ 多项检查失败，请查看上述详细信息并修复问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
