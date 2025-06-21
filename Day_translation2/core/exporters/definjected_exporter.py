"""
Day Translation 2 - DefInjected翻译导出模块

负责DefInjected类型翻译数据的导出功能，支持多种结构导出。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。
"""

import logging
from pathlib import Path
from typing import Dict, List

from colorama import Fore, Style
from models.exceptions import ExportError, ValidationError
from models.result_models import OperationResult, OperationStatus, OperationType
from models.translation_data import TranslationData, TranslationType
from services.config_service import config_service
from utils.file_utils import get_language_folder_path

from .xml_generators import (
    generate_definjected_xml,
    generate_definjected_xml_multi_type,
)

CONFIG = config_service.get_unified_config()


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
                xml_content = generate_definjected_xml(group_translations, def_type)

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

        # 按文件路径分组（保持原始结构）
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

                # 按def_type进一步分组
                type_groups: Dict[str, List[TranslationData]] = {}
                for translation in group_translations:
                    def_type = translation.metadata.get("def_type", "Unknown")
                    if def_type not in type_groups:
                        type_groups[def_type] = []
                    type_groups[def_type].append(translation)

                # 生成包含多个def_type的XML内容
                xml_content = generate_definjected_xml_multi_type(type_groups)

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

    本函数为向后兼容的别名，实际与export_definjected相同，
    因为标准的DefInjected导出已经按def_type分组。

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
        from ..extractors import extract_definjected_translations

        # 从DefInjected目录的父目录提取
        mod_dir = str(Path(definjected_dir).parent.parent)
        language = Path(definjected_dir).parent.name

        translations = extract_definjected_translations(mod_dir, language)

        # 使用CSV导出模块
        from .csv_exporter import export_to_csv

        return export_to_csv(translations, csv_path, include_context=True)

    except Exception as e:
        error_msg = f"DefInjected目录CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)
