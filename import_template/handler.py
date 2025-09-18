"""
导入模板处理器
处理导入CSV到翻译模板的交互流程
"""

import logging
from colorama import Fore, Style

from utils.interaction import (
    select_csv_path_with_history,
    confirm_action,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from core.translation_facade import TranslationFacade
from utils.path_manager import PathManager
from utils.config import get_config

path_manager = PathManager()


def handle_import_template():
    """处理导入模板功能"""
    try:
        # 获取输入CSV文件
        csv_path = select_csv_path_with_history()
        if not csv_path:
            return

        # 选择模组目录
        selected_path = path_manager.get_path(
            path_type="mod_dir",
            prompt="请输入编号或模组目录路径（支持历史编号或直接输入路径）: ",
            validator_type="mod",
            required=True,
        )
        if not selected_path:
            return

        mod_dir = path_manager.detect_version_and_choose(selected_path)
        if not mod_dir:
            return

        # 创建翻译门面实例（使用配置中的目标语言）
        language = get_config().CN_language
        facade = TranslationFacade(mod_dir, language)

        # 确认导入
        if confirm_action("确认导入翻译到模板？"):
            show_info("=== 开始导入 ===")
            try:
                facade.import_translations_to_templates(csv_path)
                show_success("导入完成！")
            except Exception as e:
                show_error(f"导入失败: {str(e)}")
                logging.error("导入失败: %s", str(e), exc_info=True)
        else:
            show_warning("用户取消导入")
    except Exception as e:
        show_error(f"导入模板失败: {str(e)}")
        logging.error("导入模板失败: %s", str(e), exc_info=True)
