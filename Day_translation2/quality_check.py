#!/usr/bin/env python3
"""
一键代码质量检查和修复脚本
运行格式化、linting和基础测试
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def run_command(cmd, description) -> Tuple[int, str]:
    """运行命令并显示结果"""
    print(f"\n{'=' * 60}")
    print(f"🔧 {description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            print("✅ 输出:")
            print(result.stdout)

        if result.stderr:
            print("⚠️  警告/错误:")
            print(result.stderr)

        if result.returncode == 0:
            print(f"✅ {description} - 完成")
        else:
            print(f"❌ {description} - 失败 (退出码: {result.returncode})")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 Day翻译项目 - 代码质量检查和修复 (专业AI建议优化版)")
    print("=" * 60)

    # 确保在正确的目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"📁 工作目录: {project_root}")

    success_count = 0
    total_steps = 6

    # 1. Black 格式化
    if run_command("python -m black . --line-length=88", "Black 代码格式化"):
        success_count += 1

    # 2. isort 导入排序
    if run_command("python -m isort . --profile=black", "isort 导入排序"):
        success_count += 1

    # 3. 移除尾随空格
    if run_command("python remove_trailing_whitespace.py", "移除尾随空格"):
        success_count += 1  # 4. Pylint 代码质量检查 (替代Flake8，按专业AI建议)
    # 只检查语法错误和导入问题，忽略其他警告
    pylint_targets = []
    for target in ["core", "utils", "services", "models"]:
        if (project_root / target).exists():
            pylint_targets.append(target + "/")

    if pylint_targets:
        # 只检查致命错误和错误，忽略警告和信息
        pylint_cmd = f"python -m pylint {' '.join(pylint_targets)} --rcfile=.pylintrc --errors-only"
        if run_command(pylint_cmd, "Pylint 代码质量检查"):
            success_count += 1
    else:
        print("⚠️  没有找到核心模块目录，跳过Pylint检查")
        success_count += 1

    # 5. 基础测试
    if run_command("python -m pytest tests/test_basic.py -v", "基础测试"):
        success_count += 1

    # 6. 组件测试
    if run_command("python -m pytest tests/test_integration.py -v", "集成测试"):
        success_count += 1

    # 总结
    print(f"\n{'=' * 60}")
    print(f"📊 质量检查完成: {success_count}/{total_steps} 步骤成功")
    print(f"{'=' * 60}")

    if success_count == total_steps:
        print("🎉 所有检查通过!")
        return 0
    else:
        print(f"⚠️  {total_steps - success_count} 个步骤需要注意")
        return 1


if __name__ == "__main__":
    sys.exit(main())
