"""
翻译器工厂
负责创建和管理不同类型的翻译器实例
"""

from typing import Optional
from utils.logging_config import get_logger
from .translation_config import TranslationConfig
from .java_translator import JavaTranslator
from .python_translator import translate_csv, AcsClient, TranslateGeneralRequest


class TranslatorFactory:
    """翻译器工厂类"""

    def __init__(self, config: TranslationConfig):
        """
        初始化翻译器工厂

        Args:
            config: 翻译配置
        """
        self.logger = get_logger(f"{__name__}.TranslatorFactory")
        self.config = config

    def create_java_translator(self):
        """创建Java翻译器实例"""
        try:
            return JavaTranslatorAdapter(JavaTranslator(), self.config)
        except ImportError as e:
            self.logger.debug("Java翻译器导入失败: %s", e)
            raise RuntimeError("Java翻译器不可用") from e
        except Exception as e:
            self.logger.debug("创建Java翻译器失败: %s", e)
            raise RuntimeError(f"创建Java翻译器失败: {str(e)}") from e

    def create_python_translator(self):
        """创建Python翻译器实例"""
        try:
            return PythonTranslatorAdapter(translate_csv, self.config)
        except ImportError as e:
            self.logger.debug("Python翻译器导入失败: %s", e)
            raise RuntimeError("Python翻译器不可用") from e
        except Exception as e:
            self.logger.debug("创建Python翻译器失败: %s", e)
            raise RuntimeError(f"创建Python翻译器失败: {str(e)}") from e


class JavaTranslatorAdapter:
    """Java翻译器适配器"""

    def __init__(self, java_translator, config: TranslationConfig):
        """
        初始化Java翻译器适配器

        Args:
            java_translator: Java翻译器实例
            config: 翻译配置
        """
        self.java_translator = java_translator
        self.config = config
        self.logger = get_logger(f"{__name__}.JavaTranslatorAdapter")

    def translate_csv(self, input_csv: str, output_csv: str, **kwargs) -> bool:
        """
        翻译CSV文件

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            **kwargs: 其他参数

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 从配置或kwargs中获取API密钥
            access_key_id = kwargs.get("access_key_id") or self.config.access_key_id
            access_key_secret = (
                kwargs.get("access_key_secret") or self.config.access_key_secret
            )

            if not access_key_id or not access_key_secret:
                self.logger.error("缺少阿里云API密钥")
                return False

            # 调用Java翻译器
            success = self.java_translator.translate_csv(
                input_csv,
                output_csv,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                model_id=kwargs.get("model_id", self.config.model_id),
                enable_interrupt=kwargs.get(
                    "enable_interrupt", self.config.enable_interrupt
                ),
                resume_line=kwargs.get("resume_line"),
            )

            self.logger.info("Java翻译完成: %s -> %s", input_csv, output_csv)
            return success

        except Exception as e:
            self.logger.error("Java翻译失败: %s", e, exc_info=True)
            return False

    def can_resume_translation(self, input_csv: str) -> Optional[str]:
        """检查是否可以恢复翻译"""
        try:
            return self.java_translator.can_resume_translation(input_csv)
        except Exception as e:
            self.logger.debug("检查恢复状态失败: %s", e)
            return None

    def resume_translation(self, input_csv: str, output_csv: str) -> bool:
        """恢复翻译"""
        try:
            return self.java_translator.resume_translation(input_csv, output_csv)
        except Exception as e:
            self.logger.error("恢复翻译失败: %s", e, exc_info=True)
            return False

    def get_status(self) -> dict:
        """获取翻译器状态"""
        try:
            return self.java_translator.get_status()
        except Exception as e:
            return {"available": False, "reason": str(e)}


class PythonTranslatorAdapter:
    """Python翻译器适配器"""

    def __init__(self, translate_func, config: TranslationConfig):
        """
        初始化Python翻译器适配器

        Args:
            translate_func: Python翻译函数
            config: 翻译配置
        """
        self.translate_func = translate_func
        self.config = config
        self.logger = get_logger(f"{__name__}.PythonTranslatorAdapter")

    def translate_csv(self, input_csv: str, output_csv: str, **kwargs) -> bool:
        """
        翻译CSV文件

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            **kwargs: 其他参数

        Returns:
            bool: 翻译是否成功
        """
        try:
            # 从配置或kwargs中获取API密钥
            access_key_id = kwargs.get("access_key_id") or self.config.access_key_id
            access_key_secret = (
                kwargs.get("access_key_secret") or self.config.access_key_secret
            )

            if not access_key_id or not access_key_secret:
                self.logger.error("缺少阿里云API密钥")
                return False

            # 调用Python翻译函数
            self.translate_func(
                input_csv,
                output_csv,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                **kwargs,
            )

            self.logger.info("Python翻译完成: %s -> %s", input_csv, output_csv)
            return True

        except Exception as e:
            self.logger.error("Python翻译失败: %s", e, exc_info=True)
            return False

    def can_resume_translation(self, input_csv: str) -> Optional[str]:
        """检查是否可以恢复翻译（Python翻译器暂不支持）"""
        return None

    def resume_translation(self, input_csv: str, output_csv: str) -> bool:
        """恢复翻译（Python翻译器暂不支持）"""
        return False

    def get_status(self) -> dict:
        """获取翻译器状态"""
        try:
            return {
                "available": AcsClient is not None
                and TranslateGeneralRequest is not None,
                "type": "python",
                "reason": "Python翻译器可用" if AcsClient else "阿里云SDK未安装",
            }
        except Exception as e:
            return {"available": False, "type": "python", "reason": str(e)}
