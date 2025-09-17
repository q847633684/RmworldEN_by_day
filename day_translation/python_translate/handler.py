"""
Python机翻处理器
处理Python机翻的交互流程
"""

import logging
from colorama import Fore, Style

from day_translation.utils.interaction import (
    select_csv_path_with_history,
    confirm_action,
    auto_generate_output_path,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from day_translation.core.translation_facade import TranslationFacade
from day_translation.utils.path_manager import PathManager


def handle_python_translate():
    """处理Python机翻功能"""
    try:
        # 获取输入CSV文件
        csv_path = select_csv_path_with_history()
        if not csv_path:
            return

        # 询问是否指定输出文件
        output_csv = None
        if confirm_action("指定输出文件？"):
            # 这里可以扩展为使用path_manager.get_path
            output_csv = input(
                f"{Fore.CYAN}请输入输出 CSV 路径: {Style.RESET_ALL}"
            ).strip()
            if not output_csv:
                show_warning("未指定输出文件，将使用默认路径")
                output_csv = None

        # 创建翻译门面实例（需要模组目录，这里使用临时目录）
        import tempfile

        temp_dir = tempfile.mkdtemp()
        facade = TranslationFacade(temp_dir)

        # 执行翻译
        show_info("=== 开始Python翻译 ===")
        facade.machine_translate(csv_path, output_csv)
        # 将输出CSV加入“导入翻译”的历史
        try:
            if output_csv is None:
                # 如果未手动指定，machine_translate会自动生成 *_translated.csv
                from pathlib import Path as _P

                p = _P(csv_path)
                output_csv_path = str(p.parent / f"{p.stem}_translated.csv")
            else:
                output_csv_path = output_csv
            PathManager().remember_path("import_csv", output_csv_path)
        except Exception:
            pass

        show_success("Python翻译完成！")

    except Exception as e:
        show_error(f"Python翻译失败: {str(e)}")
        logging.error("Python翻译失败: %s", str(e), exc_info=True)
