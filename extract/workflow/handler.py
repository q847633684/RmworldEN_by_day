"""
RimWorld 翻译提取主处理器

负责协调整个翻译提取流程，包括：
- 用户交互和配置选择
- 智能工作流程管理
- 冲突处理和模式选择
- 错误处理和日志记录
"""

from pathlib import Path
from utils.config import (
    get_config,
    get_language_subdir,
    get_language_dir,
)
from utils.logging_config import get_logger, log_user_action, log_error_with_context
from utils.interaction import (
    select_mod_path_with_version_detection,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from utils.path_manager import PathManager
from utils.config import ConfigError
from .manager import TemplateManager
from .interaction import InteractionManager


def handle_extract():
    """处理提取模板功能"""
    logger = get_logger(f"{__name__}.handle_extract")
    config = get_config()

    print(f"日志文件路径：{config.log_file}")
    if config.debug_mode:
        print("调试模式已开启，详细日志见日志文件。")

    logger.info("开始处理提取模板功能")

    try:
        # 选择模组目录
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            logger.info("用户取消了模组目录选择")
            return

        # 记录用户操作
        log_user_action("选择模组目录", mod_dir=mod_dir)

        # 创建模板管理器和交互管理器
        template_manager = TemplateManager()
        interaction_manager = InteractionManager()

        show_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程
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

            show_info(
                f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}"
            )

            output_csv = config.output_csv
            output_path = Path(output_dir)

            # 根据冲突处理方式执行相应操作
            if conflict_resolution == "merge":
                # 合并模式
                translations = template_manager.merge_mode(
                    import_dir=import_dir,
                    import_language=import_language,
                    output_dir=output_dir,
                    output_language=output_language,
                    data_source_choice=data_source_choice,
                    has_input_keyed=has_input_keyed,
                    output_csv=output_csv,
                )
            else:  # 包括 'rebuild' 和 'new'
                # 步骤 1: 根据模式处理文件系统
                if conflict_resolution == "rebuild":
                    # 重建：清空输出目录
                    language_dir = get_language_dir(
                        base_dir=output_path,
                        language=output_language,
                    )
                    if language_dir.exists():
                        try:
                            import shutil

                            for item in language_dir.iterdir():
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            show_info(f"🗑️ 已清空输出目录：{language_dir}")
                        except PermissionError as e:
                            show_warning(
                                f"⚠️ 无法删除某些文件（可能是系统文件），跳过：{e}"
                            )
                    else:
                        show_info(f"📁 输出目录不存在，将创建：{language_dir}")

                # 步骤 2: 统一执行提取
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

                # 步骤 3: 根据模式显示不同的成功消息
                if conflict_resolution == "rebuild":
                    show_success(f"重建完成！共提取 {len(translations)} 条翻译")
                else:  # 'new'
                    show_success(f"智能提取完成！共提取 {len(translations)} 条翻译")

            show_info(f"输出目录：{output_dir}")

        except (OSError, IOError, ValueError, RuntimeError) as e:
            show_error(f"智能提取失败: {str(e)}")
            log_error_with_context(e, "智能提取失败", mod_dir=mod_dir)
            if config.debug_mode:
                import traceback

                traceback.print_exc()
        except ConfigError as e:
            show_error(
                f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
            )
            log_error_with_context(e, "配置错误", mod_dir=mod_dir)
            if config.debug_mode:
                import traceback

                traceback.print_exc()

    except (OSError, IOError, ValueError, ImportError, AttributeError) as e:
        show_error(f"提取模板功能失败: {str(e)}")
        log_error_with_context(e, "提取模板功能失败")
        if config.debug_mode:
            import traceback

            traceback.print_exc()
    except ConfigError as e:
        show_error(
            f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
        )
        log_error_with_context(e, "配置错误")
        if config.debug_mode:
            import traceback

            traceback.print_exc()
