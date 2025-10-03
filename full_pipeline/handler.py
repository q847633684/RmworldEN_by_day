"""
完整流程处理器
处理提取、翻译、导入一体化流程
"""

from utils.logging_config import get_logger
from utils.interaction import confirm_action
from utils.ui_style import ui
from user_config.path_manager import PathManager
from extract.workflow.handler import handle_extract
from translate.handler import handle_unified_translate
from import_template.handler import handle_import_template

path_manager = PathManager()


def handle_full_pipeline():
    """处理完整流程功能"""
    logger = get_logger(f"{__name__}.handle_full_pipeline")

    try:
        ui.print_info("=== 开始完整流程 ===")

        # 第一步：执行提取流程
        ui.print_info("步骤 1/3: 提取翻译模板...")
        result = handle_extract()

        if not result:
            ui.print_error("提取失败，无法继续完整流程")
            return

        # 解包结果：csv_path, mod_dir
        csv_path, mod_dir = result

        if confirm_action("是否立即进行机翻并导入？"):
            # 第二步：执行翻译
            ui.print_info("步骤 2/3: 执行机器翻译...")
            translated_csv = handle_unified_translate(csv_path)

            if translated_csv:
                # 第三步：执行导入
                ui.print_info("步骤 3/3: 导入翻译结果...")
                handle_import_template(translated_csv, mod_dir)
                ui.print_success("完整流程完成！")
            else:
                ui.print_warning("翻译未完成，跳过导入")
        else:
            ui.print_info("用户取消完整流程")

    except (
        OSError,
        IOError,
        ValueError,
        RuntimeError,
        ImportError,
        AttributeError,
    ) as e:
        ui.print_error(f"完整流程失败: {str(e)}")
        logger.error("完整流程失败: %s", str(e), exc_info=True)
