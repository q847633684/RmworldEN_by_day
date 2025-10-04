"""
统一翻译器
提供多种翻译方式的统一接口，自动选择最佳翻译器
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from utils.logging_config import get_logger
from utils.ui_style import ui

from .translator_factory import TranslatorFactory

# 翻译配置已迁移到新配置系统
from .python_translator import AcsClient, TranslateGeneralRequest


class UnifiedTranslator:
    """统一翻译器，自动选择最佳翻译方式"""

    def __init__(self, config: Optional[dict] = None):
        """
        初始化统一翻译器

        Args:
            config: 翻译配置，如果为None则使用默认配置
        """
        self.logger = get_logger(f"{__name__}.UnifiedTranslator")
        # 从新配置系统获取配置
        if config is None:
            try:
                from user_config import UserConfigManager

                config_manager = UserConfigManager()
                api_manager = config_manager.api_manager
                primary_api = api_manager.get_primary_api()

                if primary_api and primary_api.api_type == "aliyun":
                    config = {
                        "access_key_id": primary_api.get_value("access_key_id", ""),
                        "access_key_secret": primary_api.get_value(
                            "access_key_secret", ""
                        ),
                        "region_id": primary_api.get_value("region", "cn-hangzhou"),
                        "model_id": primary_api.get_value("model_id", 27345),
                        "sleep_sec": primary_api.get_value("sleep_sec", 0.5),
                        "enable_interrupt": primary_api.get_value(
                            "enable_interrupt", True
                        ),
                        "default_translator": "aliyun",
                    }
                else:
                    config = {}
            except Exception as e:
                self.logger.warning(f"从新配置系统获取配置失败: {e}")
                config = {}

        self.config = config
        self.factory = TranslatorFactory(self.config)

        # 缓存翻译器实例
        self._java_translator = None
        self._python_translator = None

    def translate_csv(
        self,
        input_csv: str,
        output_csv: Optional[str] = None,
        translator_type: str = "auto",
        **kwargs,
    ) -> bool:
        """
        统一翻译CSV文件接口

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径，如果为None则自动生成
            translator_type: 翻译器类型 ("auto", "java", "python")
            **kwargs: 其他参数（如API密钥等）

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 验证输入文件
            if not os.path.exists(input_csv):
                raise FileNotFoundError(f"输入CSV文件不存在: {input_csv}")

            # 自动生成输出路径
            if output_csv is None:
                input_path = Path(input_csv)
                output_csv = str(
                    input_path.parent / f"{input_path.stem}_translated.csv"
                )

            # 步骤1：预处理成人内容
            ui.print_info("🔍 检查成人内容...")
            temp_csv = input_csv
            try:
                from ..dictionary.dictionary_translator import DictionaryTranslator

                adult_translator = DictionaryTranslator("adult")

                # 创建临时文件用于成人内容翻译
                temp_csv = str(Path(input_csv).with_suffix(".temp_adult.csv"))
                adult_success = adult_translator.translate_csv_file(input_csv, temp_csv)

                if adult_success:
                    ui.print_success("✅ 成人内容预处理完成")
                    self.logger.info("成人内容预处理完成，使用临时文件: %s", temp_csv)
                else:
                    ui.print_warning("⚠️ 成人内容预处理失败，使用原始文件")
                    temp_csv = input_csv

            except Exception as e:
                self.logger.warning("成人内容预处理失败: %s，使用原始文件", e)
                temp_csv = input_csv

            self.logger.info(
                "开始统一翻译: input=%s, output=%s, type=%s",
                temp_csv,
                output_csv,
                translator_type,
            )

            # 步骤2：选择翻译器
            translator = self._select_translator(translator_type)
            if not translator:
                raise RuntimeError(f"无法创建翻译器: {translator_type}")

            # 步骤3：执行机器翻译
            success = translator.translate_csv(temp_csv, output_csv, **kwargs)

            # 步骤4：清理临时文件
            if temp_csv != input_csv and Path(temp_csv).exists():
                try:
                    Path(temp_csv).unlink()
                    self.logger.debug("已清理临时文件: %s", temp_csv)
                except Exception as e:
                    self.logger.warning("清理临时文件失败: %s", e)

            if success:
                self.logger.info("翻译成功完成: %s", output_csv)
            else:
                self.logger.warning("翻译未完成或被中断: %s", output_csv)

            return success

        except Exception as e:
            error_msg = f"统一翻译失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            ui.print_error(error_msg)
            return False

    def can_resume_translation(self, input_csv: str) -> Optional[str]:
        """
        检查是否可以恢复翻译

        Args:
            input_csv: 输入CSV文件路径

        Returns:
            Optional[str]: 可恢复的输出文件路径，如果没有则返回None
        """
        try:
            # 优先检查Java翻译器
            java_translator = self._get_java_translator()
            if java_translator:
                return java_translator.can_resume_translation(input_csv)

            # TODO: 为Python翻译器添加恢复功能
            return None

        except Exception as e:
            self.logger.debug("检查恢复状态失败: %s", e)
            return None

    def resume_translation(self, input_csv: str, output_csv: str) -> bool:
        """
        恢复翻译任务

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            bool: 是否成功恢复
        """
        try:
            java_translator = self._get_java_translator()
            if java_translator:
                return java_translator.resume_translation(input_csv, output_csv)

            # TODO: 为Python翻译器添加恢复功能
            ui.print_warning("当前翻译器不支持恢复功能")
            return False

        except Exception as e:
            error_msg = f"恢复翻译失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            ui.print_error(error_msg)
            return False

    def get_available_translators(self) -> Dict[str, Dict[str, Any]]:
        """
        获取可用的翻译器信息

        Returns:
            Dict[str, Dict[str, Any]]: 翻译器状态信息
        """
        return {
            "java": self._get_java_status(),
            "python": self._get_python_status(),
        }

    def _select_translator(self, translator_type: str):
        """选择翻译器"""
        if translator_type == "auto":
            # 自动选择：优先Java，回退Python
            if self._is_java_available():
                return self._get_java_translator()
            else:
                return self._get_python_translator()
        elif translator_type == "java":
            return self._get_java_translator()
        elif translator_type == "python":
            return self._get_python_translator()
        else:
            raise ValueError(f"不支持的翻译器类型: {translator_type}")

    def _get_java_translator(self):
        """获取Java翻译器实例"""
        if self._java_translator is None:
            try:
                self._java_translator = self.factory.create_java_translator()
            except Exception as e:
                self.logger.debug("创建Java翻译器失败: %s", e)
                return None
        return self._java_translator

    def _get_python_translator(self):
        """获取Python翻译器实例"""
        if self._python_translator is None:
            try:
                self._python_translator = self.factory.create_python_translator()
            except Exception as e:
                self.logger.debug("创建Python翻译器失败: %s", e)
                return None
        return self._python_translator

    def _is_java_available(self) -> bool:
        """检查Java翻译器是否可用"""
        try:
            translator = self._get_java_translator()
            return translator is not None
        except Exception:
            return False

    def _get_java_status(self) -> Dict[str, Any]:
        """获取Java翻译器状态"""
        try:
            translator = self._get_java_translator()
            if translator:
                status = translator.get_status()
                # 转换Java翻译器状态格式为统一格式
                return {
                    "available": status.get("java_available", False)
                    and status.get("jar_exists", False),
                    "reason": (
                        "Java翻译器可用"
                        if (
                            status.get("java_available", False)
                            and status.get("jar_exists", False)
                        )
                        else "Java环境或JAR文件不可用"
                    ),
                    "java_available": status.get("java_available", False),
                    "jar_exists": status.get("jar_exists", False),
                    "jar_path": status.get("jar_path", None),
                }
            else:
                return {"available": False, "reason": "无法创建Java翻译器"}
        except Exception as e:
            return {"available": False, "reason": str(e)}

    def _get_python_status(self) -> Dict[str, Any]:
        """获取Python翻译器状态"""
        try:
            # 检查Python翻译依赖
            return {
                "available": AcsClient is not None
                and TranslateGeneralRequest is not None,
                "reason": "Python翻译器可用" if AcsClient else "阿里云SDK未安装",
            }
        except Exception as e:
            return {"available": False, "reason": str(e)}
