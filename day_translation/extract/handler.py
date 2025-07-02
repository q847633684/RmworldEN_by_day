"""
提取模板处理器
处理提取模板的交互流程
"""

import logging
from pathlib import Path
from day_translation.extract.smart_merger import SmartMerger
from day_translation.extract.exporters import write_merged_definjected_translations
from day_translation.utils.interaction import (
    select_mod_path_with_version_detection,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from day_translation.utils.path_manager import PathManager

path_manager = PathManager()


def handle_extract():
    """处理提取模板功能"""
    try:
        # 选择模组目录
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            return

        # 延迟导入，避免循环导入
        from day_translation.core.translation_facade import TranslationFacade
        from .interaction_manager import InteractionManager

        # 创建翻译门面实例
        facade = TranslationFacade(mod_dir)

        # 创建智能交互管理器
        interaction_manager = InteractionManager()

        show_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程
            smart_config = interaction_manager.handle_smart_extraction_workflow(mod_dir)

            # 从智能配置中获取所有参数
            output_dir = smart_config["output_config"]["output_dir"]
            conflict_resolution = smart_config["output_config"]["conflict_resolution"]
            data_source_choice = smart_config["data_sources"]["choice"]
            template_structure = smart_config["template_structure"]

            show_info(
                f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}"
            )

            # 根据冲突处理方式执行相应操作
            if conflict_resolution == "rebuild":
                # 重建：清空输出目录
                output_path = Path(output_dir)
                if output_path.exists():
                    try:
                        # 只删除翻译相关的目录，不删除整个目录
                        languages_dir = output_path / "Languages"
                        if languages_dir.exists():
                            import shutil

                            shutil.rmtree(languages_dir)
                            show_info(f"🗑️ 已清空翻译目录：{languages_dir}")
                        else:
                            show_info(f"📁 翻译目录不存在，无需清空：{languages_dir}")
                    except PermissionError as e:
                        show_warning(f"⚠️ 无法删除某些文件（可能是系统文件），跳过：{e}")

                # 重建后执行提取
                translations = facade.template_manager.extract_and_generate_templates(
                    output_dir=output_dir,
                    data_source_choice=data_source_choice,
                    template_structure=template_structure,
                )
                show_success(f"重建完成！共提取 {len(translations)} 条翻译")

            elif conflict_resolution == "overwrite":
                # 覆盖：删除现有的翻译文件
                import shutil

                output_path = Path(output_dir)
                definjected_dir = output_path / "DefInjected"
                keyed_dir = output_path / "Keyed"

                if definjected_dir.exists():
                    shutil.rmtree(definjected_dir)
                    show_info(f"🗑️ 已删除DefInjected目录：{definjected_dir}")
                if keyed_dir.exists():
                    shutil.rmtree(keyed_dir)
                    show_info(f"🗑️ 已删除Keyed目录：{keyed_dir}")
                # 覆盖后执行提取
                translations = facade.template_manager.extract_and_generate_templates(
                    output_dir=output_dir,
                    data_source_choice=data_source_choice,
                    template_structure=template_structure,
                )
                show_success(f"覆盖完成！共提取 {len(translations)} 条翻译")

            elif conflict_resolution == "merge":
                # 1. 提取输入目录数据（英文/原始）- 返回四元组
                input_data = facade.template_manager.extract_all_translations(
                    data_source_choice=data_source_choice,
                    direct_dir=None,
                )
                # 2. 提取输出目录数据（中文/现有）- 返回五元组
                output_data = facade.template_manager.extract_all_translations(
                    data_source_choice="definjected_only",
                    direct_dir=output_dir,
                )
                # 3. 智能合并（使用新版 SmartMerger 类）
                merger = SmartMerger(input_data, output_data)
                merged = merger.smart_merge_definjected_translations()
                show_info("🔄 正在执行智能合并...")
                # 4. 写回 XML
                write_merged_definjected_translations(merged, output_dir)
                show_success(f"智能合并完成！共处理 {len(merged)} 条翻译。")

            else:
                # 新建：直接提取
                translations = facade.template_manager.extract_and_generate_templates(
                    output_dir=output_dir,
                    data_source_choice=data_source_choice,
                    template_structure=template_structure,
                )
                show_success(f"智能提取完成！共提取 {len(translations)} 条翻译")

            show_info(f"输出目录：{output_dir}")

        except (OSError, IOError, ValueError, RuntimeError) as e:
            show_error(f"智能提取失败: {str(e)}")
            logging.error("智能提取失败: %s", str(e), exc_info=True)
    except (OSError, IOError, ValueError, ImportError, AttributeError) as e:
        show_error(f"提取模板功能失败: {str(e)}")
        logging.error("提取模板功能失败: %s", str(e), exc_info=True)
