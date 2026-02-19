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


# Python翻译器依赖通过try-except导入，这里不直接导入


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
            config = self._load_config_from_system()

        self.config = config
        self.factory = TranslatorFactory(self.config)

        # 缓存翻译器实例
        self._java_translator = None
        self._python_translator = None
        self._google_translator = None

    def _load_config_from_system(self) -> dict:
        """
        从配置系统加载配置

        Returns:
            dict: 配置字典
        """
        try:
            from user_config import UserConfigManager

            config_manager = UserConfigManager.get_instance()
            api_manager = config_manager.api_manager
            primary_api = api_manager.get_primary_api()

            if primary_api and primary_api.api_type == "aliyun":
                return {
                    "access_key_id": primary_api.get_value("access_key_id", ""),
                    "access_key_secret": primary_api.get_value("access_key_secret", ""),
                    "region_id": primary_api.get_value("region", "cn-hangzhou"),
                    "model_id": primary_api.get_value("model_id", 27345),
                    "sleep_sec": primary_api.get_value("sleep_sec", 0.5),
                    "enable_interrupt": primary_api.get_value("enable_interrupt", True),
                    "default_translator": "aliyun",
                }
            else:
                return {}
        except (ImportError, AttributeError, KeyError, ValueError) as e:
            self.logger.warning("从新配置系统获取配置失败: %s", e)
            return {}

    def translate_csv(
        self,
        input_csv: str,
        output_csv: Optional[str] = None,
        translator_type: str = "auto",
        **_kwargs,
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

            # 步骤1：保护
            placeholder_manager = self.factory.create_dictionary_translator("adult")
            success, placeholder_map, protected_text = (
                placeholder_manager.translate_csv(input_csv, mode="protect")
            )
            self.logger.info("保护后的占位符数据: %s", placeholder_map)
            if not success:
                raise RuntimeError("占位符保护失败")

            # 步骤2：选择翻译器
            translator = self._select_translator(translator_type)
            if not translator:
                raise RuntimeError(f"无法创建翻译器: {translator_type}")

            # 步骤3：执行机器翻译（若翻译器支持 placeholder_map 则每行翻译后立即恢复占位符，否则步骤4再整表恢复）
            success = translator.translate_csv(
                input_csv,
                output_csv,
                protected_text=protected_text,
                placeholder_map=placeholder_map,
            )

            # 步骤4：若翻译器未做行内恢复，则在此恢复占位符
            if success and getattr(translator, "restores_placeholders_per_row", False) is False:
                restore_success, _, _ = placeholder_manager.translate_csv(
                    output_csv, mode="restore", placeholder_map=placeholder_map
                )
                if restore_success:
                    self.logger.info("占位符恢复完成: %s", output_csv)
                else:
                    self.logger.warning("占位符恢复失败，但翻译已完成")
            elif success:
                self.logger.info("翻译成功完成: %s", output_csv)
            else:
                self.logger.warning("翻译未完成或被中断: %s", output_csv)
            return success

        except (FileNotFoundError, RuntimeError, ValueError, OSError) as e:
            error_msg = f"统一翻译失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            ui.print_error(error_msg)
            return False

    def _generate_output_path(self, input_csv: str) -> str:
        """
        生成输出文件路径：输入 xxx.csv → 输出 xxx_zh.csv（同一目录）

        Args:
            input_csv: 输入CSV文件路径

        Returns:
            str: 输出文件路径
        """
        input_path = Path(input_csv)
        output_name = input_path.stem + "_zh" + input_path.suffix
        return str(input_path.parent / output_name)

    def can_resume_translation(self, input_csv: str, output_csv: str) -> Optional[str]:
        """
        检查是否可以恢复翻译

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            Optional[str]: 可恢复的输出文件路径, 如果没有则返回None
        """
        try:
            for getter in (
                self._get_google_translator,
                self._get_java_translator,
                self._get_python_translator,
            ):
                translator = getter()
                if translator:
                    result = translator.can_resume_translation(input_csv, output_csv)
                    if result:
                        return result
            return None
        except (FileNotFoundError, PermissionError, RuntimeError) as e:
            self.logger.warning("检查恢复状态失败: %s", e)
            return None

    def resume_translation(
        self, input_csv: str, output_csv: str, protected_text: str
    ) -> bool:
        """
        恢复翻译任务

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            bool: 是否成功恢复
        """
        try:
            for getter in (
                self._get_google_translator,
                self._get_java_translator,
                self._get_python_translator,
            ):
                translator = getter()
                if translator and translator.can_resume_translation(input_csv, output_csv):
                    return translator.resume_translation(
                        input_csv, output_csv, protected_text
                    )
            ui.print_warning("当前无可用翻译器或无法恢复")
            return False
        except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as e:
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
            "google": self._get_google_status(),
            "java": self._get_java_status(),
            "python": self._get_python_status(),
        }

    def _select_translator(self, translator_type: str):
        """
        选择翻译器

        Args:
            translator_type: 翻译器类型 ("auto", "google", "java", "python")

        Returns:
            翻译器实例

        Raises:
            ValueError: 不支持的翻译器类型
        """
        if translator_type == "auto":
            # 自动选择：优先 Google（免费），其次 Java/阿里云，最后 Python/阿里云
            if self._is_google_available():
                return self._get_google_translator()
            if self._is_java_available():
                return self._get_java_translator()
            return self._get_python_translator()
        elif translator_type == "google":
            return self._get_google_translator()
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
            except (ImportError, FileNotFoundError, RuntimeError) as e:
                self.logger.debug("创建Java翻译器失败: %s", e)
                return None
        return self._java_translator

    def _get_python_translator(self):
        """获取Python翻译器实例"""
        if self._python_translator is None:
            try:
                self._python_translator = self.factory.create_python_translator()
            except (ImportError, FileNotFoundError, RuntimeError) as e:
                self.logger.debug("创建Python翻译器失败: %s", e)
                return None
        return self._python_translator

    def _get_google_translator(self):
        """获取 Google 免费翻译器实例"""
        if self._google_translator is None:
            try:
                self._google_translator = self.factory.create_google_translator()
            except (ImportError, FileNotFoundError, RuntimeError) as e:
                self.logger.debug("创建 Google 翻译器失败: %s", e)
                return None
        return self._google_translator

    def _is_google_available(self) -> bool:
        """检查 Google 翻译器是否可用"""
        try:
            status = self._get_google_status()
            return status.get("available", False)
        except (AttributeError, KeyError, RuntimeError):
            return False

    def _get_google_status(self) -> Dict[str, Any]:
        """获取 Google 翻译器状态"""
        try:
            translator = self._get_google_translator()
            if translator:
                return translator.get_status()
            return {"available": False, "reason": "无法创建 Google 翻译器"}
        except (AttributeError, KeyError, RuntimeError) as e:
            return {"available": False, "reason": str(e)}

    def _is_java_available(self) -> bool:
        """检查Java翻译器是否可用"""
        try:
            status = self._get_java_status()
            return status.get("available", False)
        except (AttributeError, KeyError, RuntimeError):
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
        except (AttributeError, KeyError, RuntimeError) as e:
            return {"available": False, "reason": str(e)}

    def _get_python_status(self) -> Dict[str, Any]:
        """获取Python翻译器状态"""
        try:
            # 通过工厂获取Python翻译器状态
            python_translator = self._get_python_translator()
            if python_translator:
                return python_translator.get_status()
            else:
                return {"available": False, "reason": "无法创建Python翻译器"}
        except (AttributeError, KeyError, RuntimeError) as e:
            return {"available": False, "reason": str(e)}
