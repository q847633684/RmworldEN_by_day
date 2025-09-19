"""
完整流程处理器
处理提取、翻译、导入一体化流程
"""

import logging
from utils.logging_config import get_logger, log_error_with_context
from colorama import Fore, Style

from utils.interaction import (
    select_mod_path_with_version_detection,
    confirm_action,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from core.translation_facade import TranslationFacade
from utils.path_manager import PathManager
from java_translate.java_translator_simple import JavaTranslator
from utils.config import get_config
from utils.config import get_language_dir
from utils.config import get_user_config

path_manager = PathManager()


def handle_full_pipeline():
    """处理完整流程功能"""
    logger = get_logger(f"{__name__}.handle_full_pipeline")
    try:
        # 选择模组目录
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            return

        language = get_config().CN_language
        facade = TranslationFacade(mod_dir, language)

        # 直接走“提取翻译”的智能流程，使用与提取模块相同的逻辑
        from extract.template_manager import TemplateManager
        from extract.interaction_manager import InteractionManager

        template_manager = TemplateManager()
        interaction_manager = InteractionManager()

        show_info("=== 开始提取模板 ===")
        smart_config = interaction_manager.handle_smart_extraction_workflow(mod_dir)
        conflict_resolution = smart_config["output_config"]["conflict_resolution"]
        data_source_choice = smart_config["data_sources"]["choice"]
        template_structure = smart_config["template_structure"]
        has_input_keyed = smart_config["data_sources"]["import_status"].get(
            "has_keyed", False
        )
        import_dir = smart_config["data_sources"]["import_status"]["mod_dir"]
        import_language = smart_config["data_sources"]["import_status"]["language"]
        output_dir = smart_config["output_config"]["output_status"]["mod_dir"]
        output_language = smart_config["output_config"]["output_status"]["language"]
        output_csv = get_config().output_csv

        # 执行提取
        translations = template_manager.extract_and_generate_templates(
            import_dir=import_dir,
            import_language=import_language,
            output_dir=output_dir,
            output_language=output_language,
            data_source_choice=data_source_choice,
            template_structure=template_structure,
            has_input_keyed=has_input_keyed,
            output_csv=output_csv,
        )

        # 提取生成的 CSV 路径（与提取流程一致）
        export_csv_path = str(
            get_language_dir(output_dir, output_language) / output_csv
        )

        if translations and confirm_action("是否立即进行机翻并导入？"):
            # 选择翻译方式
            show_info("=== 选择翻译方式 ===")
            print(
                f"{Fore.GREEN}1. Java翻译（推荐）{Style.RESET_ALL} ── 使用Java工具翻译（高性能）"
            )
            print(f"{Fore.CYAN}2. Python翻译{Style.RESET_ALL} ── 使用Python阿里云翻译")
            translate_choice = input(
                f"{Fore.CYAN}请选择翻译方式 (1-2, 回车默认选择1): {Style.RESET_ALL}"
            ).strip()
            if translate_choice == "1" or translate_choice == "":
                # Java翻译
                try:
                    translator = JavaTranslator()
                    status = translator.get_status()
                    if not status["java_available"] or not status["jar_exists"]:
                        show_error("Java环境或JAR文件未就绪")
                        return
                    output_csv = export_csv_path.replace(".csv", "_zh.csv")
                    # 优先使用配置中的密钥，缺失再交互输入
                    cfg = get_user_config() or {}
                    ak = (cfg.get("aliyun_access_key_id") or "").strip()
                    sk = (cfg.get("aliyun_access_key_secret") or "").strip()
                    if ak and sk:
                        success = translator.translate_csv(
                            export_csv_path, output_csv, ak, sk
                        )
                        if not success:
                            show_error("Java翻译失败")
                            return
                    else:
                        # 如果没有配置密钥，提示用户配置
                        show_error("未找到阿里云翻译密钥配置")
                        show_info("请先配置翻译密钥：")
                        show_info(
                            "1. 在配置文件中设置 aliyun_access_key_id 和 aliyun_access_key_secret"
                        )
                        show_info("2. 或使用其他功能进行配置")
                        return
                    facade.import_translations_to_templates(output_csv)
                except Exception as e:
                    show_error(f"Java翻译失败: {str(e)}")
                    logger.error("Java翻译失败: %s", str(e), exc_info=True)
            elif translate_choice == "2":
                # Python翻译
                output_csv = None
                if confirm_action("指定输出文件？"):
                    output_csv = path_manager.get_path(
                        path_type="output_csv",
                        prompt="请输入翻译后 CSV 路径（例如：translated.csv）: ",
                        validator_type="csv",
                        default=path_manager.get_remembered_path("output_csv"),
                    )
                    if not output_csv:
                        return
                facade.machine_translate(export_csv_path, output_csv)
                final_csv = output_csv or export_csv_path.replace(
                    ".csv", "_translated.csv"
                )
                facade.import_translations_to_templates(final_csv)
            else:
                show_warning("用户取消翻译")
        else:
            show_warning("用户取消完整流程")
    except Exception as e:
        show_error(f"完整流程失败: {str(e)}")
        logger.error("完整流程失败: %s", str(e), exc_info=True)
