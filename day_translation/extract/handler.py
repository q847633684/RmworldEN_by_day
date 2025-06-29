"""
提取模板处理器
处理提取模板的交互流程
"""

import logging
from colorama import Fore, Style
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from day_translation.utils.interaction import (
    select_mod_path_with_version_detection,
    select_output_directory,
    show_success,
    show_error,
    show_info,
    show_warning
)
from day_translation.utils.path_manager import PathManager
from .smart_merger import SmartMerger

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
        
        # 创建智能合并器
        smart_merger = SmartMerger()

        show_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程
            smart_config = interaction_manager.handle_smart_extraction_workflow(mod_dir)
            
            # 从智能配置中获取所有参数
            output_dir = smart_config['output_config']['output_dir']
            conflict_resolution = smart_config['output_config']['conflict_resolution']
            data_source_choice = smart_config['data_sources']['choice']
            template_structure = smart_config['template_structure']
            
            show_info(f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}")

            # 根据冲突处理方式执行相应操作
            if conflict_resolution == 'rebuild':
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
                translations = facade.extract_templates_and_generate_csv(
                    output_dir=output_dir,
                    data_source_choice=data_source_choice,
                    template_structure=template_structure
                )
                show_success(f"重建完成！共提取 {len(translations)} 条翻译")
                
            elif conflict_resolution == 'overwrite':
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
                translations = facade.extract_templates_and_generate_csv(
                    output_dir=output_dir,
                    data_source_choice=data_source_choice,
                    template_structure=template_structure
                )
                show_success(f"覆盖完成！共提取 {len(translations)} 条翻译")
                
            elif conflict_resolution == 'merge':
                # 合并：使用智能合并功能
                show_info("🔄 正在执行智能合并...")
                
                # 直接提取新的翻译数据，不生成模板文件
                if data_source_choice == 'definjected_only':
                    definjected_extract_mode = "definjected_only"
                else:
                    definjected_extract_mode = "defs_only"
                
                new_translations = facade.template_manager._extract_all_translations(
                    data_source_choice=definjected_extract_mode, 
                    direct_dir=None
                )
                
                # 执行智能合并（_perform_smart_merge会直接从文件系统读取现有翻译）
                merge_results = _perform_smart_merge(output_dir, new_translations, smart_merger)
                if merge_results:
                    show_success(f"智能合并完成！")
                    show_info(f"合并统计：替换 {merge_results['summary']['total_replaced']} 个，新增 {merge_results['summary']['total_added']} 个，保持 {merge_results['summary']['total_unchanged']} 个")
                else:
                    show_warning("智能合并未执行，可能是没有现有文件需要合并")
                
                translations = new_translations  # 用于显示总数
            
            else:
                # 新建：直接提取
                translations = facade.extract_templates_and_generate_csv(
                    output_dir=output_dir,
                    data_source_choice=data_source_choice,
                    template_structure=template_structure
                )
                show_success(f"智能提取完成！共提取 {len(translations)} 条翻译")
            
            show_info(f"输出目录：{output_dir}")
            
        except Exception as e:
            show_error(f"智能提取失败: {str(e)}")
            logging.error("智能提取失败: %s", str(e), exc_info=True)
    except Exception as e:
        show_error(f"提取模板功能失败: {str(e)}")
        logging.error("提取模板功能失败: %s", str(e), exc_info=True)

def _perform_smart_merge(output_dir: str, translations: List[Tuple[str, str, str, str]], smart_merger: SmartMerger) -> Optional[Dict]:
    """
    执行智能合并操作
    
    Args:
        output_dir (str): 输出目录
        translations (List[Tuple[str, str, str, str]]): 提取的翻译数据，格式为 (key, text, group, file_info)
        smart_merger (SmartMerger): 智能合并器实例
        
    Returns:
        Optional[Dict]: 合并结果，如果没有需要合并的文件则返回None
    """
    try:
        output_path = Path(output_dir)
        file_mappings = []
        
        # 处理DefInjected文件
        definjected_dir = output_path / "DefInjected"
        if definjected_dir.exists():
            for xml_file in definjected_dir.rglob("*.xml"):
                if xml_file.is_file():
                    # 从translations中提取对应文件的翻译内容
                    file_translations = _extract_file_translations(xml_file, translations)
                    if file_translations:
                        file_mappings.append((str(xml_file), file_translations))
        
        # 处理Keyed文件
        keyed_dir = output_path / "Keyed"
        if keyed_dir.exists():
            for xml_file in keyed_dir.glob("*.xml"):
                if xml_file.is_file():
                    # 从translations中提取对应文件的翻译内容
                    file_translations = _extract_file_translations(xml_file, translations)
                    if file_translations:
                        file_mappings.append((str(xml_file), file_translations))
        
        if not file_mappings:
            return None
        
        # 执行批量合并
        results = smart_merger.merge_multiple_files(file_mappings)
        
        # 打印合并结果
        smart_merger.print_batch_summary(results)
        
        return results
        
    except Exception as e:
        logging.error(f"智能合并失败: {e}")
        show_error(f"智能合并失败: {str(e)}")
        return None

def _extract_file_translations(xml_file: Path, translations: List[Tuple[str, str, str, str]]) -> Dict[str, str]:
    """
    从翻译数据中提取对应文件的翻译内容
    
    Args:
        xml_file (Path): XML文件路径
        translations (List[Tuple[str, str, str, str]]): 翻译数据列表，格式为 (key, text, group, file_info)
        
    Returns:
        Dict[str, str]: 该文件的翻译内容 {key: text}
    """
    file_translations = {}
    
    # 获取XML文件的相对路径，用于匹配翻译数据
    xml_file_name = xml_file.name
    
    # 遍历翻译数据，格式为 (key, text, group, file_info)
    for key, text, group, file_info in translations:
        # 检查文件信息是否匹配当前XML文件
        if file_info and (file_info.endswith(xml_file_name) or xml_file_name in file_info):
            file_translations[key] = text
    
    return file_translations 