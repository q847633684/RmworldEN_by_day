"""
翻译门面类模块
提供翻译操作的核心接口，管理模组翻译流程
"""

import csv
import os
from pathlib import Path
from typing import List, Tuple, Optional
from utils.logging_config import (
    get_logger,
)
from utils.ui_style import ui

from .exceptions import TranslationError, TranslationImportError, ExportError
from utils.config import get_config, ConfigError
from extract.workflow import TemplateManager
from translate import UnifiedTranslator
from corpus.parallel_corpus import generate_parallel_corpus

CONFIG = get_config()


class TranslationFacade:
    """翻译操作的核心接口，管理模组翻译流程"""

    def __init__(
        self,
        mod_dir: str,
        language: str,
        template_location: str = "mod",
    ):
        """
        初始化 TranslationFacade

        Args:
            mod_dir (str): 模组目录路径（已经是最终目录，可能是根目录或版本号子目录）
            language (str): 目标语言，默认为 CONFIG.default_language
            template_location (str): 模板位置，默认为 'mod'

        Raises:
            ConfigError: 如果配置无效
            ImportError: 如果模组目录无效
        """
        try:
            self.logger = get_logger(f"{__name__}.TranslationFacade")

            self.mod_dir = str(Path(mod_dir).resolve())
            if not os.path.isdir(self.mod_dir):
                raise TranslationImportError(f"无效的模组目录: {mod_dir}")

            self.language = language
            self.template_location = template_location
            # 直接使用传入的目录初始化模板管理器
            # TemplateManager 当前无构造参数，按需实例化
            self.template_manager = TemplateManager()
            self._validate_config()

            self.logger.debug(
                "初始化TranslationFacade: mod_dir=%s, language=%s",
                self.mod_dir,
                self.language,
            )
        except (OSError, IOError, ValueError, ImportError) as e:
            raise ConfigError(f"初始化失败: {str(e)}") from e

    def _validate_config(self) -> None:
        """验证配置是否有效"""
        if not self.language:
            raise ConfigError("未指定目标语言")
        if not os.path.isdir(self.mod_dir):
            raise ConfigError(f"模组目录不存在: {self.mod_dir}")
        if not os.path.exists(os.path.join(self.mod_dir, "Languages")):
            self.logger.warning("模组目录中未找到 Languages 文件夹: %s", self.mod_dir)

    def extract_templates_and_generate_csv(
        self,
        output_dir: str,
        en_keyed_dir: Optional[str] = None,
        auto_choose_definjected: bool = False,
        data_source_choice: str = None,
        template_structure: str = None,
    ) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译模板并生成 CSV 文件
        """
        try:
            # 记录提取操作的开始，包含所有关键参数用于调试和审计
            self.logger.info(
                "开始提取模板: output_dir=%s, en_keyed_dir=%s, auto_choose_definjected=%s, data_source_choice=%s",
                output_dir,
                en_keyed_dir,
                auto_choose_definjected,
                data_source_choice,
            )

            # 调用模板管理器执行核心提取操作
            # - output_dir: 输出目录，模板和CSV文件的保存位置
            # - en_keyed_dir: 英文Keyed目录，用于确保UI文本翻译完整性
            # - data_source_choice: 数据来源选择（'definjected_only', 'defs_only', 'both'）
            # 如果传入了data_source_choice，直接使用；否则根据auto_choose_definjected转换
            translations = self.template_manager.extract_and_generate_templates(
                output_dir, en_keyed_dir, data_source_choice, template_structure
            )
            # 返回提取到的翻译数据列表，格式：[(key, text, group, file_info), ...]
            return translations
        except (OSError, IOError, ValueError, RuntimeError, ImportError) as e:
            # 捕获并处理提取过程中的任何异常
            error_msg = f"提取模板失败: {str(e)}"  # 构建详细错误信息
            self.logger.error(error_msg)  # 记录错误到日志文件
            raise ExportError(error_msg) from e  # 抛出自定义异常，便于上层处理

    def import_translations_to_templates(
        self, csv_path: str, merge: bool = True
    ) -> None:
        """
        将翻译后的 CSV 导入翻译模板

        Args:
            csv_path (str): 翻译 CSV 文件路径
            merge (bool): 是否合并现有翻译

        Raises:
            ImportError: 如果导入失败
        """
        try:
            if not os.path.isfile(csv_path):
                raise TranslationImportError(f"CSV文件不存在: {csv_path}")
            self.logger.info("导入翻译到模板: csv_path=%s, merge=%s", csv_path, merge)
            # 使用导入模块执行导入逻辑
            from import_template.importers import import_translations

            if not import_translations(
                csv_path=csv_path,
                mod_dir=self.mod_dir,
                merge=merge,
                auto_create_templates=True,
                language=self.language,
            ):
                raise TranslationImportError("导入翻译失败")

        except (OSError, IOError, ValueError, RuntimeError, csv.Error) as e:
            error_msg = f"导入翻译失败: {str(e)}"
            self.logger.error(error_msg)
            raise TranslationImportError(error_msg) from e

    def generate_corpus(self, mode: str = "2") -> List[Tuple[str, str]]:
        """
        生成英-中平行语料

        Args:
            mode: 生成模式 ("1"=从XML注释提取, "2"=从DefInjected和Keyed提取)

        Returns:
            List[Tuple[str, str]]: 平行语料（英文, 中文）

        Raises:
            ExportError: 如果生成失败
        """
        try:
            self.logger.info("开始生成平行语料，模式: %s", mode)
            # generate_parallel_corpus 函数签名：(mode: str, mod_dir: str) -> int
            corpus_count = generate_parallel_corpus(mode, self.mod_dir)

            if not corpus_count:
                self.logger.warning("未找到任何平行语料")
                ui.print_warning("未找到任何平行语料")
                return []
            else:
                ui.print_success(f"生成语料：{corpus_count} 条")

            return []  # 这里可以返回实际的语料数据
        except (OSError, IOError, ValueError, RuntimeError) as e:
            error_msg = f"生成语料失败: {str(e)}"
            self.logger.error(error_msg)
            raise ExportError(error_msg) from e

    def machine_translate(
        self,
        csv_path: str,
        output_csv: Optional[str] = None,
        translator_type: str = "auto",
    ) -> None:
        """
        使用统一翻译接口翻译 CSV 文件

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (Optional[str]): 输出 CSV 文件路径，如果为 None 则自动生成
            translator_type (str): 翻译器类型 ("auto", "java", "python")

        Raises:
            TranslationError: 如果翻译失败
        """
        try:
            if not os.path.isfile(csv_path):
                raise TranslationError(f"CSV文件不存在: {csv_path}")

            # 如果没有指定输出文件，则自动生成
            if output_csv is None:
                input_path = Path(csv_path)
                output_csv = str(
                    input_path.parent / f"{input_path.stem}_translated.csv"
                )

            self.logger.info(
                "开始统一机器翻译: csv_path=%s, output_csv=%s, type=%s",
                csv_path,
                output_csv,
                translator_type,
            )

            # 使用统一翻译器
            translator = UnifiedTranslator()

            # 显示翻译方式信息
            available_translators = translator.get_available_translators()
            if translator_type == "auto":
                if available_translators.get("java", {}).get("available", False):
                    translator_name = "Java翻译器"
                    translator_features = "高性能，支持中断和恢复"
                else:
                    translator_name = "Python翻译器"
                    translator_features = "简单部署，稳定可靠"
            elif translator_type == "java":
                translator_name = "Java翻译器"
                translator_features = "高性能，支持中断和恢复"
            else:
                translator_name = "Python翻译器"
                translator_features = "简单部署，稳定可靠"

            ui.print_info(f"🚀 使用翻译方式: {translator_name}")
            ui.print_info(f"💡 特性: {translator_features}")

            success = translator.translate_csv(csv_path, output_csv, translator_type)

            if not success:
                # 检查是否是用户中断（通过检查是否有恢复文件）
                resume_file = translator.can_resume_translation(csv_path)
                if resume_file:
                    ui.print_warning("翻译已暂停，可以随时恢复")
                    ui.print_info(f"💡 恢复文件: {resume_file}")
                    return  # 用户中断是正常操作，不抛出异常
                else:
                    raise TranslationError("翻译失败")

            # 验证翻译是否真正完成
            if self._verify_translation_completion(csv_path, output_csv):
                ui.print_success(f"翻译完成：{output_csv}")
            else:
                ui.print_warning(f"翻译部分完成：{output_csv}")
                ui.print_info("可能因API限制或网络问题未完全翻译")
        except (
            OSError,
            IOError,
            ValueError,
            RuntimeError,
            ConnectionError,
            TimeoutError,
        ) as e:
            error_msg = f"机器翻译失败: {str(e)}"
            self.logger.error(error_msg)
            raise TranslationError(error_msg) from e

    def _verify_translation_completion(self, input_csv: str, output_csv: str) -> bool:
        """
        验证翻译是否真正完成

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            bool: 翻译是否真正完成
        """
        try:
            import csv

            # 检查输出文件是否存在
            if not os.path.exists(output_csv):
                return False

            # 统计输入和输出的行数
            input_rows = 0
            output_rows = 0
            translated_rows = 0

            # 统计输入行数
            with open(input_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                input_rows = sum(1 for _ in reader) - 1  # 减去表头

            # 统计输出行数和翻译行数
            with open(output_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    output_rows += 1
                    # 检查是否有翻译内容（translated列不为空且不等于原文）
                    if "translated" in row and row["translated"].strip():
                        if "text" in row and row["translated"] != row["text"]:
                            translated_rows += 1

            # 如果输出行数少于输入行数，说明翻译未完成
            if output_rows < input_rows:
                self.logger.warning(
                    "翻译未完成: 输入%d行，输出%d行", input_rows, output_rows
                )
                return False

            # 如果翻译行数太少，可能有问题
            translation_ratio = translated_rows / input_rows if input_rows > 0 else 0
            if translation_ratio < 0.1:  # 翻译率低于10%
                self.logger.warning("翻译率过低: %.1f%%", translation_ratio * 100)
                return False

            self.logger.info(
                "翻译验证通过: 输入%d行，输出%d行，翻译%d行 (%.1f%%)",
                input_rows,
                output_rows,
                translated_rows,
                translation_ratio * 100,
            )
            return True

        except (OSError, IOError, csv.Error, UnicodeDecodeError) as e:
            self.logger.error("验证翻译完成状态失败: %s", e)
            return False  # 验证失败时保守处理

    def can_resume_translation(self, csv_path: str) -> Optional[str]:
        """
        检查是否可以恢复翻译

        Args:
            csv_path (str): 输入 CSV 文件路径

        Returns:
            Optional[str]: 可恢复的输出文件路径，如果没有则返回None
        """
        try:
            translator = UnifiedTranslator()
            return translator.can_resume_translation(csv_path)
        except (OSError, IOError, RuntimeError) as e:
            self.logger.debug("检查恢复状态失败: %s", e)
            return None

    def resume_translation(self, csv_path: str, output_csv: str) -> bool:
        """
        恢复翻译任务

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (str): 输出 CSV 文件路径

        Returns:
            bool: 是否成功恢复
        """
        try:
            translator = UnifiedTranslator()
            success = translator.resume_translation(csv_path, output_csv)

            if success:
                ui.print_success(f"恢复翻译完成：{output_csv}")
            else:
                ui.print_warning("恢复翻译失败或被中断")

            return success
        except (OSError, IOError, RuntimeError, ValueError) as e:
            error_msg = f"恢复翻译失败: {str(e)}"
            self.logger.error(error_msg)
            ui.print_error(error_msg)
            return False

    def get_translator_status(self) -> dict:
        """
        获取翻译器状态信息

        Returns:
            dict: 翻译器状态信息
        """
        try:
            translator = UnifiedTranslator()
            return translator.get_available_translators()
        except (OSError, IOError, RuntimeError, AttributeError) as e:
            self.logger.error("获取翻译器状态失败: %s", e)
            return {"error": str(e)}

    def extract_all_translations(
        self,
        data_source_choice: str = "defs",
        direct_dir: Optional[str] = None,
    ):
        """
        提取所有翻译数据的公共接口

        Args:
            data_source_choice (str): 数据来源选择 ('definjected_only', 'defs_only')
            direct_dir (Optional[str]): 直接指定DefInjected目录路径，用于从输出目录提取现有翻译

        Returns:
            根据 direct_dir 自动判断返回格式：
            - direct_dir=None: 返回四元组 (key, test, tag, rel_path) - 用于输入数据
            - direct_dir=指定路径: 返回五元组 (key, test, tag, rel_path, en_test) - 用于输出数据

        Raises:
            TranslationError: 提取失败时抛出
        """
        try:
            return self.template_manager.extract_all_translations(
                data_source_choice, direct_dir
            )
        except (OSError, IOError, ValueError, RuntimeError) as e:
            error_msg = f"提取翻译数据失败: {str(e)}"
            self.logger.error(error_msg)
            raise TranslationError(error_msg) from e
