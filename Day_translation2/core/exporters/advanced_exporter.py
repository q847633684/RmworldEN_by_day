"""
Day Translation 2 - 高级导出器类

高级导出器门面类，提供统一的接口来导出翻译数据。
遵循提示文件标准：具体异常类型、详细错误上下文、完整类型注解。

核心功能:
- CSV格式导出: 导出翻译数据为CSV格式
- XML格式导出: 支持Keyed和DefInjected格式
- 批量导出: 自定义配置批量导出
- 统计信息: 提供导出统计和状态监控
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.result_models import OperationResult, OperationStatus, OperationType
from models.translation_data import TranslationData, TranslationType
from services.config_service import config_service
from utils.export_manager import ExportManager

from .csv_exporter import export_to_csv
from .definjected_exporter import export_definjected
from .export_utils import export_all_with_advanced_features
from .keyed_exporter import export_keyed

CONFIG = config_service.get_unified_config()


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
            result = export_to_csv(translations, csv_path, include_context)
            self.logger.info(f"CSV导出完成: {csv_path}")
            return result

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

            result = export_keyed(keyed_translations, target_dir, self.language)
            self.logger.info(f"Keyed XML导出完成: {target_dir}")
            return result

        except Exception as e:
            self.logger.error(f"Keyed XML导出失败: {e}")
            return OperationResult(
                status=OperationStatus.FAILED,
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

            result = export_definjected(
                definjected_translations, target_dir, self.language
            )
            self.logger.info(f"DefInjected XML导出完成: {target_dir}")
            return result

        except Exception as e:
            self.logger.error(f"DefInjected XML导出失败: {e}")
            return OperationResult(
                status=OperationStatus.FAILED,
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

            total_success = sum(1 for r in results.values() if r.is_success)
            self.logger.info(f"批量导出完成: {total_success}/{len(results)} 成功")

        except Exception as e:
            self.logger.error(f"批量导出过程中出现错误: {e}")
            results["error"] = OperationResult(
                status=OperationStatus.FAILED,
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


# 导出类列表
__all__ = [
    "AdvancedExporter",
]
