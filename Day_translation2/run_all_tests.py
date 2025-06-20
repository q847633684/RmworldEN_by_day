#!/usr/bin/env python3
"""
Day Translation 2 - 一键测试脚本

自动执行所有测试，无需用户交互
"""

import os
import subprocess
import sys
from pathlib import Path

# 设置UTF-8编码
if sys.platform.startswith("win"):
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def run_command(command, description):
    """执行命令并显示结果"""
    print(f"\n🔄 {description}")
    print("-" * 50)

    try:
        # 设置环境变量以支持UTF-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            env=env,
            encoding="utf-8",
        )

        if result.returncode == 0:
            print("✅ 成功")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print("❌ 失败")
            if result.stderr.strip():
                print(f"错误: {result.stderr}")

        return result.returncode == 0

    except Exception as e:
        print(f"💥 异常: {e}")
        return False


def main():
    """主函数"""
    print("🎯 Day Translation 2 - 一键测试套件")
    print("=" * 50)

    tests = [
        ("python test_core_imports.py", "核心模块导入测试"),
        ("python test_basic.py", "基础功能测试"),
        ("python test_components.py", "组件功能测试"),
    ]

    results = []
    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))

    # 汇总结果
    print("\n📊 测试汇总")
    print("=" * 50)

    success_count = 0
    for description, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{description}: {status}")
        if success:
            success_count += 1

    print(f"\n总结: {success_count}/{len(results)} 测试通过")

    if success_count == len(results):
        print("🎉 所有测试都通过了！")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
