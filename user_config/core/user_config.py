"""
用户配置管理器

统一管理所有用户配置
"""

from typing import Any, Dict, Optional, List
from pathlib import Path
import os
from utils.logging_config import get_logger
from ..api.api_manager import APIManager
from .base_config import BaseConfig
from .system_config import SystemConfig


class PathConfig(BaseConfig):
    """路径配置"""

    def __init__(self):
        super().__init__("路径配置")

        # 默认值
        self._defaults.update(
            {
                "default_export_csv": "",
                "default_output_dir": "",
                "remember_paths": True,
                "path_history": {},  # 路径历史记录
                "max_history_length": 10,  # 历史记录长度限制
            }
        )

        # 字段类型
        self._field_types.update(
            {
                "default_export_csv": str,
                "default_output_dir": str,
                "remember_paths": bool,
                "path_history": dict,
                "max_history_length": int,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "default_export_csv": {
                "type": "file",
                "label": "默认导出CSV",
                "description": "默认的CSV导出文件路径",
                "filter": "CSV文件 (*.csv)|*.csv",
                "placeholder": "选择CSV文件",
            },
            "default_output_dir": {
                "type": "directory",
                "label": "默认输出目录",
                "description": "默认的输出目录",
                "placeholder": "选择输出目录",
            },
            "remember_paths": {
                "type": "boolean",
                "label": "记住路径",
                "description": "是否记住最近使用的路径",
                "default": True,
            },
        }

    def validate(self) -> bool:
        """验证路径配置"""
        # 检查路径是否存在（如果已设置）
        for key in ["default_import_csv", "default_export_csv"]:
            path = self.get_value(key)
            if path and not os.path.exists(os.path.dirname(path)):
                self.logger.warning(f"路径不存在: {path}")

        for key in ["default_mod_dir", "default_output_dir"]:
            path = self.get_value(key)
            if path and not os.path.exists(path):
                self.logger.warning(f"目录不存在: {path}")

        return True

    def add_to_history(self, path_type: str, path: str) -> None:
        """添加路径到历史记录"""
        history = self.get_value("path_history", {})
        if path_type not in history:
            history[path_type] = []

        # 移除重复项
        if path in history[path_type]:
            history[path_type].remove(path)

        # 添加到开头
        history[path_type].insert(0, path)

        # 限制长度
        max_length = self.get_value("max_history_length", 10)
        history[path_type] = history[path_type][:max_length]

        self.set_value("path_history", history)

    def get_history(self, path_type: str) -> List[str]:
        """获取指定类型的历史记录"""
        history = self.get_value("path_history", {})
        return history.get(path_type, [])

    def clear_history(self, path_type: Optional[str] = None) -> None:
        """清除历史记录"""
        if path_type:
            history = self.get_value("path_history", {})
            if path_type in history:
                del history[path_type]
                self.set_value("path_history", history)
        else:
            self.set_value("path_history", {})


class LanguageConfig(BaseConfig):
    """语言配置 - 管理所有语言相关设置"""

    def __init__(self):
        super().__init__("语言配置")

        # 默认值 - 包含从系统配置迁移的语言相关字段
        self._defaults.update(
            {
                # 语言目录配置 (从系统配置迁移)
                "cn_language": "ChineseSimplified",
                "en_language": "English",
                "definjected_dir": "DefInjected",
                "keyed_dir": "Keyed",
                "output_csv": "extracted_translations.csv",
                # 界面和格式配置
                "interface_language": "zh_CN",  # 界面语言
                "csv_encoding": "utf-8",  # CSV文件编码
                "csv_delimiter": ",",  # CSV分隔符
                "date_format": "%Y-%m-%d %H:%M:%S",  # 日期格式
                "number_format": "1,234.56",  # 数字格式
            }
        )

        # 必需字段
        self._required_fields = {
            "cn_language",
            "en_language",
            "definjected_dir",
            "keyed_dir",
            "output_csv",
        }

        # 字段类型
        self._field_types.update(
            {
                # 语言目录类型
                "cn_language": str,
                "en_language": str,
                "definjected_dir": str,
                "keyed_dir": str,
                "output_csv": str,
                # 界面和格式类型
                "interface_language": str,
                "csv_encoding": str,
                "csv_delimiter": str,
                "date_format": str,
                "number_format": str,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            # 语言目录配置
            "cn_language": {
                "type": "text",
                "label": "中文语言目录",
                "description": "中文语言目录名称",
                "default": "ChineseSimplified",
                "required": True,
            },
            "en_language": {
                "type": "text",
                "label": "英文语言目录",
                "description": "英文语言目录名称",
                "default": "English",
                "required": True,
            },
            "definjected_dir": {
                "type": "text",
                "label": "DefInjected目录",
                "description": "DefInjected子目录名称",
                "default": "DefInjected",
                "required": True,
            },
            "keyed_dir": {
                "type": "text",
                "label": "Keyed目录",
                "description": "Keyed子目录名称",
                "default": "Keyed",
                "required": True,
            },
            "output_csv": {
                "type": "text",
                "label": "默认输出CSV",
                "description": "默认输出CSV文件名",
                "default": "extracted_translations.csv",
                "required": True,
            },
            # 界面和格式配置
            "interface_language": {
                "type": "select",
                "label": "界面语言",
                "description": "用户界面显示语言",
                "default": "zh_CN",
                "options": [
                    {"value": "zh_CN", "label": "简体中文"},
                    {"value": "en_US", "label": "English"},
                ],
            },
            "csv_encoding": {
                "type": "select",
                "label": "CSV编码",
                "description": "CSV文件字符编码",
                "default": "utf-8",
                "options": [
                    {"value": "utf-8", "label": "UTF-8"},
                    {"value": "gbk", "label": "GBK"},
                    {"value": "utf-8-sig", "label": "UTF-8 with BOM"},
                ],
            },
            "csv_delimiter": {
                "type": "select",
                "label": "CSV分隔符",
                "description": "CSV文件字段分隔符",
                "default": ",",
                "options": [
                    {"value": ",", "label": "逗号 (,)"},
                    {"value": ";", "label": "分号 (;)"},
                    {"value": "\\t", "label": "制表符 (Tab)"},
                ],
            },
            "date_format": {
                "type": "text",
                "label": "日期格式",
                "description": "日期时间显示格式",
                "default": "%Y-%m-%d %H:%M:%S",
                "placeholder": "%Y-%m-%d %H:%M:%S",
            },
            "number_format": {
                "type": "text",
                "label": "数字格式",
                "description": "数字显示格式",
                "default": "1,234.56",
                "placeholder": "1,234.56",
            },
        }

    def validate(self) -> bool:
        """验证语言配置"""
        # 验证必需的语言目录字段
        required_fields = [
            "cn_language",
            "en_language",
            "definjected_dir",
            "keyed_dir",
            "output_csv",
        ]
        for field in required_fields:
            value = self.get_value(field, "")
            if not value or not isinstance(value, str) or not value.strip():
                self.logger.error(f"语言配置字段 {field} 不能为空")
                return False

        # 验证界面语言
        interface_lang = self.get_value("interface_language", "")
        if interface_lang not in ["zh_CN", "en_US"]:
            self.logger.error("界面语言必须是 zh_CN 或 en_US")
            return False

        # 验证CSV编码
        csv_encoding = self.get_value("csv_encoding", "")
        if csv_encoding not in ["utf-8", "gbk", "utf-8-sig"]:
            self.logger.error("CSV编码必须是支持的编码格式")
            return False

        # 验证CSV分隔符
        csv_delimiter = self.get_value("csv_delimiter", "")
        if csv_delimiter not in [",", ";", "\\t"]:
            self.logger.error("CSV分隔符必须是支持的分隔符")
            return False

        return True

    def get_language_dir(self, base_dir, language: str):
        """获取指定语言的Languages目录路径"""
        from pathlib import Path

        return Path(base_dir) / "Languages" / language

    def get_language_subdir(self, base_dir, language: str, subdir_type: str):
        """获取指定语言的子目录路径"""
        from pathlib import Path

        subdir_type = subdir_type.lower()
        subdir_map = {
            "definjected": self.get_value("definjected_dir"),
            "keyed": self.get_value("keyed_dir"),
        }

        if subdir_type not in subdir_map:
            raise ValueError(f"不支持的子目录类型: {subdir_type}")

        return self.get_language_dir(base_dir, language) / subdir_map[subdir_type]


class LogConfig(BaseConfig):
    """日志配置"""

    def __init__(self):
        super().__init__("日志配置")

        # 默认值
        self._defaults.update(
            {
                "log_level": "INFO",
                "log_to_file": True,
                "log_to_console": False,
                "log_file_size": 10,  # MB
                "log_backup_count": 5,
                "log_format": "%(asctime)s - %(levelname)s - %(message)s",
            }
        )

        # 字段类型
        self._field_types.update(
            {
                "log_level": str,
                "log_to_file": bool,
                "log_to_console": bool,
                "log_file_size": int,
                "log_backup_count": int,
                "log_format": str,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "log_level": {
                "type": "select",
                "label": "日志级别",
                "description": "设置日志记录级别",
                "options": [
                    {"value": "DEBUG", "label": "调试"},
                    {"value": "INFO", "label": "信息"},
                    {"value": "WARNING", "label": "警告"},
                    {"value": "ERROR", "label": "错误"},
                ],
                "default": "INFO",
            },
            "log_to_file": {
                "type": "boolean",
                "label": "记录到文件",
                "description": "是否将日志记录到文件",
                "default": True,
            },
            "log_to_console": {
                "type": "boolean",
                "label": "输出到控制台",
                "description": "是否将日志输出到控制台",
                "default": False,
            },
            "log_file_size": {
                "type": "number",
                "label": "日志文件大小(MB)",
                "description": "单个日志文件的最大大小",
                "min": 1,
                "max": 100,
                "default": 10,
            },
            "log_backup_count": {
                "type": "number",
                "label": "备份文件数量",
                "description": "保留的日志备份文件数量",
                "min": 1,
                "max": 20,
                "default": 5,
            },
        }

    def validate(self) -> bool:
        """验证日志配置"""
        log_level = self.get_value("log_level")
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            self.logger.error(f"无效的日志级别: {log_level}")
            return False

        log_file_size = self.get_value("log_file_size", 10)
        if log_file_size < 1 or log_file_size > 100:
            self.logger.error(f"日志文件大小无效: {log_file_size}")
            return False

        return True


class UIConfig(BaseConfig):
    """界面配置"""

    def __init__(self):
        super().__init__("界面配置")

        # 默认值
        self._defaults.update(
            {
                "theme": "default",
                "language": "zh_CN",
                "show_progress": True,
                "confirm_actions": True,
                "auto_save": True,
            }
        )

        # 字段类型
        self._field_types.update(
            {
                "theme": str,
                "language": str,
                "show_progress": bool,
                "confirm_actions": bool,
                "auto_save": bool,
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "theme": {
                "type": "select",
                "label": "界面主题",
                "description": "选择界面主题",
                "options": [
                    {"value": "default", "label": "默认"},
                    {"value": "dark", "label": "深色"},
                    {"value": "light", "label": "浅色"},
                ],
                "default": "default",
            },
            "language": {
                "type": "select",
                "label": "界面语言",
                "description": "选择界面显示语言",
                "options": [
                    {"value": "zh_CN", "label": "简体中文"},
                    {"value": "en_US", "label": "English"},
                ],
                "default": "zh_CN",
            },
            "show_progress": {
                "type": "boolean",
                "label": "显示进度条",
                "description": "是否显示操作进度条",
                "default": True,
            },
            "confirm_actions": {
                "type": "boolean",
                "label": "确认操作",
                "description": "是否在执行重要操作前确认",
                "default": True,
            },
            "auto_save": {
                "type": "boolean",
                "label": "自动保存",
                "description": "是否自动保存配置更改",
                "default": True,
            },
        }

    def validate(self) -> bool:
        """验证界面配置"""
        return True


class UserConfigManager:
    """用户配置管理器"""

    def __init__(self):
        """初始化用户配置管理器"""
        self.logger = get_logger(f"{__name__}.UserConfigManager")

        # 初始化各个配置模块
        self.system_config = SystemConfig()  # 系统配置
        self.api_manager = APIManager()
        self.path_config = PathConfig()
        self.language_config = LanguageConfig()
        self.log_config = LogConfig()
        self.ui_config = UIConfig()

        # 配置文件路径
        self.config_dir = Path.home() / ".day_translation"
        self.config_file = self.config_dir / "user_config.json"

        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        self.logger.info("用户配置管理器初始化完成")

    def get_config_modules(self) -> Dict[str, BaseConfig]:
        """获取所有配置模块"""
        return {
            "system": self.system_config,
            "api": self.api_manager,
            "path": self.path_config,
            "language": self.language_config,
            "log": self.log_config,
            "ui": self.ui_config,
        }

    def get_config_module(self, module_name: str) -> Optional[BaseConfig]:
        """获取指定配置模块"""
        modules = self.get_config_modules()
        return modules.get(module_name)

    def validate_all_configs(self) -> Dict[str, bool]:
        """验证所有配置"""
        results = {}
        modules = self.get_config_modules()

        for name, module in modules.items():
            try:
                results[name] = module.validate()
            except Exception as e:
                self.logger.error(f"验证配置模块失败: {name}, 错误: {e}")
                results[name] = False

        return results

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": "2.0.0",
            "system": self.system_config.to_dict(),
            "api": self.api_manager.to_dict(),
            "path": self.path_config.to_dict(),
            "language": self.language_config.to_dict(),
            "log": self.log_config.to_dict(),
            "ui": self.ui_config.to_dict(),
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载配置"""
        version = data.get("version", "1.0.0")
        self.logger.info(f"加载配置版本: {version}")

        # 加载各模块配置
        if "system" in data:
            self.system_config.from_dict(data["system"])

        if "api" in data:
            self.api_manager.from_dict(data["api"])

        if "path" in data:
            self.path_config.from_dict(data["path"])

        if "language" in data:
            self.language_config.from_dict(data["language"])

        if "log" in data:
            self.log_config.from_dict(data["log"])

        if "ui" in data:
            self.ui_config.from_dict(data["ui"])

    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            import json

            config_data = self.to_dict()

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"配置已保存到: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False

    def load_config(self) -> bool:
        """从文件加载配置"""
        try:
            if not self.config_file.exists():
                self.logger.info("配置文件不存在，使用默认配置")
                return True

            import json

            with open(self.config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            self.from_dict(config_data)
            self.logger.info(f"配置已从 {self.config_file} 加载")
            return True

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """重置所有配置为默认值"""
        self.api_manager = APIManager()
        self.path_config.reset_to_defaults()
        self.language_config.reset_to_defaults()
        self.log_config.reset_to_defaults()
        self.ui_config.reset_to_defaults()

        self.logger.info("所有配置已重置为默认值")

    def backup_config(self, backup_path: Optional[str] = None) -> bool:
        """备份配置"""
        try:
            if backup_path is None:
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = str(self.config_dir / f"config_backup_{timestamp}.json")

            import shutil

            shutil.copy2(self.config_file, backup_path)

            self.logger.info(f"配置已备份到: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"备份配置失败: {e}")
            return False

    def restore_config(self, backup_path: str) -> bool:
        """恢复配置"""
        try:
            import shutil

            shutil.copy2(backup_path, self.config_file)

            # 重新加载配置
            self.load_config()

            self.logger.info(f"配置已从 {backup_path} 恢复")
            return True

        except Exception as e:
            self.logger.error(f"恢复配置失败: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "config_file": str(self.config_file),
            "config_exists": self.config_file.exists(),
            "modules": {
                name: {
                    "valid": module.validate() if hasattr(module, "validate") else True,
                    "complete": (
                        module.is_complete() if hasattr(module, "is_complete") else True
                    ),
                }
                for name, module in self.get_config_modules().items()
            },
            "api_status": self.api_manager.get_api_status(),
        }
