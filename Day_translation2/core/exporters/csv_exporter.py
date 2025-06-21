"""
Day Translation 2 - CSV导出模块

负责将翻译数据导出为CSV格式，支持上下文信息和自定义字段配置。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。

核心功能:
- 基础CSV导出: 导出翻译数据为标准CSV格式
- Keyed目录转CSV: 将现有Keyed目录导出为CSV
- DefInjected目录转CSV: 将现有DefInjected目录导出为CSV
- 上下文信息控制: 可选择是否包含元数据
"""

import csv
import logging
from pathlib import Path
from typing import List

from colorama import Fore, Style
from core.extractors import extract_keyed_translations
from models.exceptions import ExportError, ValidationError
from models.result_models import OperationResult, OperationStatus, OperationType
from models.translation_data import TranslationData, TranslationType


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

    Raises:
        ValidationError: 翻译数据为空时抛出
        ExportError: CSV导出失败时抛出
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
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
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
        raise ExportError(error_msg) from e


def export_keyed_to_csv(keyed_dir: str, csv_path: str) -> OperationResult:
    """
    将Keyed目录导出为CSV

    Args:
        keyed_dir: Keyed目录路径
        csv_path: CSV文件路径

    Returns:
        操作结果

    Raises:
        ExportError: Keyed目录CSV导出失败时抛出
    """
    try:
        # 使用提取器获取Keyed翻译
        # 从Keyed目录的父目录提取
        mod_dir = str(Path(keyed_dir).parent.parent)
        language = Path(keyed_dir).parent.name

        translations = extract_keyed_translations(mod_dir, language)

        return export_to_csv(translations, csv_path, include_context=False)

    except Exception as e:
        error_msg = f"Keyed目录CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg) from e


def export_definjected_to_csv(definjected_dir: str, csv_path: str) -> OperationResult:
    """
    将DefInjected目录导出为CSV

    Args:
        definjected_dir: DefInjected目录路径
        csv_path: CSV文件路径

    Returns:
        操作结果

    Raises:
        ExportError: DefInjected目录CSV导出失败时抛出
    """
    try:
        # 使用提取器获取DefInjected翻译
        from core.extractors import extract_definjected_translations

        # 从DefInjected目录的父目录提取
        mod_dir = str(Path(definjected_dir).parent.parent)
        language = Path(definjected_dir).parent.name

        translations = extract_definjected_translations(mod_dir, language)

        return export_to_csv(translations, csv_path, include_context=True)

    except Exception as e:
        error_msg = f"DefInjected目录CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg) from e


# 导出函数列表
__all__ = [
    "export_to_csv",
    "export_keyed_to_csv",
    "export_definjected_to_csv",
]
