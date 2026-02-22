"""
修补翻译处理器
处理用户输入文件夹、调用 scan_and_repair_folder 的交互流程
"""

import os
from utils.constants import PATH_HISTORY_REPAIR_FOLDER
from utils.logging_config import get_logger
from utils.interaction import safe_input
from utils.ui_style import ui
from user_config import UserConfigManager
from .repair import scan_and_repair_folder

logger = get_logger(__name__)


def handle_repair_translation() -> None:
    """
    修补翻译：扫描用户指定的文件夹，找出 Google 翻译错误，用英文源重新翻译并替换。
    """
    config = UserConfigManager.get_instance()
    ui.print_header("修补翻译", ui.Icons.TRANSLATE)
    ui.print_info("将扫描指定文件夹中的翻译 XML，检测 Google 错误（如 Error 500）并用英文源重新翻译。")
    ui.print_info("支持 DefInjected 中带 <!--EN: xxx--> 注释的条目。")

    history = config.path_manager.get_history_list(PATH_HISTORY_REPAIR_FOLDER)
    if history:
        ui.print_section_header("历史记录", ui.Icons.HISTORY)
        for i, p in enumerate(history[:8], 1):
            ui.print_menu_item(str(i), os.path.basename(p), p, ui.Icons.FOLDER)
        ui.print_menu_item("0", "输入新路径", "直接输入文件夹路径", ui.Icons.FOLDER)

    prompt = (
        ui.get_input_prompt("选择或输入文件夹路径", options=f"0-{len(history)}, q 退出")
        if history
        else ui.get_input_prompt("请输入翻译目录路径（含 Keyed/DefInjected）", options="q 退出")
    )
    choice = safe_input(prompt)
    if not choice or choice.lower() == "q":
        ui.print_warning("已取消")
        return

    folder: str = ""
    if history and choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(history):
            folder = history[idx - 1]
        elif idx == 0:
            folder = safe_input(ui.get_input_prompt("请输入文件夹路径")) or ""
    else:
        folder = choice.strip()

    if not folder:
        ui.print_error("路径不能为空")
        return
    if not os.path.isdir(folder):
        ui.print_error(f"目录不存在: {folder}")
        return

    config.path_manager.remember_path(PATH_HISTORY_REPAIR_FOLDER, folder)
    ui.print_info(f"扫描目录: {folder}")
    try:
        total = scan_and_repair_folder(folder)
        ui.print_success(f"修补完成，共修复 {total} 条异常翻译")
    except Exception as e:
        ui.print_error(f"修补失败: {str(e)}")
        logger.exception("repair_translation failed")
