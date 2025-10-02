"""
系统配置模块
管理翻译系统的核心配置参数
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Set, List, Dict, Any
from .base_config import BaseConfig
from utils.logging_config import get_logger


class SystemConfig(BaseConfig):
    """系统配置类 - 管理翻译系统的核心参数"""

    def __init__(self):
        super().__init__("系统配置")

        # 设置默认值 - 移除语言相关配置，这些已迁移到LanguageConfig
        self._defaults = {
            "version": "1.0.0",
            "log_format": "%(asctime)s - %(levelname)s - %(message)s",
            "debug_mode": True,
            "preview_translatable_fields": 0,
            "log_file": "",  # 动态生成
        }

        # 设置必需字段 - 移除语言相关字段
        self._required_fields = {
            "log_format",
        }

        # 设置字段类型 - 移除语言相关字段
        self._field_types = {
            "version": str,
            "log_format": str,
            "debug_mode": bool,
            "preview_translatable_fields": int,
            "log_file": str,
        }

        # 初始化数据
        self._data = self._defaults.copy()

        # 动态生成日志文件名
        if not self._data["log_file"]:
            self._generate_log_file_path()

        # 加载翻译字段规则
        self._load_translation_rules()

    def _generate_log_file_path(self):
        """动态生成日志文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_file = log_dir / f"day_translation_{timestamp}.log"
        self._data["log_file"] = str(log_file)

    def _load_translation_rules(self):
        """加载翻译字段规则"""
        try:
            # 尝试导入YAML
            try:
                import yaml
            except ImportError:
                self.logger.warning("YAML库未安装，使用默认翻译规则")
                self._set_default_translation_rules()
                return

            # 加载配置文件
            config_path = (
                Path(__file__).parent.parent / "config" / "translation_fields.yaml"
            )

            if not config_path.exists():
                self.logger.warning("翻译字段配置文件不存在，使用默认规则")
                self._set_default_translation_rules()
                return

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 提取字段规则
            self._data["translation_fields"] = self._extract_fields_from_categories(
                config.get("translation_fields", {}).get("categories", {})
            )
            self._data["ignore_fields"] = self._extract_fields_from_categories(
                config.get("ignore_fields", {}).get("categories", {})
            )
            self._data["non_text_patterns"] = list(
                self._extract_fields_from_categories(
                    config.get("non_text_patterns", {}).get("categories", {})
                )
            )

            self.logger.debug("翻译字段规则加载成功")

        except Exception as e:
            self.logger.error(f"加载翻译字段规则失败: {e}")
            self._set_default_translation_rules()

    def _extract_fields_from_categories(self, categories: Dict[str, Any]) -> Set[str]:
        """从分类中提取字段列表"""
        fields = set()
        for category_data in categories.values():
            if isinstance(category_data, dict) and "fields" in category_data:
                fields.update(category_data["fields"])
        return fields

    def _set_default_translation_rules(self):
        """设置默认翻译规则"""
        self._data["translation_fields"] = {
            "label",
            "description",
            "text",
            "message",
            "tooltip",
        }
        self._data["ignore_fields"] = {"defName", "id", "cost", "damage"}
        self._data["non_text_patterns"] = [
            r"^\d+$",  # 整数
            r"^-?\d+\.\d+$",  # 浮点数
            r"^[0-9a-fA-F]+$",  # 十六进制
            r"^\s*$",  # 纯空白
            r"^true$|^false$",  # 布尔值
        ]

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "version": {
                "type": "text",
                "description": "配置版本",
                "default": "1.0.0",
                "readonly": True,
            },
            "log_format": {
                "type": "text",
                "description": "日志格式",
                "default": "%(asctime)s - %(levelname)s - %(message)s",
                "required": True,
            },
            "debug_mode": {
                "type": "boolean",
                "description": "调试模式",
                "default": True,
            },
            "preview_translatable_fields": {
                "type": "number",
                "description": "预览可翻译字段数量",
                "default": 0,
                "min": 0,
                "integer": True,
            },
        }

    def validate(self) -> bool:
        """验证配置"""
        try:
            # 基础验证 - 检查必需字段
            if not self.is_complete():
                missing = self.get_missing_required_fields()
                self.logger.error(f"系统配置不完整，缺少字段: {missing}")
                return False

            # 特殊验证
            if self.get_value("preview_translatable_fields", 0) < 0:
                self.logger.error("preview_translatable_fields必须是非负整数")
                return False

            return True

        except Exception as e:
            self.logger.error(f"系统配置验证失败: {e}")
            return False

    def is_translation_field(self, field_name: str) -> bool:
        """判断字段是否需要翻译"""
        translation_fields = self.get_value("translation_fields", set())
        return field_name in translation_fields

    def is_ignore_field(self, field_name: str) -> bool:
        """判断字段是否需要忽略"""
        ignore_fields = self.get_value("ignore_fields", set())
        return field_name in ignore_fields

    def get_translation_fields(self) -> Set[str]:
        """获取需要翻译的字段集合"""
        return self.get_value("translation_fields", set())

    def get_ignore_fields(self) -> Set[str]:
        """获取需要忽略的字段集合"""
        return self.get_value("ignore_fields", set())

    def get_non_text_patterns(self) -> List[str]:
        """获取非文本模式列表"""
        return self.get_value("non_text_patterns", [])

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典，处理set类型的序列化

        Returns:
            配置字典，set类型转换为list
        """
        # 获取基础字典
        result = super().to_dict()

        # 处理set类型字段
        if "translation_fields" in result and isinstance(
            result["translation_fields"], set
        ):
            result["translation_fields"] = list(result["translation_fields"])

        if "ignore_fields" in result and isinstance(result["ignore_fields"], set):
            result["ignore_fields"] = list(result["ignore_fields"])

        return result

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典加载配置，处理list到set的转换

        Args:
            data: 配置数据字典
        """
        # 处理list到set的转换
        if "translation_fields" in data and isinstance(
            data["translation_fields"], list
        ):
            data["translation_fields"] = set(data["translation_fields"])

        if "ignore_fields" in data and isinstance(data["ignore_fields"], list):
            data["ignore_fields"] = set(data["ignore_fields"])

        # 调用基类方法
        super().from_dict(data)

    # 语言目录相关方法已迁移到 LanguageConfig

    def setup_logging(self):
        """设置日志系统"""
        import logging

        # 检查是否已经初始化过日志系统
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return  # 已经初始化，直接返回

        try:
            log_file = self.get_value("log_file")
            log_format = self.get_value("log_format")
            debug_mode = self.get_value("debug_mode", True)

            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # 创建文件处理器和控制台处理器
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
            file_handler.setFormatter(logging.Formatter(log_format))

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误
            console_handler.setFormatter(logging.Formatter(log_format))

            # 配置根日志器
            root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

            self.logger.info(f"日志系统初始化完成: {log_file}")

        except Exception as e:
            self.logger.error(f"日志系统初始化失败: {e}")
            raise
