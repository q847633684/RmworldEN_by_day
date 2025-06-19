"""
Day Translation 2 - 翻译门面模式

提供统一的翻译操作接口，整合提取、翻译、导入等功能。
遵循提示文件标准：接口兼容、错误处理、渐进式迁移。
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import get_config
from ..models.exceptions import ConfigError
from ..models.exceptions import ImportError as TranslationImportError
from ..models.exceptions import TranslationError
from ..models.result_models import (OperationResult, OperationStatus,
                                    OperationType)
from .template_manager import TemplateManager


class TranslationFacade:
    """翻译门面类，提供统一的翻译操作接口"""

    def __init__(self, mod_dir: str, language: str = None, template_location: str = "mod"):
        """
        初始化 TranslationFacade

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言，默认为配置中的默认语言
            template_location (str): 模板位置，默认为 'mod'

        Raises:
            ConfigError: 如果配置无效
            TranslationImportError: 如果模组目录无效
        """
        try:
            self.config = get_config()
            self.mod_dir = str(Path(mod_dir).resolve())
            if not os.path.isdir(self.mod_dir):
                raise TranslationImportError(f"无效的模组目录: {mod_dir}")

            self.language = language or self.config.core.default_language
            self.template_location = template_location
            self.template_manager = TemplateManager(self.mod_dir, self.language, template_location)
            self._validate_config()

            logging.debug(
                f"初始化 TranslationFacade: mod_dir={self.mod_dir}, language={self.language}"
            )
        except Exception as e:
            raise ConfigError(f"初始化失败: {str(e)}")

    def _validate_config(self) -> None:
        """验证配置是否有效"""
        if not self.language:
            raise ConfigError("未指定目标语言")
        if not os.path.isdir(self.mod_dir):
            raise ConfigError(f"模组目录不存在: {self.mod_dir}")
        if not os.path.exists(os.path.join(self.mod_dir, "Languages")):
            logging.warning(f"模组目录中未找到 Languages 文件夹: {self.mod_dir}")

    def extract_templates_and_generate_csv(
        self,
        output_dir: str,
        en_keyed_dir: str = None,
        auto_choose_definjected: bool = False,
        structure_choice: str = "original",
        merge_mode: str = "smart-merge",
    ) -> OperationResult:
        """
        提取翻译模板并生成 CSV 文件

        Args:
            output_dir: 输出目录
            en_keyed_dir: 英文Keyed目录
            auto_choose_definjected: 是否自动选择DefInjected方式
            structure_choice: 结构选择
            merge_mode: 合并模式

        Returns:
            OperationResult: 操作结果
        """
        try:
            logging.info(f"开始提取模板: output_dir={output_dir}, en_keyed_dir={en_keyed_dir}")

            # 调用模板管理器执行核心提取操作
            translations = self.template_manager.extract_and_generate_templates(
                output_dir, en_keyed_dir, auto_choose_definjected, structure_choice, merge_mode
            )

            # 创建成功结果
            result = OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.EXTRACTION,
                message=f"提取完成：{len(translations)} 条翻译",
                processed_count=len(translations),
                success_count=len(translations),
            )

            result.details["output_dir"] = output_dir
            result.details["structure_choice"] = structure_choice
            result.details["merge_mode"] = merge_mode

            return result

        except Exception as e:
            error_msg = f"提取模板失败: {str(e)}"
            logging.error(error_msg)

            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.EXTRACTION,
                message=error_msg,
                errors=[str(e)],
            )

    def import_translations_to_templates(
        self, csv_path: str, merge: bool = True
    ) -> OperationResult:
        """
        将翻译后的 CSV 导入翻译模板

        Args:
            csv_path (str): 翻译 CSV 文件路径
            merge (bool): 是否合并现有翻译

        Returns:
            OperationResult: 操作结果
        """
        try:
            if not os.path.isfile(csv_path):
                raise TranslationImportError(f"CSV文件不存在: {csv_path}")

            logging.info(f"导入翻译到模板: csv_path={csv_path}, merge={merge}")

            success = self.template_manager.import_translations(csv_path, merge)

            if success:
                return OperationResult(
                    status=OperationStatus.SUCCESS,
                    operation_type=OperationType.IMPORT,
                    message="翻译导入成功",
                    details={"csv_path": csv_path, "merge_mode": merge},
                )
            else:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    operation_type=OperationType.IMPORT,
                    message="翻译导入失败",
                    errors=["导入操作返回失败状态"],
                )

        except Exception as e:
            error_msg = f"导入翻译失败: {str(e)}"
            logging.error(error_msg)

            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.IMPORT,
                message=error_msg,
                errors=[str(e)],
            )

    def generate_corpus(self) -> OperationResult:
        """
        生成英-中平行语料

        Returns:
            OperationResult: 操作结果，包含语料数据
        """
        try:
            logging.info("开始生成平行语料")

            # 这里需要导入语料生成服务
            from ..services.corpus_generator import generate_parallel_corpus

            corpus = generate_parallel_corpus(
                self.mod_dir, self.config.core.source_language, self.language
            )

            result = OperationResult(
                status=OperationStatus.SUCCESS if corpus else OperationStatus.PARTIAL,
                operation_type=OperationType.GENERATION,
                message=f"生成语料：{len(corpus)} 条" if corpus else "未找到任何平行语料",
                processed_count=len(corpus) if corpus else 0,
                success_count=len(corpus) if corpus else 0,
            )

            result.details["corpus_data"] = corpus

            if not corpus:
                result.warnings.append("未找到任何平行语料")

            return result

        except Exception as e:
            error_msg = f"生成语料失败: {str(e)}"
            logging.error(error_msg)

            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.GENERATION,
                message=error_msg,
                errors=[str(e)],
            )

    def machine_translate(self, csv_path: str, output_csv: str = None) -> OperationResult:
        """
        使用机器翻译处理 CSV 文件

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (str): 输出 CSV 文件路径

        Returns:
            OperationResult: 操作结果
        """
        try:
            if not os.path.isfile(csv_path):
                raise TranslationImportError(f"CSV文件不存在: {csv_path}")

            logging.info(f"开始机器翻译: csv_path={csv_path}, output_csv={output_csv}")

            # 获取API密钥
            access_key_id = self._get_api_key("ALIYUN_ACCESS_KEY_ID")
            access_key_secret = self._get_api_key("ALIYUN_ACCESS_KEY_SECRET")

            # 导入翻译服务
            from ..services.translation_service import translate_csv

            # 执行翻译
            translate_csv(
                csv_path,
                output_csv or csv_path.replace(".csv", "_translated.csv"),
                access_key_id,
                access_key_secret,
                self.config.core.source_language,
                self.language,
            )

            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.TRANSLATION,
                message="机器翻译完成",
                details={
                    "input_csv": csv_path,
                    "output_csv": output_csv or csv_path.replace(".csv", "_translated.csv"),
                },
            )

        except Exception as e:
            error_msg = f"机器翻译失败: {str(e)}"
            logging.error(error_msg)

            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.TRANSLATION,
                message=error_msg,
                errors=[str(e)],
            )

    def _get_api_key(self, key_name: str) -> str:
        """获取API密钥，支持从环境变量、配置文件或用户输入获取"""
        key = self.config.get_api_key(key_name) or os.getenv(key_name)
        if not key:
            from colorama import Fore, Style

            key = input(f"{Fore.CYAN}请输入 {key_name}: {Style.RESET_ALL}").strip()
            if input(f"{Fore.YELLOW}保存API密钥到配置？[y/n]: {Style.RESET_ALL}").lower() == "y":
                self.config.set_api_key(key_name, key)
                self.config.save_config()
                logging.debug(f"已保存 {key_name} 到用户配置文件")
        return key

    def validate_mod_structure(self) -> OperationResult:
        """
        验证模组目录结构

        Returns:
            OperationResult: 验证结果
        """
        try:
            issues = []

            # 检查基本目录结构
            languages_dir = os.path.join(self.mod_dir, "Languages")
            if not os.path.exists(languages_dir):
                issues.append("缺少 Languages 目录")

            # 检查英文目录
            english_dir = os.path.join(languages_dir, "English")
            if not os.path.exists(english_dir):
                issues.append("缺少 English 语言目录")

            # 检查目标语言目录
            target_dir = os.path.join(languages_dir, self.language)
            target_exists = os.path.exists(target_dir)

            result = OperationResult(
                status=OperationStatus.SUCCESS if not issues else OperationStatus.PARTIAL,
                operation_type=OperationType.VALIDATION,
                message="模组结构验证完成",
                details={
                    "mod_dir": self.mod_dir,
                    "languages_dir_exists": os.path.exists(languages_dir),
                    "english_dir_exists": os.path.exists(english_dir),
                    "target_dir_exists": target_exists,
                    "target_language": self.language,
                },
            )

            if issues:
                result.warnings.extend(issues)

            return result

        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.VALIDATION,
                message=f"验证失败: {str(e)}",
                errors=[str(e)],
            )

    def export_with_advanced_features(
        self,
        translations: List = None,
        output_dir: str = None,
        export_config: Optional[Dict[str, Any]] = None,
    ) -> OperationResult:
        """
        使用高级功能导出翻译

        Args:
            translations: 翻译数据列表，如果为None则提取当前模组的翻译
            output_dir: 输出目录，如果为None则使用模组目录
            export_config: 导出配置

        Returns:
            OperationResult: 操作结果
        """
        try:
            # 如果没有提供翻译数据，则提取当前模组的翻译
            if translations is None:
                from .extractors import extract_all_translations

                translations = extract_all_translations(self.mod_dir, self.language)

            # 如果没有提供输出目录，则使用模组目录
            if output_dir is None:
                output_dir = self.mod_dir

            # 导入高级导出功能
            from .exporters import export_all_with_advanced_features

            return export_all_with_advanced_features(
                translations=translations,
                output_dir=output_dir,
                language=self.language,
                export_config=export_config,
            )

        except Exception as e:
            error_msg = f"高级导出失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationError(
                error_msg,
                context={
                    "mod_dir": self.mod_dir,
                    "language": self.language,
                    "output_dir": output_dir,
                    "operation": "export_with_advanced_features",
                },
            )

    def export_with_smart_merge(
        self,
        translations: List = None,
        output_dir: str = None,
        mode: str = "smart-merge",
        auto_mode: bool = False,
    ) -> OperationResult:
        """
        使用智能合并模式导出翻译

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录
            mode: 导出模式
            auto_mode: 是否自动模式

        Returns:
            OperationResult: 操作结果
        """
        try:
            # 如果没有提供翻译数据，则提取当前模组的翻译
            if translations is None:
                from .extractors import extract_all_translations

                translations = extract_all_translations(self.mod_dir, self.language)

            # 如果没有提供输出目录，则使用模组目录
            if output_dir is None:
                output_dir = self.mod_dir

            # 导入智能导出功能
            from .exporters import export_with_smart_merge

            return export_with_smart_merge(
                translations=translations,
                output_dir=output_dir,
                language=self.language,
                mode=mode,
                auto_mode=auto_mode,
            )

        except Exception as e:
            error_msg = f"智能导出失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationError(
                error_msg,
                context={
                    "mod_dir": self.mod_dir,
                    "language": self.language,
                    "output_dir": output_dir,
                    "mode": mode,
                    "operation": "export_with_smart_merge",
                },
            )

    def export_with_user_interaction(
        self, translations: List = None, output_dir: str = None
    ) -> OperationResult:
        """
        使用用户交互模式导出翻译

        Args:
            translations: 翻译数据列表
            output_dir: 输出目录

        Returns:
            OperationResult: 操作结果
        """
        try:
            # 如果没有提供翻译数据，则提取当前模组的翻译
            if translations is None:
                from .extractors import extract_all_translations

                translations = extract_all_translations(self.mod_dir, self.language)

            # 如果没有提供输出目录，则使用模组目录
            if output_dir is None:
                output_dir = self.mod_dir

            # 导入交互式导出功能
            from .exporters import export_with_user_interaction

            return export_with_user_interaction(
                translations=translations, output_dir=output_dir, language=self.language
            )

        except Exception as e:
            error_msg = f"交互式导出失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationError(
                error_msg,
                context={
                    "mod_dir": self.mod_dir,
                    "language": self.language,
                    "output_dir": output_dir,
                    "operation": "export_with_user_interaction",
                },
            )

    def process_with_workflow_automation(self, workflow_config: Dict[str, Any]) -> OperationResult:
        """
        使用工作流自动化处理翻译

        Args:
            workflow_config: 工作流配置

        Returns:
            OperationResult: 操作结果
        """
        try:
            logging.info("开始自动化工作流程...")

            results = []
            workflow_steps = workflow_config.get("steps", [])

            for step_config in workflow_steps:
                step_type = step_config.get("type")
                step_params = step_config.get("params", {})

                logging.info(f"执行工作流步骤: {step_type}")

                if step_type == "extract":
                    result = self.extract_templates_and_generate_csv(**step_params)
                elif step_type == "translate":
                    result = self.translate_csv(**step_params)
                elif step_type == "import":
                    result = self.import_translations_to_templates(**step_params)
                elif step_type == "export_advanced":
                    result = self.export_with_advanced_features(**step_params)
                elif step_type == "export_smart":
                    result = self.export_with_smart_merge(**step_params)
                elif step_type == "export_interactive":
                    result = self.export_with_user_interaction(**step_params)
                elif step_type == "generate_corpus":
                    result = self.generate_corpus(**step_params)
                elif step_type == "validate":
                    result = self.validate_mod_structure()
                else:
                    raise TranslationError(f"未知的工作流步骤类型: {step_type}")

                results.append(result)

                # 如果步骤失败且配置要求停止，则中断工作流
                if not result.success and workflow_config.get("stop_on_failure", True):
                    break

            # 汇总结果
            successful_steps = sum(1 for r in results if r.success)
            total_steps = len(results)

            success = successful_steps == total_steps
            message = f"工作流完成: {successful_steps}/{total_steps} 步骤成功"

            return OperationResult(
                success=success,
                operation_type=OperationType.WORKFLOW,
                message=message,
                details={
                    "total_steps": total_steps,
                    "successful_steps": successful_steps,
                    "failed_steps": total_steps - successful_steps,
                    "workflow_config": workflow_config,
                    "step_results": [r.__dict__ for r in results],
                },
            )

        except Exception as e:
            error_msg = f"工作流自动化失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationError(
                error_msg,
                context={
                    "mod_dir": self.mod_dir,
                    "language": self.language,
                    "workflow_config": workflow_config,
                    "operation": "process_with_workflow_automation",
                },
            )
