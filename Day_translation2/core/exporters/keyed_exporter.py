"""
Day Translation 2 - Keyed翻译导出模块

负责Keyed类型翻译数据的导出功能。
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

from .xml_generators import generate_keyed_xml

CONFIG = config_service.get_unified_config()


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

        # 按文件路径分组
        file_groups: Dict[str, List[TranslationData]] = {}
        for translation in keyed_translations:
            file_path = translation.file_path or "Keyed.xml"
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(translation)

        exported_files = []

        # 为每个文件组生成XML
        for file_path, group_translations in file_groups.items():
            try:
                output_file = keyed_dir / file_path
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # 生成XML内容
                xml_content = generate_keyed_xml(group_translations)

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
        from ..extractors import extract_keyed_translations

        # 从Keyed目录的父目录提取
        mod_dir = str(Path(keyed_dir).parent.parent)
        language = Path(keyed_dir).parent.name

        translations = extract_keyed_translations(mod_dir, language)

        # 使用CSV导出模块
        from .csv_exporter import export_to_csv

        return export_to_csv(translations, csv_path, include_context=False)

    except Exception as e:
        error_msg = f"Keyed目录CSV导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg)
