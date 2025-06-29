"""
完整流程处理器
处理提取、翻译、导入一体化流程
"""

import logging
from colorama import Fore, Style

from day_translation.utils.interaction import (
    select_mod_path_with_version_detection,
    confirm_action,
    show_success,
    show_error,
    show_info,
    show_warning
)
from day_translation.core.translation_facade import TranslationFacade
from day_translation.utils.path_manager import PathManager
from day_translation.java_translate.java_translator import JavaTranslator

path_manager = PathManager()

def handle_full_pipeline():
    """处理完整流程功能"""
    try:
        # 选择模组目录
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            return

        facade = TranslationFacade(mod_dir)

        # 提取模板并生成CSV
        export_csv = path_manager.get_path(
            path_type="export_csv",
            prompt="请输入导出 CSV 路径（例如：output.csv）: ",
            validator_type="csv",
            default=path_manager.get_remembered_path("export_csv")
        )
        if not export_csv:
            return

        en_keyed_dir = None
        if confirm_action("是否指定英文 Keyed 目录？"):
            en_keyed_dir = path_manager.get_path(
                path_type="en_keyed_dir",
                prompt="请输入英文 Keyed 目录（例如：C:\\Mods\\Keyed）: ",
                validator_type="dir",
                default=path_manager.get_remembered_path("en_keyed_dir")
            )
            if not en_keyed_dir:
                return

        translations = facade.extract_templates_and_generate_csv(export_csv, en_keyed_dir, auto_choose_definjected=True)

        if translations and confirm_action("确认翻译并导入？"):
            # 选择翻译方式
            show_info("=== 选择翻译方式 ===")
            print(f"{Fore.GREEN}1. Python翻译{Style.RESET_ALL} ── 使用Python阿里云翻译")
            print(f"{Fore.GREEN}2. Java翻译{Style.RESET_ALL}  ── 使用Java工具翻译（高性能）")
            translate_choice = input(f"{Fore.CYAN}请选择翻译方式 (1-2): {Style.RESET_ALL}").strip()
            if translate_choice == "1":
                # Python翻译
                output_csv = None
                if confirm_action("指定输出文件？"):
                    output_csv = path_manager.get_path(
                        path_type="output_csv",
                        prompt="请输入翻译后 CSV 路径（例如：translated.csv）: ",
                        validator_type="csv",
                        default=path_manager.get_remembered_path("output_csv")
                    )
                    if not output_csv:
                        return
                facade.machine_translate(export_csv, output_csv)
                final_csv = output_csv or export_csv.replace('.csv', '_translated.csv')
                facade.import_translations_to_templates(final_csv)
            elif translate_choice == "2":
                # Java翻译
                try:
                    translator = JavaTranslator()
                    status = translator.get_status()
                    if not status['java_available'] or not status['jar_exists']:
                        show_error("Java环境或JAR文件未就绪")
                        return
                    output_csv = export_csv.replace('.csv', '_zh.csv')
                    translator.translate_csv_interactive(export_csv, output_csv)
                    facade.import_translations_to_templates(output_csv)
                except Exception as e:
                    show_error(f"Java翻译失败: {str(e)}")
                    logging.error("Java翻译失败: %s", str(e), exc_info=True)
            else:
                show_warning("用户取消翻译")
        else:
            show_warning("用户取消完整流程")
    except Exception as e:
        show_error(f"完整流程失败: {str(e)}")
        logging.error("完整流程失败: %s", str(e), exc_info=True) 