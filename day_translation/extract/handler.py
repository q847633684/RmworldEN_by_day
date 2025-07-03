"""
提取模板处理器
处理提取模板的交互流程
"""

import logging
from pathlib import Path
from day_translation.utils.config import (
    get_config,
    get_language_subdir,
    ConfigError,
)
from day_translation.utils.interaction import (
    select_mod_path_with_version_detection,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from day_translation.utils.path_manager import PathManager


CONFIG = get_config()
path_manager = PathManager()


def handle_extract():
    """处理提取模板功能"""

    print(f"日志文件路径：{CONFIG.log_file}")
    if CONFIG.debug_mode:
        print("调试模式已开启，详细日志见日志文件。")
    try:
        # 选择模组目录  已检查
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            return

        # 延迟导入，避免循环导入
        from day_translation.extract.template_manager import TemplateManager
        from day_translation.extract.interaction_manager import InteractionManager

        template_manager = TemplateManager()

        # 创建智能交互管理器
        interaction_manager = InteractionManager()

        show_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程
            # 正在检查
            smart_config = interaction_manager.handle_smart_extraction_workflow(mod_dir)

            conflict_resolution = smart_config["output_config"][
                "conflict_resolution"
            ]  # 冲突处理
            data_source_choice = smart_config["data_sources"]["choice"]  # 数据来源
            template_structure = smart_config["template_structure"]  # 模板结构
            has_input_keyed = smart_config["data_sources"]["import_status"].get(
                "has_keyed", False
            )  #  输入是否已键化
            # has_output_keyed = smart_config["output_config"]["output_status"].get(
            #    "has_keyed", False
            # )  # 输出是否已键化
            import_dir = smart_config["data_sources"]["import_status"][
                "mod_dir"
            ]  # 导入路径
            import_language = smart_config["data_sources"]["import_status"]["language"]
            output_dir = smart_config["output_config"]["output_status"]["mod_dir"]
            output_language = smart_config["output_config"]["output_status"]["language"]
            show_info(
                f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}"
            )
            output_csv = CONFIG.output_csv
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
                show_success(
                    f"DefInjected 智能合并完成！共处理 {len(translations)} 条翻译。"
                )
            else:  # 包括 'rebuild', 'overwrite', 和 'new'
                # 步骤 1: 根据模式处理文件系统
                if conflict_resolution == "rebuild":
                    # 重建：清空输出目录
                    if output_path.exists():
                        try:
                            import shutil

                            for item in output_path.iterdir():
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            show_info(f"🗑️ 已清空输出目录：{output_path}")
                        except PermissionError as e:
                            show_warning(
                                f"⚠️ 无法删除某些文件（可能是系统文件），跳过：{e}"
                            )
                    else:
                        show_info(f"📁 输出目录不存在，将创建：{output_path}")

                elif conflict_resolution == "overwrite":
                    # 覆盖：删除现有的翻译文件
                    import shutil

                    definjected_dir = get_language_subdir(
                        base_dir=output_path,
                        language=output_language,
                        subdir_type="DefInjected",
                    )
                    keyed_dir = get_language_subdir(
                        base_dir=output_path,
                        language=output_language,
                        subdir_type="keyed",
                    )

                    if definjected_dir.exists():
                        shutil.rmtree(definjected_dir)
                        show_info(f"🗑️ 已删除DefInjected目录：{definjected_dir}")
                    if keyed_dir.exists():
                        shutil.rmtree(keyed_dir)
                        show_info(f"🗑️ 已删除Keyed目录：{keyed_dir}")

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
                elif conflict_resolution == "overwrite":
                    show_success(f"覆盖完成！共提取 {len(translations)} 条翻译")
                else:  # 'new'
                    show_success(f"智能提取完成！共提取 {len(translations)} 条翻译")

            show_info(f"输出目录：{output_dir}")

        except (OSError, IOError, ValueError, RuntimeError) as e:
            show_error(f"智能提取失败: {str(e)}")
            logging.error("智能提取失败: %s", str(e), exc_info=True)
            if CONFIG.debug_mode:
                import traceback

                traceback.print_exc()
        except ConfigError as e:
            show_error(
                f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
            )
            logging.error("配置错误：%s", e, exc_info=True)
            if CONFIG.debug_mode:
                import traceback

                traceback.print_exc()
    except (OSError, IOError, ValueError, ImportError, AttributeError) as e:
        show_error(f"提取模板功能失败: {str(e)}")
        logging.error("提取模板功能失败: %s", str(e), exc_info=True)
        if CONFIG.debug_mode:
            import traceback

            traceback.print_exc()
    except ConfigError as e:
        show_error(
            f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
        )
        logging.error("配置错误：%s", e, exc_info=True)
        if CONFIG.debug_mode:
            import traceback

            traceback.print_exc()
