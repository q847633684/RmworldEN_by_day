#!/usr/bin/env python3
"""
词典翻译工具
独立工具，用于处理翻译API无法处理的敏感内容
支持成人内容和游戏内容两种词典类型
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from translate.dictionary.dictionary_translator import (
    DictionaryTranslator,
    translate_content_in_csv,
)
from utils.ui_style import ui


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="词典翻译工具")
    parser.add_argument("input_csv", nargs="?", help="输入CSV文件路径")
    parser.add_argument("-o", "--output", help="输出CSV文件路径（默认自动生成）")
    parser.add_argument(
        "-t",
        "--type",
        choices=["adult", "game"],
        default="adult",
        help="词典类型：adult（成人内容）或 game（游戏内容），默认为 adult",
    )
    parser.add_argument(
        "--add",
        nargs=2,
        metavar=("ENGLISH", "CHINESE"),
        help="添加自定义翻译：--add 'cum' '精液'",
    )
    parser.add_argument("--stats", action="store_true", help="显示词典统计信息")
    parser.add_argument("--reload", action="store_true", help="重新加载词典")

    args = parser.parse_args()

    # 创建翻译器
    translator = DictionaryTranslator(args.type)

    # 处理参数
    if args.stats:
        stats = translator.get_dictionary_stats()
        ui.print_info(f"📊 {args.type}词典统计信息:")
        ui.print_info(f"  总条目数: {stats['total_entries']}")
        ui.print_info(f"  词典路径: {stats['dictionary_path']}")
        ui.print_info(f"  词典存在: {'是' if stats['dictionary_exists'] else '否'}")
        return

    if args.reload:
        if translator.reload_dictionary():
            ui.print_success(f"✅ {args.type}词典重新加载成功")
        else:
            ui.print_error(f"❌ {args.type}词典重新加载失败")
        return

    if args.add:
        english, chinese = args.add
        if translator.add_custom_translation(english, chinese):
            ui.print_success(f"✅ 添加{args.type}自定义翻译: {english} -> {chinese}")
        else:
            ui.print_error(f"❌ 添加{args.type}自定义翻译失败")
        return

    # 检查是否提供了输入文件
    if not args.input_csv:
        ui.print_error("❌ 请提供输入CSV文件路径")
        parser.print_help()
        return

    # 处理翻译
    input_csv = args.input_csv
    output_csv = args.output

    if not Path(input_csv).exists():
        ui.print_error(f"❌ 输入文件不存在: {input_csv}")
        return

    if not output_csv:
        input_path = Path(input_csv)
        output_csv = str(
            input_path.parent / f"{input_path.stem}_{args.type}_translated.csv"
        )

    ui.print_info(f"🔍 开始处理{args.type}内容翻译...")
    ui.print_info(f"   输入文件: {input_csv}")
    ui.print_info(f"   输出文件: {output_csv}")

    success = translate_content_in_csv(input_csv, output_csv, args.type)

    if success:
        ui.print_success(f"✅ {args.type}内容翻译完成: {output_csv}")
    else:
        ui.print_error(f"❌ {args.type}内容翻译失败")


if __name__ == "__main__":
    main()
