"""
翻译门面类模块
提供翻译操作的核心接口，管理模组翻译流程
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from colorama import Fore, Style

from .exceptions import TranslationError, TranslationImportError, ExportError
from day_translation.utils.config import get_config, ConfigError
from day_translation.extract.template_manager import TemplateManager
from day_translation.utils.machine_translate import translate_csv
from day_translation.corpus.parallel_corpus import generate_parallel_corpus
from day_translation.batch.batch_processor import BatchProcessor
from day_translation.java_translate.java_translator import JavaTranslator

CONFIG = get_config()

class TranslationFacade:
    """翻译操作的核心接口，管理模组翻译流程"""
    
    def __init__(self, mod_dir: str, language: str = CONFIG.default_language,
                 template_location: str = "mod"):
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
            self.mod_dir = str(Path(mod_dir).resolve())
            if not os.path.isdir(self.mod_dir):
                raise TranslationImportError(f"无效的模组目录: {mod_dir}")
            
            self.language = language
            self.template_location = template_location
            # 直接使用传入的目录初始化模板管理器
            self.template_manager = TemplateManager(self.mod_dir, language, template_location)
            self._validate_config()
            logging.debug("初始化 TranslationFacade: mod_dir=%s, language=%s", 
                         self.mod_dir, self.language)
        except Exception as e:
            raise ConfigError(f"初始化失败: {str(e)}") from e

    def _validate_config(self) -> None:
        """验证配置是否有效"""
        if not self.language:
            raise ConfigError("未指定目标语言")
        if not os.path.isdir(self.mod_dir):
            raise ConfigError(f"模组目录不存在: {self.mod_dir}")
        if not os.path.exists(os.path.join(self.mod_dir, "Languages")):
            logging.warning("模组目录中未找到 Languages 文件夹: %s", self.mod_dir)

    def extract_templates_and_generate_csv(self, output_dir: str, en_keyed_dir: Optional[str] = None, auto_choose_definjected: bool = False) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译模板并生成 CSV 文件
        """
        try:
            # 记录提取操作的开始，包含所有关键参数用于调试和审计
            logging.info("开始提取模板: output_dir=%s, en_keyed_dir=%s, auto_choose_definjected=%s", output_dir, en_keyed_dir, auto_choose_definjected)

            # 调用模板管理器执行核心提取操作
            # - output_dir: 输出目录，模板和CSV文件的保存位置
            # - en_keyed_dir: 英文Keyed目录，用于确保UI文本翻译完整性
            # - auto_choose_definjected: DefInjected提取方式选择（True=使用DefInjected目录，False=使用Defs扫描）
            translations = self.template_manager.extract_and_generate_templates(output_dir, en_keyed_dir, auto_choose_definjected)
            # 返回提取到的翻译数据列表，格式：[(key, text, group, file_info), ...]
            return translations
        except Exception as e:
            # 捕获并处理提取过程中的任何异常
            error_msg = f"提取模板失败: {str(e)}"           # 构建详细错误信息
            logging.error(error_msg)                        # 记录错误到日志文件
            raise ExportError(error_msg) from e                    # 抛出自定义异常，便于上层处理

    def import_translations_to_templates(self, csv_path: str, merge: bool = True) -> None:
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
            logging.info("导入翻译到模板: csv_path=%s, merge=%s", csv_path, merge)
            if not self.template_manager.import_translations(csv_path, merge):
                raise TranslationImportError("导入翻译失败")

        except Exception as e:
            error_msg = f"导入翻译失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationImportError(error_msg) from e

    def generate_corpus(self) -> List[Tuple[str, str]]:
        """
        生成英-中平行语料

        Returns:
            List[Tuple[str, str]]: 平行语料（英文, 中文）

        Raises:
            ExportError: 如果生成失败
        """
        try:
            logging.info("开始生成平行语料")
            # generate_parallel_corpus 函数签名：(mode: str, mod_dir: str) -> int
            # 使用模式 "2" 表示从 DefInjected 和 Keyed 提取
            corpus_count = generate_parallel_corpus("2", self.mod_dir)

            if not corpus_count:
                logging.warning("未找到任何平行语料")
                print(f"{Fore.YELLOW}⚠️ 未找到任何平行语料{Style.RESET_ALL}")
                return []
            else:
                print(f"{Fore.GREEN}✅ 生成语料：{corpus_count} 条{Style.RESET_ALL}")

            return []  # 这里可以返回实际的语料数据
        except Exception as e:
            error_msg = f"生成语料失败: {str(e)}"
            logging.error(error_msg)
            raise ExportError(error_msg) from e

    def machine_translate(self, csv_path: str, output_csv: Optional[str] = None) -> None:
        """
        使用阿里云机器翻译 CSV 文件

        Args:
            csv_path (str): 输入 CSV 文件路径
            output_csv (Optional[str]): 输出 CSV 文件路径，如果为 None 则自动生成

        Raises:
            TranslationError: 如果翻译失败
        """
        try:
            if not os.path.isfile(csv_path):
                raise TranslationError(f"CSV文件不存在: {csv_path}")

            # 如果没有指定输出文件，则自动生成
            if output_csv is None:
                input_path = Path(csv_path)
                output_csv = str(input_path.parent / f"{input_path.stem}_translated.csv")

            logging.info("开始机器翻译: csv_path=%s, output_csv=%s", csv_path, output_csv)
            
            # 调用机器翻译函数
            translate_csv(csv_path, output_csv)
            
            print(f"{Fore.GREEN}✅ 翻译完成：{output_csv}{Style.RESET_ALL}")
        except Exception as e:
            error_msg = f"机器翻译失败: {str(e)}"
            logging.error(error_msg)
            raise TranslationError(error_msg) from e

    def _get_api_key(self, key_name: str, user_config: Dict[str, Any]) -> str:
        """
        获取API密钥

        Args:
            key_name (str): 密钥名称
            user_config (Dict[str, Any]): 用户配置

        Returns:
            str: API密钥

        Raises:
            ConfigError: 如果密钥未配置
        """
        api_key = user_config.get(key_name)
        if not api_key:
            raise ConfigError(f"未配置 {key_name}，请在配置管理中设置")
        return api_key