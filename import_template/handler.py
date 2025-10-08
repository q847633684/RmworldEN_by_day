"""
导入模板处理器
处理导入CSV到翻译模板的交互流程
"""

import csv
from utils.logging_config import get_logger

from utils.interaction import (
    select_csv_path_with_history,
    confirm_action,
)
from utils.ui_style import ui
from user_config.path_manager import PathManager
from user_config import UserConfigManager
from .importers import import_translations

path_manager = PathManager()


def handle_import_template(
    csv_path: str = None,
    mod_dir: str = None,
):
    """处理导入模板功能

    Args:
        csv_path: CSV文件路径，如果提供则跳过路径选择
        mod_dir: 模组目录路径，如果提供则跳过目录选择
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

        # 获取模组目录
        if not mod_dir:
            selected_path = path_manager.get_path(
                path_type="mod_dir",
                prompt="请输入编号或模组目录路径（支持历史编号或直接输入路径）: ",
                validator_type="mod",
                required=True,
            )
            if not selected_path:
                return

            result = path_manager.detect_version_and_choose(selected_path)
            if not result:
                return

            # 解包结果：mod_dir, project_type
            if isinstance(result, tuple):
                mod_dir, _ = result  # project_type 暂时不使用
            else:
                # 兼容旧格式
                mod_dir = result
        else:
            ui.print_info(f"使用提供的模组目录: {mod_dir}")

        # 获取配置
        config = UserConfigManager.get_instance()
        language = config.language_config.get_value("cn_language", "ChineseSimplified")

        # 确认导入
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
