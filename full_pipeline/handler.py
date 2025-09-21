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
from translate import UnifiedTranslator
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
        from extract.workflow import TemplateManager, InteractionManager

        template_manager = TemplateManager()
        interaction_manager = InteractionManager()

        show_info("=== 开始提取模板 ===")
        smart_config = interaction_manager.handle_smart_extraction_workflow(
            mod_dir, skip_output_selection=True
        )
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
            # 使用统一翻译处理器，它会自动处理恢复翻译
            from translate.handler import handle_unified_translate

            output_csv = handle_unified_translate(export_csv_path)

            if output_csv:
                # 翻译完成，进行导入
                facade.import_translations_to_templates(output_csv)
            else:
                # 翻译未完成（用户中断或失败），不进行导入
                show_info("翻译未完成，跳过导入")
        else:
            show_warning("用户取消完整流程")
    except Exception as e:
        show_error(f"完整流程失败: {str(e)}")
        logger.error("完整流程失败: %s", str(e), exc_info=True)
