"""
Day Translation 2 - 翻译门面类

翻译操作的核心接口，管理模组翻译流程，提供统一的高级API。
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from ..models.exceptions import TranslationError, ConfigError, ImportError, ExportError
from ..models.result_models import OperationResult, OperationStatus, OperationType
from ..config import get_config
from .template_manager import TemplateManager

class TranslationFacade:
    """翻译操作的核心接口，管理模组翻译流程"""
    
    def __init__(self, mod_dir: str, language: str = None, template_location: str = "mod"):
        """
        初始化 TranslationFacade

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言，默认为配置中的默认语言
            template_location (str): 模板位置，默认为 'mod'

        Raises:
            ConfigError: 如果配置无效
            ImportError: 如果模组目录无效
        """
        try:
            self.config = get_config()
            self.mod_dir = str(Path(mod_dir).resolve())
            if not os.path.isdir(self.mod_dir):
                raise ImportError(f"无效的模组目录: {mod_dir}")
                
            self.language = language or self.config.core.default_language
            self.template_location = template_location
            self.template_manager = TemplateManager(self.mod_dir, self.language, template_location)
            self._validate_config()
            
            logging.debug(f"初始化 TranslationFacade: mod_dir={self.mod_dir}, language={self.language}")
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

    def extract_templates_and_generate_csv(self, 
                                         output_dir: str, 
                                         en_keyed_dir: str = None, 
                                         auto_choose_definjected: bool = False, 
                                         structure_choice: str = "original", 
                                         merge_mode: str = "smart-merge") -> OperationResult:
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
                success_count=len(translations)
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
                errors=[str(e)]
            )

    def import_translations_to_templates(self, csv_path: str, merge: bool = True) -> OperationResult:
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
                raise ImportError(f"CSV文件不存在: {csv_path}")
                
            logging.info(f"导入翻译到模板: csv_path={csv_path}, merge={merge}")
            
            success = self.template_manager.import_translations(csv_path, merge)
            
            if success:
                return OperationResult(
                    status=OperationStatus.SUCCESS,
                    operation_type=OperationType.IMPORT,
                    message="翻译导入成功",
                    details={"csv_path": csv_path, "merge_mode": merge}
                )
            else:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    operation_type=OperationType.IMPORT,
                    message="翻译导入失败",
                    errors=["导入操作返回失败状态"]
                )
                
        except Exception as e:
            error_msg = f"导入翻译失败: {str(e)}"
            logging.error(error_msg)
            
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.IMPORT,
                message=error_msg,
                errors=[str(e)]
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
                self.mod_dir, 
                self.config.core.source_language, 
                self.language
            )
            
            result = OperationResult(
                status=OperationStatus.SUCCESS if corpus else OperationStatus.PARTIAL,
                operation_type=OperationType.GENERATION,
                message=f"生成语料：{len(corpus)} 条" if corpus else "未找到任何平行语料",
                processed_count=len(corpus) if corpus else 0,
                success_count=len(corpus) if corpus else 0
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
                errors=[str(e)]
            )

    def machine_translate(self, csv_path: str, output_csv: str = None) -> OperationResult:
        """
        使用阿里云翻译 CSV 文件

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (str): 输出 CSV 文件路径

        Returns:
            OperationResult: 操作结果
        """
        try:
            if not os.path.isfile(csv_path):
                raise ExportError(f"CSV文件不存在: {csv_path}")
                
            logging.info(f"开始机器翻译: csv_path={csv_path}, output_csv={output_csv}")
            
            # 这里需要导入机器翻译服务
            from ..services.machine_translate import translate_csv
            
            # 获取API密钥
            access_key_id = self._get_api_key("ALIYUN_ACCESS_KEY_ID")
            access_key_secret = self._get_api_key("ALIYUN_ACCESS_KEY_SECRET")
            
            # 确定输出文件路径
            final_output = output_csv or csv_path.replace(".csv", "_translated.csv")
            
            # 执行翻译
            translate_csv(
                csv_path,
                final_output,
                access_key_id,
                access_key_secret,
                self.config.core.source_language,
                self.language
            )
            
            return OperationResult(
                status=OperationStatus.SUCCESS,
                operation_type=OperationType.TRANSLATION,
                message="机器翻译完成",
                details={
                    "input_file": csv_path,
                    "output_file": final_output,
                    "source_language": self.config.core.source_language,
                    "target_language": self.language
                }
            )
            
        except Exception as e:
            error_msg = f"机器翻译失败: {str(e)}"
            logging.error(error_msg)
            
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.TRANSLATION,
                message=error_msg,
                errors=[str(e)]
            )

    def _get_api_key(self, key_name: str) -> str:
        """获取API密钥，支持从环境变量、配置文件或用户输入获取"""
        from colorama import Fore, Style
        
        key = self.config.get_api_key(key_name) or os.getenv(key_name)
        if not key:
            key = input(f"{Fore.CYAN}请输入 {key_name}:{Style.RESET_ALL} ").strip()
            if input(f"{Fore.YELLOW}保存到配置文件？[y/n]:{Style.RESET_ALL} ").lower() == 'y':
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
                    "target_language": self.language
                }
            )
            
            if issues:
                result.warnings.extend(issues)
            
            return result
            
        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                operation_type=OperationType.VALIDATION,
                message=f"验证失败: {str(e)}",
                errors=[str(e)]
            )
