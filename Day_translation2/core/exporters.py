"""
Day Translation 2 - 数据导出核心模块

负责将翻译数据导出为各种格式和结构，支持多种导出策略。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。

核心功能:
- Keyed导出: 生成Keyed翻译模板
- DefInjected导出: 生成DefInjected翻译模板
- CSV导出: 将翻译数据导出为CSV格式
- 多种结构导出: 原始结构、Defs结构、英文模板结构
- 智能合并: 支持多种合并策略
"""

import csv
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from colorama import Fore, Style

try:
    # 尝试相对导入（包内使用）
    from ..config import get_config
    from ..models.exceptions import (
        ExportError,
        ProcessingError,
        TranslationError,
        ValidationError,
    )
    from ..models.result_models import OperationResult, OperationStatus, OperationType
    from ..models.translation_data import TranslationData, TranslationType
    from ..utils.export_manager import ExportManager, ExportMode
    from ..utils.file_utils import get_language_folder_path
    from ..utils.user_interaction import UserInteractionManager
    from ..utils.xml_processor import AdvancedXMLProcessor
except ImportError:
    # 备用绝对导入（独立运行时�?
    # 添加项目根目录到sys.path
    current_dir = Path(__file__).parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

    from config import get_config
    from models.exceptions import (
        ExportError,
        ProcessingError,
        TranslationError,
        ValidationError,
    )
    from models.result_models import OperationResult, OperationStatus, OperationType
    from models.translation_data import TranslationData, TranslationType
    from utils.export_manager import ExportManager, ExportMode
    from utils.file_utils import get_language_folder_path
    from utils.user_interaction import UserInteractionManager
    from utils.xml_processor import AdvancedXMLProcessor

# 获取配置实例
CONFIG = get_config()


def export_keyed(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
) -> OperationResult:
    """
    导出Keyed翻译文件

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言

    Returns:
        操作结果

    Raises:
        ValidationError: 参数验证失败
        ExportError: 导出失败
    """
    print(f"{Fore.GREEN}正在导出 Keyed 翻译文件...{Style.RESET_ALL}")

    # 参数验证
    if not translations:
        raise ValidationError("翻译数据不能为空")

    if not output_dir:
        raise ValidationError("输出目录不能为空")

    try:
        # 筛选Keyed类型的翻译
        keyed_translations = [
            t for t in translations if t.translation_type == TranslationType.KEYED
        ]

        if not keyed_translations:
            logging.warning("没有找到Keyed类型的翻译")
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.EXPORT,
                message="没有找到Keyed类型的翻译",
                details={"total_translations": len(translations)},
            )

        # 创建输出目录
        lang_path = get_language_folder_path(language, output_dir)
        keyed_dir = Path(lang_path) / CONFIG.core.keyed_dir
        keyed_dir.mkdir(parents=True, exist_ok=True)

        # 按文件路径分�?
        file_groups: Dict[str, List[TranslationData]] = {}
        for translation in keyed_translations:
            file_path = translation.file_path or "Keyed.xml"
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(translation)

        processor = AdvancedXMLProcessor()
        exported_files = []

        # 为每个文件组生成XML
        for file_path, group_translations in file_groups.items():
            try:
                output_file = keyed_dir / file_path
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # 生成XML内容
                xml_content = _generate_keyed_xml(group_translations)

                # 保存文件
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(xml_content)

                exported_files.append(str(output_file))
                logging.debug(f"导出Keyed文件: {output_file}")

            except Exception as e:
                logging.error(f"导出Keyed文件失败 {file_path}: {str(e)}")
                continue

        success = len(exported_files) > 0
        message = f"成功导出 {len(exported_files)} 个Keyed文件，包含 {len(keyed_translations)} 条翻译"

        if success:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Keyed导出失败{Style.RESET_ALL}")

        return OperationResult(
            status=OperationStatus.SUCCESS if success else OperationStatus.FAILED,
            operation_type=OperationType.EXPORT,
            message=message,
            details={
                "exported_files": len(exported_files),
                "translations_count": len(keyed_translations),
                "output_dir": str(keyed_dir),
            },
        )

    except ValidationError:
        raise
    except Exception as e:
        error_msg = f"Keyed导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(
            error_msg,
            output_path=output_dir,
        )


def export_definjected(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
) -> OperationResult:
    """
    导出DefInjected翻译文件

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言

    Returns:
        操作结果
    """
    print(f"{Fore.GREEN}正在导出 DefInjected 翻译文件...{Style.RESET_ALL}")

    # 参数验证
    if not translations:
        raise ValidationError("翻译数据不能为空")

    try:
        # 筛选DefInjected类型的翻译
        definjected_translations = [
            t for t in translations if t.translation_type == TranslationType.DEFINJECTED
        ]

        if not definjected_translations:
            logging.warning("没有找到DefInjected类型的翻译")
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.EXPORT,
                message="没有找到DefInjected类型的翻译",
                details={"total_translations": len(translations)},
            )

        # 创建输出目录
        lang_path = get_language_folder_path(language, output_dir)
        definjected_dir = Path(lang_path) / CONFIG.core.definjected_dir
        definjected_dir.mkdir(parents=True, exist_ok=True)

        # 按def_type分组
        type_groups: Dict[str, List[TranslationData]] = {}
        for translation in definjected_translations:
            def_type = translation.metadata.get("def_type", "Unknown")
            if def_type not in type_groups:
                type_groups[def_type] = []
            type_groups[def_type].append(translation)

        exported_files = []

        # 为每个def_type生成XML文件
        for def_type, group_translations in type_groups.items():
            try:
                output_file = definjected_dir / f"{def_type}.xml"

                # 生成XML内容
                xml_content = _generate_definjected_xml(group_translations, def_type)

                # 保存文件
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(xml_content)

                exported_files.append(str(output_file))
                logging.debug(f"导出DefInjected文件: {output_file}")

            except Exception as e:
                logging.error(f"导出DefInjected文件失败 {def_type}: {str(e)}")
                continue

        success = len(exported_files) > 0
        message = f"成功导出 {len(exported_files)} 个DefInjected文件，包含 {len(definjected_translations)} 条翻译"

        if success:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

        return OperationResult(
            status=OperationStatus.SUCCESS if success else OperationStatus.FAILED,
            operation_type=OperationType.EXPORT,
            message=message,
            details={
                "exported_files": len(exported_files),
                "translations_count": len(definjected_translations),
                "output_dir": str(definjected_dir),
            },
        )

    except ValidationError:
        raise
    except Exception as e:
        error_msg = f"DefInjected导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


def export_definjected_with_original_structure(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
) -> OperationResult:
    """
    按原始结构导出DefInjected（保持源文件结构）

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言

    Returns:
        操作结果
    """
    print(f"{Fore.GREEN}正在按原始结构导出 DefInjected...{Style.RESET_ALL}")

    try:
        # 筛选DefInjected类型的翻译
        definjected_translations = [
            t for t in translations if t.translation_type == TranslationType.DEFINJECTED
        ]

        if not definjected_translations:
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.EXPORT,
                message="没有找到DefInjected类型的翻译",
            )

        # 创建输出目录
        lang_path = get_language_folder_path(language, output_dir)
        definjected_dir = Path(lang_path) / CONFIG.core.definjected_dir
        definjected_dir.mkdir(parents=True, exist_ok=True)

        # 按文件路径分组（保持原始结构�?
        file_groups: Dict[str, List[TranslationData]] = {}
        for translation in definjected_translations:
            file_path = (
                translation.file_path
                or f"{translation.metadata.get('def_type', 'Unknown')}.xml"
            )
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(translation)

        exported_files = []

        # 为每个文件组生成XML
        for file_path, group_translations in file_groups.items():
            try:
                output_file = definjected_dir / file_path
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # 按def_type进一步分�?
                type_groups: Dict[str, List[TranslationData]] = {}
                for translation in group_translations:
                    def_type = translation.metadata.get("def_type", "Unknown")
                    if def_type not in type_groups:
                        type_groups[def_type] = []
                    type_groups[def_type].append(translation)

                # 生成包含多个def_type的XML内容
                xml_content = _generate_definjected_xml_multi_type(type_groups)

                # 保存文件
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(xml_content)

                exported_files.append(str(output_file))
                logging.debug(f"导出原始结构DefInjected文件: {output_file}")

            except Exception as e:
                logging.error(f"导出原始结构DefInjected文件失败 {file_path}: {str(e)}")
                continue

        success = len(exported_files) > 0
        message = f"成功按原始结构导出 {len(exported_files)} 个DefInjected文件"

        if success:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

        return OperationResult(
            status=OperationStatus.SUCCESS if success else OperationStatus.FAILED,
            operation_type=OperationType.EXPORT,
            message=message,
            details={
                "exported_files": len(exported_files),
                "translations_count": len(definjected_translations),
                "output_dir": str(definjected_dir),
                "structure_type": "original",
            },
        )

    except Exception as e:
        error_msg = f"原始结构DefInjected导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


def export_definjected_with_defs_structure(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
) -> OperationResult:
    """
    按Defs结构导出DefInjected（按定义类型分组）

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言

    Returns:
        操作结果
    """
    print(f"{Fore.GREEN}正在按Defs结构导出 DefInjected...{Style.RESET_ALL}")

    # 这与标准的export_definjected相同，按def_type分组
    return export_definjected(translations, output_dir, language)


def export_to_csv(
    translations: List[TranslationData], csv_path: str, include_context: bool = True
) -> OperationResult:
    """
    将翻译数据导出为CSV格式

    Args:
        translations: 翻译条目列表
        csv_path: CSV文件路径
        include_context: 是否包含上下文信息

    Returns:
        操作结果
    """
    print(f"{Fore.GREEN}正在导出CSV文件: {csv_path}...{Style.RESET_ALL}")

    if not translations:
        raise ValidationError("翻译数据不能为空")

    try:
        # 确保输出目录存在
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        # 准备CSV字段
        fieldnames = [
            "key",
            "original_text",
            "translated_text",
            "translation_type",
            "file_path",
            "tag",
        ]

        if include_context:
            fieldnames.extend(
                ["def_type", "def_name", "field_path", "language", "mod_dir"]
            )

        # 写入CSV文件
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for translation in translations:
                row = {
                    "key": translation.key,
                    "original_text": translation.original_text,
                    "translated_text": translation.translated_text,
                    "translation_type": translation.translation_type.value,
                    "file_path": translation.file_path,
                    "tag": translation.tag,
                }

                if include_context and translation.metadata:
                    row.update(
                        {
                            "def_type": translation.metadata.get("def_type", ""),
                            "def_name": translation.metadata.get("def_name", ""),
                            "field_path": translation.metadata.get("field_path", ""),
                            "language": translation.metadata.get("language", ""),
                            "mod_dir": translation.metadata.get("mod_dir", ""),
                        }
                    )

                writer.writerow(row)

        message = f"成功导出 {len(translations)} 条翻译到CSV文件"
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type=OperationType.EXPORT,
            message=message,
            details={
                "csv_path": csv_path,
                "translations_count": len(translations),
                "include_context": include_context,
            },
        )

    except Exception as e:
        error_msg = f"CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


def export_keyed_to_csv(keyed_dir: str, csv_path: str) -> OperationResult:
    """
    将Keyed目录导出为CSV

    Args:
        keyed_dir: Keyed目录路径
        csv_path: CSV文件路径

    Returns:
        操作结果
    """
    try:
        # 使用提取器获取Keyed翻译
        from .extractors import extract_keyed_translations_legacy

        # 从Keyed目录的父目录提取
        mod_dir = str(Path(keyed_dir).parent.parent)
        language = Path(keyed_dir).parent.name

        translations_data = extract_keyed_translations_legacy(mod_dir, language)

        # 转换为TranslationEntry格式
        translations = []
        for key, text, tag, file_path in translations_data:
            entry = TranslationData(
                key=key,
                original_text=text,
                translated_text="",
                translation_type=TranslationType.KEYED,
                file_path=file_path,
                tag=tag,
                metadata={"language": language, "mod_dir": mod_dir},
            )
            translations.append(entry)

        return export_to_csv(translations, csv_path, include_context=False)

    except Exception as e:
        error_msg = f"Keyed目录CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


def export_definjected_to_csv(definjected_dir: str, csv_path: str) -> OperationResult:
    """
    将DefInjected目录导出为CSV

    Args:
        definjected_dir: DefInjected目录路径
        csv_path: CSV文件路径

    Returns:
        操作结果
    """
    try:
        # 使用提取器获取DefInjected翻译
        from .extractors import extract_definjected_translations_legacy

        # 从DefInjected目录的父目录提取
        mod_dir = str(Path(definjected_dir).parent.parent)
        language = Path(definjected_dir).parent.name

        translations_data = extract_definjected_translations_legacy(mod_dir, language)

        # 转换为TranslationEntry格式
        translations = []
        for key, text, tag, file_path in translations_data:
            entry = TranslationData(
                key=key,
                original_text=text,
                translated_text="",
                translation_type=TranslationType.DEFINJECTED,
                file_path=file_path,
                tag=tag,
                metadata={"language": language, "mod_dir": mod_dir},
            )
            translations.append(entry)

        return export_to_csv(translations, csv_path, include_context=True)

    except Exception as e:
        error_msg = f"DefInjected目录CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


# 高级导出功能，集成ExportManager和UserInteractionManager
def export_with_smart_merge(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
    mode: str = "smart-merge",
    auto_mode: bool = False,
) -> OperationResult:
    """
    使用智能合并模式导出翻译文件

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言
        mode: 导出模式 (replace/merge/smart-merge/backup/incremental/preview/skip)
        auto_mode: 是否自动模式

    Returns:
        操作结果
    """
    try:
        print(f"{Fore.GREEN}🚀 启动智能导出流程...{Style.RESET_ALL}")

        # 创建导出管理器
        export_manager = ExportManager(
            output_dir=output_dir, language=language, auto_mode=auto_mode
        )

        # 转换导出模式
        export_mode = ExportMode(mode)

        # 分离Keyed和DefInjected翻译
        keyed_translations = [
            t for t in translations if t.translation_type == TranslationType.KEYED
        ]
        definjected_translations = [
            t for t in translations if t.translation_type == TranslationType.DEFINJECTED
        ]

        results = []

        # 导出Keyed翻译
        if keyed_translations:
            print(
                f"{Fore.CYAN}📝 导出Keyed翻译 ({len(keyed_translations)} 条)...{Style.RESET_ALL}"
            )
            keyed_result = export_manager.export_keyed_translations(
                keyed_translations, mode=export_mode
            )
            results.append(keyed_result)

        # 导出DefInjected翻译
        if definjected_translations:
            print(
                f"{Fore.CYAN}📝 导出DefInjected翻译 ({len(definjected_translations)} 条)...{Style.RESET_ALL}"
            )
            definjected_result = export_manager.export_definjected_translations(
                definjected_translations, mode=export_mode
            )
            results.append(definjected_result)

        # 合并结果
        total_files = sum(r.files_processed for r in results)
        total_created = sum(r.files_created for r in results)
        total_updated = sum(r.files_updated for r in results)

        success = all(r.success for r in results)

        if success:
            message = f"智能导出完成: 处理 {total_files} 个文件，创建 {total_created} 个，更新 {total_updated} 个"
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            message = f"智能导出部分失败: 处理 {total_files} 个文件"
            print(f"{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")

        return OperationResult(
            status=OperationStatus.SUCCESS if success else OperationStatus.FAILED,
            operation_type=OperationType.EXPORT,
            message=message,
            details={
                "export_mode": mode,
                "total_files": total_files,
                "files_created": total_created,
                "files_updated": total_updated,
                "keyed_count": len(keyed_translations),
                "definjected_count": len(definjected_translations),
                "results": [r.__dict__ for r in results],
            },
        )

    except Exception as e:
        error_msg = f"智能导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


def export_with_user_interaction(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
) -> OperationResult:
    """
    使用用户交互模式导出翻译文件

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言

    Returns:
        操作结果
    """
    try:
        print(f"{Fore.GREEN}🚀 启动交互式导出流程...{Style.RESET_ALL}")

        # 创建用户交互管理器
        interaction_manager = UserInteractionManager()

        # 分析导出场景
        analysis = interaction_manager.analyze_export_scenario(
            output_dir=output_dir,
            language=language,
            translations_count=len(translations),
        )

        # 显示分析结果
        print(f"\n{Fore.CYAN}📊 导出分析结果:{Style.RESET_ALL}")
        print(f"目标目录: {output_dir}")
        print(f"目标语言: {language}")
        print(f"翻译数量: {len(translations)}")
        print(f"预计文件数: {analysis.total_files}")
        print(f"冲突文件数: {analysis.will_be_affected}")

        # 获取用户选择
        choice = interaction_manager.handle_existing_translations_choice(
            analysis=analysis, default_mode="smart-merge"
        )

        if choice.mode == ExportMode.SKIP:
            print(f"{Fore.YELLOW}⏭️ 用户选择跳过导出{Style.RESET_ALL}")
            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message="用户选择跳过导出",
                details={"action": "skipped"},
            )

        # 执行导出
        return export_with_smart_merge(
            translations=translations,
            output_dir=output_dir,
            language=language,
            mode=choice.mode.value,
            auto_mode=choice.auto_mode,
        )

    except Exception as e:
        error_msg = f"交互式导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


def batch_export_with_smart_merge(
    translation_groups: List[Tuple[List[TranslationData], str, str]],
    base_output_dir: str,
    default_mode: str = "smart-merge",
    auto_mode: bool = False,
) -> OperationResult:
    """
    批量智能导出多个翻译组

    Args:
        translation_groups: 翻译组列表，每个元素为(翻译列表, 输出目录, 语言)
        base_output_dir: 基础输出目录
        default_mode: 默认导出模式
        auto_mode: 是否自动模式

    Returns:
        操作结果
    """
    try:
        print(f"{Fore.GREEN}🚀 启动批量智能导出流程...{Style.RESET_ALL}")

        total_groups = len(translation_groups)
        successful_groups = 0
        failed_groups = 0
        all_results = []

        for i, (translations, output_dir, language) in enumerate(translation_groups, 1):
            try:
                print(
                    f"\n{Fore.CYAN}📦 处理第 {i}/{total_groups} 组翻译...{Style.RESET_ALL}"
                )

                # 确保输出目录是绝对路径
                if not os.path.isabs(output_dir):
                    output_dir = os.path.join(base_output_dir, output_dir)

                result = export_with_smart_merge(
                    translations=translations,
                    output_dir=output_dir,
                    language=language,
                    mode=default_mode,
                    auto_mode=auto_mode,
                )

                all_results.append(result)

                if result.success:
                    successful_groups += 1
                    print(f"{Fore.GREEN}✅ 第 {i} 组导出成功{Style.RESET_ALL}")
                else:
                    failed_groups += 1
                    print(
                        f"{Fore.RED}❌ 第 {i} 组导出失败: {result.message}{Style.RESET_ALL}"
                    )

            except Exception as e:
                failed_groups += 1
                error_msg = f"第 {i} 组导出失败: {str(e)}"
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                logging.error(error_msg)

                # 创建失败结果
                failed_result = OperationResult(
                    status=OperationStatus.FAILED,
                    operation_type=OperationType.EXPORT,
                    message=error_msg,
                    details={"group_index": i, "error": str(e)},
                )
                all_results.append(failed_result)

        # 汇总结果
        success = failed_groups == 0
        message = f"批量导出完成: 成功 {successful_groups} 组，失败 {failed_groups} 组"

        if success:
            print(f"\n{Fore.GREEN}🎉 {message}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")

        return OperationResult(
            status=OperationStatus.SUCCESS if success else OperationStatus.FAILED,
            operation_type=OperationType.EXPORT,
            message=message,
            details={
                "total_groups": total_groups,
                "successful_groups": successful_groups,
                "failed_groups": failed_groups,
                "export_mode": default_mode,
                "auto_mode": auto_mode,
                "results": [r.__dict__ for r in all_results],
            },
        )

    except Exception as e:
        error_msg = f"批量导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


# 导出为包含导出管理器的完整工作流程
def export_all_with_advanced_features(
    translations: List[TranslationData],
    output_dir: str,
    language: str = CONFIG.core.default_language,
    export_config: Optional[Dict[str, Any]] = None,
) -> OperationResult:
    """
    使用高级功能导出所有翻译

    Args:
        translations: 翻译条目列表
        output_dir: 输出目录路径
        language: 目标语言
        export_config: 导出配置

    Returns:
        操作结果
    """
    try:
        config = export_config or {}

        # 确定导出模式
        if config.get("interactive", False):
            # 交互式模式
            return export_with_user_interaction(translations, output_dir, language)
        else:
            # 智能模式
            mode = config.get("mode", "smart-merge")
            auto_mode = config.get("auto_mode", False)
            return export_with_smart_merge(
                translations, output_dir, language, mode, auto_mode
            )

    except Exception as e:
        error_msg = f"高级导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)


# 私有辅助函数


def _generate_keyed_xml(translations: List[TranslationData]) -> str:
    """生成Keyed XML内容"""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]

    for translation in translations:
        comment = (
            f"  <!-- EN: {translation.original_text} -->"
            if translation.original_text
            else ""
        )
        if comment:
            lines.append(comment)

        # 使用translated_text如果存在，否则使用original_text作为模板
        text = translation.translated_text or translation.original_text
        lines.append(f"  <{translation.key}>{text}</{translation.key}>")

    lines.append("</LanguageData>")
    return "\n".join(lines)


def _generate_definjected_xml(
    translations: List[TranslationData], def_type: str
) -> str:
    """生成DefInjected XML内容"""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]

    # 按def_name分组
    name_groups: Dict[str, List[TranslationData]] = {}
    for translation in translations:
        def_name = translation.metadata.get("def_name", "Unknown")
        if def_name not in name_groups:
            name_groups[def_name] = []
        name_groups[def_name].append(translation)

    for def_name, group_translations in name_groups.items():
        lines.append(f"  <!-- {def_type}: {def_name} -->")

        for translation in group_translations:
            field_path = translation.metadata.get(
                "field_path", translation.key.split(".")[-1]
            )
            full_key = f"{def_type}.{def_name}.{field_path}"

            comment = (
                f"  <!-- EN: {translation.original_text} -->"
                if translation.original_text
                else ""
            )
            if comment:
                lines.append(comment)

            text = translation.translated_text or translation.original_text
            lines.append(f"  <{full_key}>{text}</{full_key}>")

    lines.append("</LanguageData>")
    return "\n".join(lines)


def _generate_definjected_xml_multi_type(
    type_groups: Dict[str, List[TranslationData]],
) -> str:
    """生成包含多个def_type的DefInjected XML内容"""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]

    for def_type, type_translations in type_groups.items():
        lines.append(f"  <!-- {def_type} -->")
        content = _generate_definjected_xml(type_translations, def_type)
        # 提取内容部分（去掉XML头和LanguageData标签）
        content_lines = content.split("\n")[2:-1]  # 跳过前两行和最后一行
        lines.extend(content_lines)
        lines.append("")  # 添加空行分隔

    lines.append("</LanguageData>")
    return "\n".join(lines)


class AdvancedExporter:
    """
    高级导出器类 - 游戏本地化数据导出的门面类

    提供统一的接口来导出翻译数据：
    - CSV格式导出
    - XML格式导出
    - 批量导出和自定义配置
    - 高级导出功能集成
    """

    def __init__(
        self, output_dir: Optional[str] = None, language: Optional[str] = None
    ):
        """
        初始化高级导出器

        Args:
            output_dir: 输出目录路径
            language: 目标语言，默认使用配置中的默认语言
        """
        self.output_dir = output_dir or "./output"
        self.language = language or CONFIG.core.default_language
        self.config = CONFIG

        # 初始化组件
        self.export_manager = ExportManager()

        # 设置日志
        self.logger = logging.getLogger(__name__)

    def export_to_csv(
        self,
        translations: List[TranslationData],
        csv_path: str,
        include_context: bool = True,
    ) -> OperationResult:
        """
        导出翻译数据到CSV文件

        Args:
            translations: 翻译数据列表
            csv_path: CSV文件路径
            include_context: 是否包含上下文信息
              Returns:
            导出操作结果
        """
        try:
            export_to_csv(translations, csv_path, include_context)
            self.logger.info(f"CSV导出完成: {csv_path}")

            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message=f"成功导出 {len(translations)} 条翻译到CSV",
                details={"csv_path": csv_path, "translation_count": len(translations)},
            )

        except Exception as e:
            self.logger.error(f"CSV导出失败: {e}")
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.EXPORT,
                message=f"CSV导出失败: {str(e)}",
                details={"csv_path": csv_path, "error": str(e)},
            )

    def export_keyed_xml(
        self, translations: List[TranslationData], output_dir: Optional[str] = None
    ) -> OperationResult:
        """
        导出Keyed翻译为XML格式

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录，默认使用初始化时的目录

        Returns:
            导出操作结果
        """
        try:
            target_dir = output_dir or self.output_dir
            keyed_translations = [
                t for t in translations if t.translation_type == TranslationType.KEYED
            ]

            export_keyed(keyed_translations, target_dir, self.language)
            self.logger.info(f"Keyed XML导出完成: {target_dir}")

            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message=f"成功导出 {len(keyed_translations)} 条Keyed翻译到XML",
                details={
                    "output_dir": target_dir,
                    "keyed_count": len(keyed_translations),
                },
            )

        except Exception as e:
            self.logger.error(f"Keyed XML导出失败: {e}")
            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message=f"Keyed XML导出失败: {str(e)}",
                details={"output_dir": target_dir, "error": str(e)},
            )

    def export_definjected_xml(
        self, translations: List[TranslationData], output_dir: Optional[str] = None
    ) -> OperationResult:
        """
        导出DefInjected翻译为XML格式

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录，默认使用初始化时的目录

        Returns:
            导出操作结果
        """
        try:
            target_dir = output_dir or self.output_dir
            definjected_translations = [
                t
                for t in translations
                if t.translation_type == TranslationType.DEFINJECTED
            ]

            export_definjected(definjected_translations, target_dir, self.language)
            self.logger.info(f"DefInjected XML导出完成: {target_dir}")

            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message=f"成功导出 {len(definjected_translations)} 条DefInjected翻译到XML",
                details={
                    "output_dir": target_dir,
                    "definjected_count": len(definjected_translations),
                },
            )

        except Exception as e:
            self.logger.error(f"DefInjected XML导出失败: {e}")
            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message=f"DefInjected XML导出失败: {str(e)}",
                details={"output_dir": target_dir, "error": str(e)},
            )

    def export_all(
        self,
        translations: List[TranslationData],
        export_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, OperationResult]:
        """
        导出所有类型的翻译数据

        Args:
            translations: 翻译数据列表
            export_config: 导出配置

        Returns:
            按导出类型分组的操作结果字典
        """
        results = {}

        try:
            # 导出CSV
            csv_path = Path(self.output_dir) / f"translations_{self.language}.csv"
            results["csv"] = self.export_to_csv(translations, str(csv_path))

            # 导出Keyed XML
            results["keyed_xml"] = self.export_keyed_xml(translations)

            # 导出DefInjected XML
            results["definjected_xml"] = self.export_definjected_xml(translations)

            # 使用高级功能导出
            if export_config:
                advanced_result = export_all_with_advanced_features(
                    translations, self.output_dir, self.language, export_config
                )
                results["advanced"] = advanced_result

            total_success = sum(1 for r in results.values() if r.success)
            self.logger.info(f"批量导出完成: {total_success}/{len(results)} 成功")

        except Exception as e:
            self.logger.error(f"批量导出过程中出现错误: {e}")
            results["error"] = OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXPORT,
                message=f"批量导出失败: {str(e)}",
                details={"error": str(e)},
            )

        return results

    def get_export_statistics(
        self, translations: List[TranslationData]
    ) -> Dict[str, Any]:
        """
        获取导出统计信息

        Args:
            translations: 翻译数据列表

        Returns:
            统计信息字典
        """
        try:
            keyed_count = len(
                [t for t in translations if t.translation_type == TranslationType.KEYED]
            )
            definjected_count = len(
                [
                    t
                    for t in translations
                    if t.translation_type == TranslationType.DEFINJECTED
                ]
            )

            return {
                "total_translations": len(translations),
                "keyed_count": keyed_count,
                "definjected_count": definjected_count,
                "output_directory": self.output_dir,
                "target_language": self.language,
                "export_ready": True,
            }

        except Exception as e:
            self.logger.error(f"获取导出统计信息失败: {e}")
            return {"error": str(e), "export_ready": False}


# 导出所有函数和类
__all__ = [
    # 主要导出函数
    "export_keyed",
    "export_definjected",
    "export_to_csv",
    "export_keyed_to_csv",
    "export_definjected_to_csv",
    "export_all_with_advanced_features",
    # 高级导出器类
    "AdvancedExporter",
    # 辅助函数
    "_generate_keyed_xml",
    "_generate_definjected_xml",
    "_generate_definjected_xml_multi_type",
]
