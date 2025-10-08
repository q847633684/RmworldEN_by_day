"""
RimWorld 翻译提取主处理器

负责协调整个翻译提取流程，包括：
- 用户交互和配置选择
- 智能工作流程管理
- 冲突处理和模式选择
- 错误处理和日志记录
"""

from pathlib import Path
from typing import Optional
from user_config import UserConfigManager
from utils.logging_config import get_logger, log_user_action, log_error_with_context
from utils.interaction import (
    select_mod_path_with_version_detection,
)
from utils.ui_style import ui
from .manager import TemplateManager
from .interaction import InteractionManager


def handle_extract() -> Optional[tuple]:
    """处理提取模板功能

    Returns:
        Optional[tuple]: (csv_path, mod_dir) 元组，如果失败则返回None
    """
    logger = get_logger(f"{__name__}.handle_extract")
    config = UserConfigManager()

    print(f"日志文件路径：{config.system_config.get_value('log_file')}")
    if config.system_config.get_value("debug_mode"):
        print("调试模式已开启，详细日志见日志文件。")

    logger.info("开始处理提取模板功能")

    try:
        # 选择模组目录
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            logger.info("用户取消了模组目录选择")
            return None

        # 记录用户操作
        log_user_action("选择模组目录", mod_dir=mod_dir)

        # 创建模板管理器和交互管理器
        template_manager = TemplateManager()
        interaction_manager = InteractionManager()

        ui.print_info("=== 开始智能提取模板 ===")
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

            ui.print_info(
                f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}"
            )

            output_csv = config.language_config.get_value(
                "output_csv", "translations.csv"
            )
            output_path = Path(output_dir)

            # 根据冲突处理方式执行相应操作
            if conflict_resolution == "merge":
                ui.print_info("合并模式")
                # 合并模式
                translations, csv_path = template_manager.merge_mode(
                    import_dir=import_dir,
                    import_language=import_language,
                    output_dir=output_dir,
                    output_language=output_language,
                    data_source_choice=data_source_choice,
                    has_input_keyed=has_input_keyed,
                    output_csv=output_csv,
                )
                ui.print_success(f"智能提取完成！共提取 {len(translations)} 条翻译")
                ui.print_info(f"CSV文件：{csv_path}")
                ui.print_info(f"输出目录：{output_dir}")
                return (csv_path, mod_dir)
            elif conflict_resolution == "incremental":
                ui.print_info("新增模式")
                # 新增模式
                translations, csv_path = template_manager.incremental_mode(
                    import_dir=import_dir,
                    import_language=import_language,
                    output_dir=output_dir,
                    output_language=output_language,
                    data_source_choice=data_source_choice,
                    has_input_keyed=has_input_keyed,
                    output_csv=output_csv,
                )
                if translations:
                    ui.print_success(f"新增模式完成！新增了 {len(translations)} 条翻译")
                    ui.print_info(f"CSV文件：{csv_path}")
                    ui.print_info(f"输出目录：{output_dir}")
                    return (csv_path, mod_dir)
                else:
                    ui.print_success("新增模式完成！没有发现缺少的key")
                    return None
            elif conflict_resolution in ["rebuild", "new"]:  # 包括 'rebuild' 和 'new'
                ui.print_info("重建模式")
                language_dir = config.language_config.get_language_dir(
                    output_path, output_language
                )
                if language_dir.exists():
                    try:
                        import shutil

                        for item in language_dir.iterdir():
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                        ui.print_info(f"🗑️ 已清空输出目录：{language_dir}")
                    except PermissionError as e:
                        ui.print_warning(
                            f"⚠️ 无法删除某些文件（可能是系统文件），跳过：{e}"
                        )
                        # 步骤 2: 统一执行提取
                translations, csv_path = (
                    template_manager.extract_and_generate_templates(
                        import_dir=import_dir,
                        import_language=import_language,
                        output_dir=output_dir,
                        output_language=output_language,
                        data_source_choice=data_source_choice,
                        template_structure=template_structure,
                        has_input_keyed=has_input_keyed,
                        output_csv=output_csv,
                    )
                )
                ui.print_success(f"重建完成！共提取 {len(translations)} 条翻译")
                ui.print_info(f"CSV文件：{csv_path}")
                ui.print_info(f"输出目录：{output_dir}")
                return (csv_path, mod_dir)
            else:
                ui.print_info(f"无效的冲突处理方式: {conflict_resolution}")
                return None

        except (OSError, IOError, ValueError, RuntimeError) as e:
            ui.print_error(f"智能提取失败: {str(e)}")
            log_error_with_context(e, "智能提取失败", mod_dir=mod_dir)
            if config.system_config.get_value("debug_mode", False):
                import traceback

                traceback.print_exc()
            return None
        except ValueError as e:
            ui.print_error(
                f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
            )
            log_error_with_context(e, "配置错误", mod_dir=mod_dir)
            if config.system_config.get_value("debug_mode", False):
                import traceback

                traceback.print_exc()
            return None

    except (OSError, IOError, ValueError, ImportError, AttributeError) as e:
        ui.print_error(f"提取模板功能失败: {str(e)}")
        log_error_with_context(e, "提取模板功能失败")
        if config.system_config.get_value("debug_mode", False):
            import traceback

            traceback.print_exc()
        return None
    except ValueError as e:
        ui.print_error(
            f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
        )
        log_error_with_context(e, "配置错误")
        if config.system_config.get_value("debug_mode", False):
            import traceback

            traceback.print_exc()
        return None
