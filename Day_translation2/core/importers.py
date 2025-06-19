"""
Day Translation 2 - 数据导入核心模块

负责将翻译数据导入到游戏模组的XML文件中，支持智能合并和备份。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。

核心功能:
- CSV翻译导入: 从CSV文件加载翻译数据
- XML文件更新: 批量更新模组中的XML文件
- 智能合并: 支持多种合并策略
- 备份机制: 导入前自动备份原文件
"""

import csv
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from colorama import Fore, Style

from ..config import get_config
from ..models.exceptions import ImportError as TranslationImportError
from ..models.exceptions import (ProcessingError, TranslationError,
                                 ValidationError)
from ..models.result_models import (OperationResult, OperationStatus,
                                    OperationType)
from ..models.translation_data import TranslationEntry, TranslationType
from ..utils.file_utils import get_language_folder_path
from ..utils.xml_processor import XMLProcessor

# 获取配置实例
CONFIG = get_config()


def load_translations_from_csv(csv_path: str) -> Dict[str, str]:
    """
    从CSV文件加载翻译数据

    Args:
        csv_path: CSV文件路径

    Returns:
        翻译字典: {key: translated_text}

    Raises:
        ValidationError: CSV文件不存在或格式错误
        ProcessingError: CSV读取失败
    """
    if not csv_path or not Path(csv_path).exists():
        raise ValidationError(f"CSV文件不存在: {csv_path}")

    try:
        translations: Dict[str, str] = {}

        with open(csv_path, "r", encoding="utf-8") as csvfile:
            # 自动检测CSV格式
            sample = csvfile.read(1024)
            csvfile.seek(0)

            # 尝试检测分隔符
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter if sniffer.has_header(sample) else ","

            reader = csv.DictReader(csvfile, delimiter=delimiter)

            # 验证必需的列
            required_columns = ["key", "target_text"]
            if not all(col in reader.fieldnames for col in required_columns):
                # 尝试常见的列名变体
                column_mapping = {
                    "key": ["key", "Key", "ID", "id"],
                    "target_text": [
                        "target_text",
                        "translated_text",
                        "translation",
                        "chinese",
                        "中文",
                    ],
                }

                actual_mapping = {}
                for req_col, variants in column_mapping.items():
                    for variant in variants:
                        if variant in reader.fieldnames:
                            actual_mapping[req_col] = variant
                            break

                    if req_col not in actual_mapping:
                        raise ValidationError(f"CSV文件缺少必需列: {req_col}")

                # 使用映射后的列名
                key_col = actual_mapping["key"]
                text_col = actual_mapping["target_text"]
            else:
                key_col = "key"
                text_col = "target_text"

            # 读取翻译数据
            row_count = 0
            for row_num, row in enumerate(reader, start=2):  # 从第2行开始（跳过表头）
                try:
                    key = row.get(key_col, "").strip()
                    text = row.get(text_col, "").strip()

                    if key and text:  # 只导入有效的翻译
                        translations[key] = text
                        row_count += 1

                except Exception as e:
                    logging.warning(f"跳过CSV第{row_num}行，数据格式错误: {str(e)}")
                    continue

            logging.info(f"从CSV文件加载了 {len(translations)} 条翻译")
            print(f"{Fore.GREEN}✅ 加载翻译: {len(translations)} 条{Style.RESET_ALL}")

            return translations

    except ValidationError:
        raise
    except Exception as e:
        error_msg = f"读取CSV文件失败: {str(e)}"
        logging.error(error_msg)
        raise ProcessingError(
            error_msg, context={"csv_path": csv_path, "operation": "load_translations_from_csv"}
        )


def import_translations(
    csv_path: str,
    mod_dir: str,
    language: str = CONFIG.core.default_language,
    merge: bool = True,
    backup: bool = True,
) -> OperationResult:
    """
    从CSV文件导入翻译到模组

    Args:
        csv_path: CSV文件路径
        mod_dir: 模组目录路径
        language: 目标语言
        merge: 是否合并现有翻译
        backup: 是否备份原文件

    Returns:
        操作结果

    Raises:
        ValidationError: 参数验证失败
        TranslationImportError: 导入失败
        ProcessingError: 处理过程出错
    """
    print(f"{Fore.GREEN}开始导入翻译到模组（{mod_dir}, 语言：{language}）...{Style.RESET_ALL}")

    # 参数验证
    if not csv_path or not Path(csv_path).exists():
        raise ValidationError(f"CSV文件不存在: {csv_path}")

    if not mod_dir or not Path(mod_dir).exists():
        raise ValidationError(f"模组目录不存在: {mod_dir}")

    try:
        # 加载翻译数据
        translations = load_translations_from_csv(csv_path)

        if not translations:
            logging.warning("CSV文件中没有有效的翻译数据")
            return OperationResult(
                success=False,
                operation_type=OperationType.IMPORT,
                message="CSV文件中没有有效的翻译数据",
                details={"csv_path": csv_path, "mod_dir": mod_dir},
            )

        # 更新XML文件
        result = update_all_xml(mod_dir, translations, language, merge, backup)

        if result.success:
            print(f"{Fore.GREEN}✅ 翻译导入完成{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ 翻译导入失败: {result.message}{Style.RESET_ALL}")

        return result

    except (ValidationError, TranslationImportError):
        raise
    except Exception as e:
        error_msg = f"导入翻译失败: {str(e)}"
        logging.error(error_msg)
        raise ProcessingError(
            error_msg,
            context={
                "csv_path": csv_path,
                "mod_dir": mod_dir,
                "language": language,
                "operation": "import_translations",
            },
        )


def update_all_xml(
    mod_dir: str,
    translations: Dict[str, str],
    language: str = CONFIG.core.default_language,
    merge: bool = True,
    backup: bool = True,
) -> OperationResult:
    """
    更新模组中所有XML文件的翻译

    Args:
        mod_dir: 模组目录路径
        translations: 翻译字典 {key: translated_text}
        language: 目标语言
        merge: 是否合并现有翻译
        backup: 是否备份原文件

    Returns:
        操作结果

    Raises:
        ValidationError: 参数验证失败
        ProcessingError: 更新过程出错
    """
    # 参数验证
    if not mod_dir or not Path(mod_dir).exists():
        raise ValidationError(f"模组目录不存在: {mod_dir}")

    if not translations:
        raise ValidationError("翻译数据不能为空")

    try:
        processor = XMLProcessor()
        language_dir = get_language_folder_path(language, mod_dir)
        language_path = Path(language_dir)

        if not language_path.exists():
            logging.warning(f"语言目录不存在: {language_path}")
            return OperationResult(
                success=False,
                operation_type=OperationType.IMPORT,
                message=f"语言目录不存在: {language_path}",
                details={"mod_dir": mod_dir, "language": language},
            )

        # 查找所有XML文件
        xml_files = list(language_path.rglob("*.xml"))

        if not xml_files:
            logging.warning(f"在语言目录中未找到XML文件: {language_path}")
            return OperationResult(
                success=False,
                operation_type=OperationType.IMPORT,
                message="在语言目录中未找到XML文件",
                details={"language_dir": str(language_path)},
            )

        updated_files = []
        skipped_files = []
        error_files = []
        backup_dir = None

        # 创建备份目录（如果启用备份）
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = language_path / f"backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            logging.info(f"创建备份目录: {backup_dir}")

        logging.info(f"开始更新 {len(xml_files)} 个XML文件")

        for xml_file in xml_files:
            try:
                # 备份原文件
                if backup and backup_dir:
                    backup_file = backup_dir / xml_file.relative_to(language_path)
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(xml_file, backup_file)

                # 解析XML文件
                tree = processor.parse_xml(str(xml_file))
                if tree is None:
                    skipped_files.append(str(xml_file))
                    logging.warning(f"跳过无效的XML文件: {xml_file}")
                    continue

                # 更新翻译
                updated = processor.update_translations(tree, translations, merge=merge)

                if updated:
                    # 保存更新后的文件
                    processor.save_xml(tree, str(xml_file))
                    updated_files.append(str(xml_file))
                    logging.debug(f"更新文件: {xml_file}")
                else:
                    skipped_files.append(str(xml_file))
                    logging.debug(f"跳过文件（无更新）: {xml_file}")

            except Exception as e:
                error_files.append(str(xml_file))
                logging.error(f"处理XML文件失败 {xml_file}: {str(e)}")
                continue

        # 生成操作结果
        success = len(updated_files) > 0
        total_files = len(xml_files)

        details = {
            "total_files": total_files,
            "updated_files": len(updated_files),
            "skipped_files": len(skipped_files),
            "error_files": len(error_files),
            "translations_count": len(translations),
            "language": language,
            "backup_dir": str(backup_dir) if backup_dir else None,
        }

        if success:
            message = f"成功更新 {len(updated_files)}/{total_files} 个XML文件"
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            message = f"未能更新任何XML文件（共 {total_files} 个文件）"
            print(f"{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")

        logging.info(f"XML更新完成: {message}")

        return OperationResult(
            success=success, operation_type=OperationType.IMPORT, message=message, details=details
        )

    except ValidationError:
        raise
    except Exception as e:
        error_msg = f"批量更新XML文件失败: {str(e)}"
        logging.error(error_msg)
        raise ProcessingError(
            error_msg,
            context={
                "mod_dir": mod_dir,
                "language": language,
                "translations_count": len(translations),
                "operation": "update_all_xml",
            },
        )


def import_translation_entries(
    entries: List[TranslationEntry], mod_dir: str, merge: bool = True, backup: bool = True
) -> OperationResult:
    """
    导入翻译条目到模组

    Args:
        entries: 翻译条目列表
        mod_dir: 模组目录路径
        merge: 是否合并现有翻译
        backup: 是否备份原文件

    Returns:
        操作结果
    """
    # 转换为字典格式
    translations = {entry.key: entry.target_text for entry in entries if entry.target_text}

    if not translations:
        return OperationResult(
            success=False,
            operation_type=OperationType.IMPORT,
            message="没有有效的翻译数据",
            details={"entries_count": len(entries)},
        )

    # 假设所有条目使用相同的语言（从第一个条目获取）
    language = (
        entries[0].context_info.get("language", CONFIG.core.default_language)
        if entries
        else CONFIG.core.default_language
    )

    return update_all_xml(mod_dir, translations, language, merge, backup)


def validate_translation_data(translations: Dict[str, str]) -> List[str]:
    """
    验证翻译数据的完整性

    Args:
        translations: 翻译字典

    Returns:
        验证问题列表
    """
    issues = []

    if not translations:
        issues.append("翻译数据为空")
        return issues

    # 检查空键或空值
    empty_keys = [k for k, v in translations.items() if not k.strip()]
    if empty_keys:
        issues.append(f"发现 {len(empty_keys)} 个空键")

    empty_values = [k for k, v in translations.items() if k.strip() and not v.strip()]
    if empty_values:
        issues.append(f"发现 {len(empty_values)} 个空翻译值")

    # 检查重复键（虽然字典本身不会有重复键，但可能在CSV中有重复）
    duplicate_count = len(translations)
    if duplicate_count != len(set(translations.keys())):
        issues.append("发现重复的翻译键")

    return issues
