"""
完整流程处理器
处理提取、翻译、导入一体化流程（单次与批量）
"""

import csv
from pathlib import Path

from utils.constants import TOTAL_CSV_NAME
from utils.logging_config import get_logger
from utils.interaction import confirm_action
from utils.ui_style import ui
from extract.workflow.handler import handle_extract
from extract.batch_extract import handle_batch_vanilla_extract
from translate.handler import handle_unified_translate
from import_template.handler import handle_import_template
from batch.handler import aggregate_chinese_translations_to_root, batch_import_from_csv


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
            # 使用配置系统的功能生成输出路径
            from translate.unified_translator import UnifiedTranslator

            translator = UnifiedTranslator()
            output_csv = translator._generate_output_path(csv_path)
            translated_csv = handle_unified_translate(csv_path, output_csv)

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


def handle_batch_full_pipeline():
    """批量提取完整流程：Vanilla 前缀模组 提取→翻译→导入→汇总到根目录（根目录现有语言文件将被删除）。"""
    ui.print_header("批量提取完整流程", ui.Icons.BATCH)
    ui.print_info(
        "将执行：1. 批量提取 2. 翻译总 CSV 3. 批量导入 4. 汇总到根目录（删除根目录现有 Keyed/DefInjected）"
    )

    output_base = handle_batch_vanilla_extract()
    if not output_base:
        ui.print_warning("批量提取未完成或失败，已取消完整流程")
        return

    output_base_path = Path(output_base)
    total_csv = output_base_path / TOTAL_CSV_NAME
    if not total_csv.is_file():
        ui.print_error(f"未找到总 CSV：{total_csv}")
        return

    if not confirm_action("是否立即进行机翻？"):
        ui.print_info(
            "已跳过翻译，可稍后手动翻译总 CSV 并运行「批量导入」「汇总到根目录」"
        )
        return

    translated = handle_unified_translate(
        csv_path=str(total_csv), ask_import_after=False
    )
    if not translated or not Path(translated).is_file():
        ui.print_warning("翻译未完成，已取消后续步骤")
        return

    if not confirm_action("是否立即批量导入翻译？"):
        ui.print_info("已跳过导入，可稍后手动运行「批量导入」")
        return

    from user_config import UserConfigManager

    config = UserConfigManager.get_instance()
    language = config.language_config.get_default_cn_language()
    try:
        success, total, failed = batch_import_from_csv(
            output_base_path, str(translated), language=language
        )
    except (OSError, IOError, csv.Error) as e:
        ui.print_error(f"读取翻译后 CSV 失败: {e}")
        return
    if total == 0:
        ui.print_error("总 CSV 需包含 mod 列")
        return
    for x in failed:
        ui.print_warning(f"导入失败: {x}")
    ui.print_success(f"批量导入完成：成功 {success}/{total}")

    ui.print_info("正在汇总到根目录（将删除根目录现有 Keyed/DefInjected）...")
    k_count, d_count = aggregate_chinese_translations_to_root(
        output_base, delete_existing=True
    )
    ui.print_success(f"汇总完成：Keyed {k_count} 个文件，DefInjected {d_count} 个文件")
    ui.print_success("批量提取完整流程完成！")
