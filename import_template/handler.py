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
    safe_input,
)
from utils.ui_style import ui
from user_config import UserConfigManager
from .importers import import_translations, migrate_translations_to_new


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


def handle_migrate_translations():
    """迁移旧翻译到新模板：扫描旧翻译目录，用旧翻译覆盖或填充新目录（默认覆盖新模板中已有内容）。"""
    logger = get_logger(f"{__name__}.handle_migrate_translations")
    try:
        config = UserConfigManager.get_instance()
        language = config.language_config.get_value("cn_language", "ChineseSimplified")
        ui.print_info("将从旧翻译目录收集所有 Keyed/DefInjected 的 key→译文，合并后按 key 一一对应写入新目录。")
        ui.print_info("支持多个旧目录：用分号 ; 分隔，将合并收集（同 key 后者覆盖），无需移动文件。")
        ui.print_info("旧/新目录可为模组根（含 Languages）、语言目录、或直接 Keyed/DefInjected 文件夹。")

        old_input = safe_input(ui.get_input_prompt("请输入旧翻译根目录（多个用 ; 分隔）", options="q 退出"))
        if not old_input or old_input.strip().lower() == "q":
            return
        old_dirs = [str(Path(p.strip()).resolve()) for p in old_input.split(";") if p.strip()]
        for d in old_dirs:
            if not Path(d).is_dir():
                ui.print_error(f"目录不存在: {d}")
                return

        new_dir = safe_input(ui.get_input_prompt("请输入新翻译根目录", options="q 退出"))
        if not new_dir or new_dir.strip().lower() == "q":
            return
        new_dir = str(Path(new_dir).resolve())
        if not Path(new_dir).is_dir():
            ui.print_error(f"目录不存在: {new_dir}")
            return

        # 默认用旧翻译覆盖新模板中已有内容（新模板里常有英文占位，需覆盖为旧中文）
        # 选 y = 仅填充空项不覆盖；直接回车或 n = 用旧翻译覆盖（推荐）
        only_fill_empty = confirm_action(
            "是否仅填充空项、不覆盖？选 y 仅填充空项；直接回车则用旧翻译覆盖（推荐）"
        )

        if not confirm_action("确认开始迁移？"):
            ui.print_warning("已取消迁移")
            return

        ui.print_info("正在扫描并合并旧翻译...")
        updated = migrate_translations_to_new(
            old_base_dirs=old_dirs,
            new_base_dir=new_dir,
            language=language,
            only_fill_empty=only_fill_empty,
        )
        ui.print_success(f"迁移完成，共更新 {updated} 个文件。")
    except (OSError, ValueError, RuntimeError, ImportError) as e:
        ui.print_error(f"迁移失败: {str(e)}")
        logger.error("迁移失败: %s", str(e), exc_info=True)
