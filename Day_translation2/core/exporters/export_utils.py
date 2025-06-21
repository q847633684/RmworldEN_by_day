"""
Day Translation 2 - 导出工具函数

提供智能导出、批量导出、用户交互等高级导出功能。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from colorama import Fore, Style

from services.config_service import config_service
from models.exceptions import ExportError
from models.result_models import OperationResult, OperationStatus, OperationType
from models.translation_data import TranslationData, TranslationType
from utils.export_manager import ExportManager, ExportMode
from utils.user_interaction import UserInteractionManager

CONFIG = config_service.get_unified_config()


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

    Raises:
        ExportError: 导出失败时抛出
    """
    try:
        print(f"{Fore.GREEN}🚀 启动智能导出流程...{Style.RESET_ALL}")

        # 创建导出管理器
        export_manager = ExportManager()

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
            print(f"{Fore.CYAN}📝 导出Keyed翻译 ({len(keyed_translations)} 条)...{Style.RESET_ALL}")
            # 转换为字典格式
            keyed_dict = {t.key: t.translated_text or t.original_text for t in keyed_translations}
            keyed_output_path = os.path.join(output_dir, "Keyed")
            os.makedirs(keyed_output_path, exist_ok=True)
            keyed_result = export_manager.export_translations(
                keyed_dict,
                os.path.join(keyed_output_path, "keyed_translations.xml"),
                mode=export_mode,
            )
            results.append(keyed_result)

        # 导出DefInjected翻译
        if definjected_translations:
            print(
                f"{Fore.CYAN}📝 导出DefInjected翻译 ({len(definjected_translations)} 条)...{Style.RESET_ALL}"
            )
            # 转换为字典格式
            definjected_dict = {
                t.key: t.translated_text or t.original_text for t in definjected_translations
            }
            definjected_output_path = os.path.join(output_dir, "DefInjected")
            os.makedirs(definjected_output_path, exist_ok=True)
            definjected_result = export_manager.export_translations(
                definjected_dict,
                os.path.join(definjected_output_path, "definjected_translations.xml"),
                mode=export_mode,
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
        raise ExportError(error_msg) from e


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

    Raises:
        ExportError: 导出失败时抛出
    """
    try:
        print(f"{Fore.GREEN}🚀 启动交互式导出流程...{Style.RESET_ALL}")

        # 创建用户交互管理器
        interaction_manager = UserInteractionManager()

        # 显示导出信息
        print(f"\n{Fore.CYAN}📊 导出信息:{Style.RESET_ALL}")
        print(f"目标目录: {output_dir}")
        print(f"目标语言: {language}")
        print(f"翻译数量: {len(translations)}")

        # 获取用户选择
        choice = interaction_manager.handle_existing_translations_choice(
            output_dir_path=output_dir, auto_mode="smart-merge"
        )

        if choice == ExportMode.SKIP:
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
            mode=choice.value,
            auto_mode=True,
        )

    except Exception as e:
        error_msg = f"交互式导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg) from e


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

    Raises:
        ExportError: 导出失败时抛出
    """
    try:
        print(f"{Fore.GREEN}🚀 启动批量智能导出流程...{Style.RESET_ALL}")

        total_groups = len(translation_groups)
        successful_groups = 0
        failed_groups = 0
        all_results = []

        for i, (translations, output_dir, language) in enumerate(translation_groups, 1):
            try:
                print(f"\n{Fore.CYAN}📦 处理第 {i}/{total_groups} 组翻译...{Style.RESET_ALL}")

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

                if result.is_success:
                    successful_groups += 1
                    print(f"{Fore.GREEN}✅ 第 {i} 组导出成功{Style.RESET_ALL}")
                else:
                    failed_groups += 1
                    print(f"{Fore.RED}❌ 第 {i} 组导出失败: {result.message}{Style.RESET_ALL}")

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
        raise ExportError(error_msg) from e


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

    Raises:
        ExportError: 导出失败时抛出
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
            return export_with_smart_merge(translations, output_dir, language, mode, auto_mode)

    except Exception as e:
        error_msg = f"高级导出失败: {str(e)}"
        logging.error(error_msg)
        raise ExportError(error_msg) from e


# 导出函数列表
__all__ = [
    "export_with_smart_merge",
    "export_with_user_interaction",
    "batch_export_with_smart_merge",
    "export_all_with_advanced_features",
]
