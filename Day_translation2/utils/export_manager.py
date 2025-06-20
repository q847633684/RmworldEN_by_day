"""
Day Translation 2 - 导出管理器

从day_translation迁移并增强的导出功能管理。
支持智能合并、备份、增量更新等高级导出策略。
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from ..models.exceptions import ExportError, ProcessingError, ValidationError
    from ..models.translation_data import TranslationData
    from .filter_rules import AdvancedFilterRules
    from .xml_processor import AdvancedXMLProcessor
except ImportError:
    # 备用导入方式
    import sys

    current_dir = Path(__file__).parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

    try:
        from models.exceptions import ExportError, ProcessingError, ValidationError
        from models.translation_data import TranslationData
        from utils.filter_rules import AdvancedFilterRules
        from utils.xml_processor import AdvancedXMLProcessor
    except ImportError:
        # 如果仍无法导入，定义临时异常类用于独立运行
        class ProcessingError(Exception):
            pass

        class ValidationError(Exception):
            pass

        class ExportError(Exception):
            pass

        class AdvancedFilterRules:
            pass

        class AdvancedXMLProcessor:
            pass

        class TranslationData:
            pass


class ExportMode(Enum):
    """导出模式枚举"""

    REPLACE = "replace"  # 替换模式：删除现有文件，重新生成
    MERGE = "merge"  # 合并模式：保留现有翻译，仅更新新内容
    SMART_MERGE = "smart-merge"  # 智能合并：扫描XML内容，智能合并
    BACKUP = "backup"  # 备份模式：备份现有文件后替换
    INCREMENTAL = "incremental"  # 增量更新：只更新有变化的文件
    PREVIEW = "preview"  # 预览模式：先预览变化再确认
    SKIP = "skip"  # 跳过模式：不做任何操作


@dataclass
class ExportResult:
    """导出结果数据类"""

    success: bool
    mode: ExportMode
    files_processed: int = 0
    files_created: int = 0
    files_updated: int = 0
    files_backed_up: int = 0
    translations_added: int = 0
    translations_updated: int = 0
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ExportManager:
    """导出管理器 - 负责翻译文件的导出和合并"""

    def __init__(self):
        """初始化导出管理器"""
        self.xml_processor = AdvancedXMLProcessor()
        self.filter_rules = AdvancedFilterRules()

    def export_translations(
        self,
        translations: Dict[str, str],
        output_file_path: str,
        mode: ExportMode = ExportMode.REPLACE,
        preserve_manual_edits: bool = True,
    ) -> ExportResult:
        """
        导出翻译数据到文件

        Args:
            translations: 翻译数据字典 {key: translation}
            output_file_path: 输出文件路径
            mode: 导出模式
            preserve_manual_edits: 是否保留手动编辑

        Returns:
            ExportResult: 导出结果
        """
        try:
            result = ExportResult(success=False, mode=mode)

            # 验证输入参数
            if not translations:
                raise ValidationError("翻译数据不能为空")

            if not output_file_path:
                raise ValidationError("输出文件路径不能为空")

            # 确保输出目录存在
            output_dir = Path(output_file_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # 根据模式执行不同的导出逻辑
            if mode == ExportMode.SMART_MERGE:
                result = self._export_with_smart_merge(
                    translations, output_file_path, preserve_manual_edits
                )
            elif mode == ExportMode.MERGE:
                result = self._export_with_merge(translations, output_file_path)
            elif mode == ExportMode.BACKUP:
                result = self._export_with_backup(translations, output_file_path)
            elif mode == ExportMode.REPLACE:
                result = self._export_with_replace(translations, output_file_path)
            elif mode == ExportMode.SKIP:
                result.success = True
                result.warnings.append("跳过导出操作")
            else:
                raise ValidationError(f"不支持的导出模式: {mode}")

            result.mode = mode
            return result

        except Exception as e:
            logging.error(f"导出翻译失败: {e}")
            return ExportResult(success=False, mode=mode, errors=[str(e)])

    def _export_with_smart_merge(
        self,
        translations: Dict[str, str],
        output_file_path: str,
        preserve_manual_edits: bool = True,
    ) -> ExportResult:
        """使用智能合并模式导出"""
        result = ExportResult(success=False, mode=ExportMode.SMART_MERGE)

        try:
            # 使用XML处理器的智能合并功能
            success = self.xml_processor.smart_merge_xml_translations(
                output_file_path, translations, preserve_manual_edits
            )

            result.success = success
            result.files_processed = 1

            if os.path.exists(output_file_path):
                result.files_updated = 1
            else:
                result.files_created = 1

            result.translations_added = len(translations)

            logging.info(f"智能合并导出完成: {output_file_path}")

        except Exception as e:
            result.errors.append(f"智能合并失败: {e}")
            logging.error(f"智能合并导出失败: {e}")

        return result

    def _export_with_merge(
        self, translations: Dict[str, str], output_file_path: str
    ) -> ExportResult:
        """使用传统合并模式导出"""
        result = ExportResult(success=False, mode=ExportMode.MERGE)

        try:
            if os.path.exists(output_file_path):
                # 文件存在，执行合并
                tree = self.xml_processor.parse_xml(output_file_path)
                if tree:
                    updated = self.xml_processor.update_translations(
                        tree, translations, merge=True
                    )
                    if updated:
                        success = self.xml_processor.save_xml(tree, output_file_path)
                        result.success = success
                        result.files_updated = 1
                    else:
                        result.errors.append("更新翻译失败")
                else:
                    result.errors.append("解析现有XML文件失败")
            else:
                # 文件不存在，创建新文件
                success = self._create_new_xml_file(output_file_path, translations)
                result.success = success
                result.files_created = 1

            result.files_processed = 1
            result.translations_added = len(translations)

        except Exception as e:
            result.errors.append(f"合并导出失败: {e}")
            logging.error(f"合并导出失败: {e}")

        return result

    def _export_with_backup(
        self, translations: Dict[str, str], output_file_path: str
    ) -> ExportResult:
        """使用备份模式导出"""
        result = ExportResult(success=False, mode=ExportMode.BACKUP)

        try:
            if os.path.exists(output_file_path):
                # 备份现有文件
                backup_success = self._backup_file(output_file_path)
                if backup_success:
                    result.files_backed_up = 1
                else:
                    result.warnings.append("备份失败，继续执行替换")

            # 执行替换
            replace_result = self._export_with_replace(translations, output_file_path)
            result.success = replace_result.success
            result.files_processed = replace_result.files_processed
            result.files_created = replace_result.files_created
            result.translations_added = replace_result.translations_added
            result.errors.extend(replace_result.errors)

        except Exception as e:
            result.errors.append(f"备份导出失败: {e}")
            logging.error(f"备份导出失败: {e}")

        return result

    def _export_with_replace(
        self, translations: Dict[str, str], output_file_path: str
    ) -> ExportResult:
        """使用替换模式导出"""
        result = ExportResult(success=False, mode=ExportMode.REPLACE)

        try:
            # 删除现有文件（如果存在）
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
                logging.info(f"删除现有文件: {output_file_path}")

            # 创建新文件
            success = self._create_new_xml_file(output_file_path, translations)
            result.success = success
            result.files_processed = 1
            result.files_created = 1
            result.translations_added = len(translations)

        except Exception as e:
            result.errors.append(f"替换导出失败: {e}")
            logging.error(f"替换导出失败: {e}")

        return result

    def _create_new_xml_file(
        self, xml_file_path: str, translations: Dict[str, str]
    ) -> bool:
        """创建新的XML翻译文件"""
        return self.xml_processor._create_new_xml_file(xml_file_path, translations)

    def _backup_file(self, file_path: str) -> bool:
        """备份文件"""
        try:
            import shutil
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"

            shutil.copy2(file_path, backup_path)
            logging.info(f"文件备份成功: {file_path} -> {backup_path}")
            return True

        except Exception as e:
            logging.error(f"备份文件失败: {e}")
            return False

    def batch_export_translations(
        self,
        translations_by_file: Dict[str, Dict[str, str]],
        mode: ExportMode = ExportMode.SMART_MERGE,
        preserve_manual_edits: bool = True,
    ) -> List[ExportResult]:
        """
        批量导出翻译文件

        Args:
            translations_by_file: 按文件分组的翻译数据 {file_path: {key: translation}}
            mode: 导出模式
            preserve_manual_edits: 是否保留手动编辑

        Returns:
            List[ExportResult]: 每个文件的导出结果
        """
        results = []

        for file_path, translations in translations_by_file.items():
            try:
                result = self.export_translations(
                    translations, file_path, mode, preserve_manual_edits
                )
                results.append(result)

                if result.success:
                    logging.info(f"批量导出成功: {file_path}")
                else:
                    logging.error(f"批量导出失败: {file_path}, 错误: {result.errors}")

            except Exception as e:
                error_result = ExportResult(
                    success=False, mode=mode, errors=[f"处理文件{file_path}时出错: {e}"]
                )
                results.append(error_result)
                logging.error(f"批量导出异常: {file_path}, 错误: {e}")

        return results

    def get_export_statistics(self, results: List[ExportResult]) -> Dict[str, Any]:
        """获取导出统计信息"""
        stats = {
            "total_files": len(results),
            "successful_files": sum(1 for r in results if r.success),
            "failed_files": sum(1 for r in results if not r.success),
            "files_created": sum(r.files_created for r in results),
            "files_updated": sum(r.files_updated for r in results),
            "files_backed_up": sum(r.files_backed_up for r in results),
            "translations_added": sum(r.translations_added for r in results),
            "translations_updated": sum(r.translations_updated for r in results),
            "total_errors": sum(len(r.errors) for r in results),
            "total_warnings": sum(len(r.warnings) for r in results),
        }

        return stats


# 兼容性函数，支持旧代码调用
def export_with_smart_merge(
    output_file_path: str, translations: Dict[str, str], merge_mode: str = "replace"
) -> bool:
    """
    兼容性函数：根据合并模式导出翻译文件

    Args:
        output_file_path: 输出文件路径
        translations: 翻译内容
        merge_mode: 合并模式 ("replace", "merge", "smart-merge", "backup")

    Returns:
        bool: 是否成功导出
    """
    try:
        # 转换字符串模式到枚举
        mode_map = {
            "replace": ExportMode.REPLACE,
            "merge": ExportMode.MERGE,
            "smart-merge": ExportMode.SMART_MERGE,
            "backup": ExportMode.BACKUP,
            "skip": ExportMode.SKIP,
        }

        mode = mode_map.get(merge_mode, ExportMode.REPLACE)

        # 使用导出管理器
        manager = ExportManager()
        result = manager.export_translations(translations, output_file_path, mode)

        return result.success

    except Exception as e:
        logging.error(f"兼容性导出函数失败: {e}")
        return False


# 导出主要接口
__all__ = [
    "ExportManager",
    "ExportMode",
    "ExportResult",
    "export_with_smart_merge",
]  # 兼容性函数
