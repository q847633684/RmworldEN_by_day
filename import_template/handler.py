"""
导入模板处理器
处理导入CSV到翻译模板的交互流程
"""

import csv
from pathlib import Path
from utils.logging_config import get_logger

from utils.interaction import (
    select_csv_path_with_history,
    confirm_action,
)
from utils.ui_style import ui
from user_config import UserConfigManager
from .importers import import_translations


def handle_import_template(
    csv_path: str = None,
    mod_dir: str = None,
):
    """处理导入模板功能

    不依赖版本号与 About 识别：以所选 CSV 所在目录为导入目标，
    直接使用该目录下的 Languages/<语言> 作为模板目录（与多子目录各自生成 CSV 的提取结果一致）。

    Args:
        csv_path: CSV文件路径，如果提供则跳过路径选择
        mod_dir: 模组/导入目录路径，若提供则直接使用；否则由 CSV 所在目录推导
    """
    logger = get_logger(f"{__name__}.handle_import_template")

    try:
        # 获取CSV文件路径
        if not csv_path:
            csv_path = select_csv_path_with_history()
            if not csv_path:
                return
        else:
            ui.print_info(f"使用提供的CSV路径: {csv_path}")

        # 导入目标目录：未提供时取 CSV 所在目录（该目录下应有 Languages/<语言>）
        if not mod_dir:
            mod_dir = str(Path(csv_path).resolve().parent)
            ui.print_info(f"导入目标目录（由 CSV 所在目录确定）: {mod_dir}")
        else:
            ui.print_info(f"使用提供的导入目录: {mod_dir}")

        config = UserConfigManager.get_instance()
        language = config.language_config.get_value("cn_language", "ChineseSimplified")

        if confirm_action("确认导入翻译到模板？"):
            ui.print_info("=== 开始导入 ===")
            try:
                success = import_translations(
                    csv_path=csv_path,
                    mod_dir=mod_dir,
                    merge=True,
                    auto_create_templates=True,
                    language=language,
                )
                if success:
                    ui.print_success("导入完成！")
                else:
                    ui.print_error("导入失败！")
            except (OSError, ValueError, RuntimeError, csv.Error) as e:
                ui.print_error(f"导入失败: {str(e)}")
                logger.error("导入失败: %s", str(e), exc_info=True)
        else:
            ui.print_warning("用户取消导入")

    except (OSError, ValueError, RuntimeError, ImportError) as e:
        ui.print_error(f"导入模板失败: {str(e)}")
        logger.error("导入模板失败: %s", str(e), exc_info=True)
