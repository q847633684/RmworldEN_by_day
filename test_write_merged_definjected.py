#!/usr/bin/env python3
"""
测试 write_merged_definjected_translations 函数
"""

import os
import tempfile
import shutil
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# 导入待测试的函数
from day_translation.extract.exporters import write_merged_definjected_translations


def test_write_merged_definjected():
    """测试合并翻译写入功能"""

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    export_dir = Path(temp_dir) / "output"

    try:
        print(f"测试目录: {temp_dir}")

        # 测试数据：六元组 (key, test, tag, rel_path, en_test, history)
        test_data = [
            # ThingDefs/Weapons.xml 文件中的翻译
            (
                "Gun_Pistol.label",
                "手枪",
                "Gun_Pistol",
                "ThingDefs/Weapons.xml",
                "Pistol",
                "",
            ),  # 无历史
            (
                "Gun_Pistol.description",
                "一把简单的手枪",
                "Gun_Pistol",
                "ThingDefs/Weapons.xml",
                "A simple pistol",
                "老式手枪",
            ),  # 有历史
            (
                "Gun_Rifle.label",
                "步枪",
                "Gun_Rifle",
                "ThingDefs/Weapons.xml",
                "Rifle",
                "",
            ),  # 无历史
            # ThingDefs/Buildings.xml 文件中的翻译
            (
                "Wall.label",
                "墙壁",
                "Wall",
                "ThingDefs/Buildings.xml",
                "Wall",
                "",
            ),  # 无历史
            (
                "Door.label",
                "门",
                "Door",
                "ThingDefs/Buildings.xml",
                "Door",
                "木门",
            ),  # 有历史
        ]

        print("=== 第一次写入测试（创建新文件） ===")
        write_merged_definjected_translations(
            merged=test_data, export_dir=str(export_dir), def_injected_dir="DefInjected"
        )

        # 检查生成的文件
        weapons_file = export_dir / "DefInjected" / "ThingDefs" / "Weapons.xml"
        buildings_file = export_dir / "DefInjected" / "ThingDefs" / "Buildings.xml"

        print(f"\n生成的文件:")
        print(f"- {weapons_file}")
        print(f"- {buildings_file}")

        # 读取并显示文件内容
        if weapons_file.exists():
            print(f"\n=== {weapons_file.name} 内容 ===")
            with open(weapons_file, "r", encoding="utf-8") as f:
                print(f.read())

        if buildings_file.exists():
            print(f"\n=== {buildings_file.name} 内容 ===")
            with open(buildings_file, "r", encoding="utf-8") as f:
                print(f.read())

        print("\n=== 第二次写入测试（更新现有文件） ===")
        # 修改一些翻译内容，测试更新功能
        updated_data = [
            (
                "Gun_Pistol.label",
                "新式手枪",
                "Gun_Pistol",
                "ThingDefs/Weapons.xml",
                "Pistol",
                "",
            ),
            (
                "Gun_Pistol.description",
                "一把改进的手枪",
                "Gun_Pistol",
                "ThingDefs/Weapons.xml",
                "An improved pistol",
                "",
            ),
            (
                "Gun_Shotgun.label",
                "霰弹枪",
                "Gun_Shotgun",
                "ThingDefs/Weapons.xml",
                "Shotgun",
                "",
            ),  # 新添加的
        ]

        write_merged_definjected_translations(
            merged=updated_data,
            export_dir=str(export_dir),
            def_injected_dir="DefInjected",
        )

        # 再次读取并显示更新后的内容
        if weapons_file.exists():
            print(f"\n=== 更新后的 {weapons_file.name} 内容 ===")
            with open(weapons_file, "r", encoding="utf-8") as f:
                print(f.read())

        print("\n=== 测试完成 ===")
        print("请检查:")
        print("1. 文件是否正确创建")
        print("2. XML结构是否正确")
        print("3. 翻译内容是否正确")
        print("4. 注释是否正确添加")
        print("5. 更新时是否保留了原有内容并添加了历史记录")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 清理临时目录
        print(f"\n清理临时目录: {temp_dir}")
        # shutil.rmtree(temp_dir)  # 注释掉以便查看结果文件


if __name__ == "__main__":
    test_write_merged_definjected()
