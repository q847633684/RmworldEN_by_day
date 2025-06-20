"""
Day Translation 2 - 统一配置管理

整合所有配置相关的数据结构和管理功能到一个模块中。
遵循提示文件标准：单一职责、接口兼容、完善类型注解。
"""

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from colorama import Fore, Style

try:
    # 尝试相对导入 (包内使用)
    from ..constants.complete_definitions import (
        DEFAULT_DIRECTORIES,
        DEFAULT_FILENAMES,
        DEFAULT_TRANSLATION_FIELDS,
        ENCODING_SETTINGS,
        LanguageCode,
    )
    from ..models.exceptions import ConfigError
except ImportError:
    # 回退到绝对导入 (直接运行时)
    from constants.complete_definitions import (
        DEFAULT_DIRECTORIES,
        DEFAULT_FILENAMES,
        DEFAULT_TRANSLATION_FIELDS,
        ENCODING_SETTINGS,
        LanguageCode,
    )
    from models.exceptions import ConfigError

CONFIG_VERSION = "2.0.0"


# ==================== 默认工厂函数 ====================


def _default_translation_fields() -> Set[str]:
    """默认翻译字段工厂函数"""
    return set(DEFAULT_TRANSLATION_FIELDS)


def _default_file_extensions() -> Set[str]:
    """默认文件扩展名工厂函数"""
    return {".xml"}


# ==================== 基础数据模型 ====================


@dataclass
class PathValidationResult:
    """路径验证结果"""

    is_valid: bool
    error_message: Optional[str] = None
    normalized_path: Optional[str] = None
    path_type: Optional[str] = None


@dataclass
class FilterConfig:
    """过滤器配置"""

    # 字段过滤 - 使用统一的字段定义
    included_fields: Set[str] = field(default_factory=_default_translation_fields)
    excluded_fields: Set[str] = field(default_factory=set)

    # 内容过滤
    min_length: int = 1
    max_length: int = 1000
    exclude_numbers_only: bool = True
    exclude_single_chars: bool = True
    exclude_special_chars_only: bool = True

    # 文件类型过滤
    included_file_extensions: Set[str] = field(default_factory=_default_file_extensions)
    excluded_file_patterns: List[str] = field(default_factory=list)

    def should_include_field(self, field_name: str) -> bool:
        """检查字段是否应该包含"""
        if field_name in self.excluded_fields:
            return False
        return field_name in self.included_fields

    def should_include_content(self, content: str) -> bool:
        """检查内容是否应该包含"""
        if not content or len(content) < self.min_length:
            return False
        if len(content) > self.max_length:
            return False

        content_stripped = content.strip()
        if self.exclude_numbers_only and content_stripped.isdigit():
            return False
        if self.exclude_single_chars and len(content_stripped) == 1:
            return False
        if self.exclude_special_chars_only and not any(
            c.isalnum() for c in content_stripped
        ):
            return False

        return True


@dataclass
class ProcessingConfig:
    """处理配置"""

    # 多线程配置
    max_workers: int = 4
    chunk_size: int = 100

    # 内存管理
    max_memory_usage: int = 1024  # MB
    enable_memory_optimization: bool = True

    # 备份配置
    create_backups: bool = True
    max_backup_count: int = 5

    # 输出配置
    pretty_print_xml: bool = True
    xml_encoding: str = ENCODING_SETTINGS["xml"]
    csv_encoding: str = ENCODING_SETTINGS["csv"]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "max_memory_usage": self.max_memory_usage,
            "enable_memory_optimization": self.enable_memory_optimization,
            "create_backups": self.create_backups,
            "max_backup_count": self.max_backup_count,
            "pretty_print_xml": self.pretty_print_xml,
            "xml_encoding": self.xml_encoding,
            "csv_encoding": self.csv_encoding,
        }


# ==================== 用户偏好配置 ====================


@dataclass
class ExtractionPreferences:
    """提取操作的用户偏好"""

    output_location: str = "external"  # "internal" 或 "external"
    output_dir: Optional[str] = None
    en_keyed_dir: Optional[str] = None
    auto_detect_en_keyed: bool = True
    auto_choose_definjected: bool = False
    structure_choice: str = "original"  # "original", "defs", "structured"
    merge_mode: str = (
        "smart-merge"  # "merge", "replace", "backup", "skip", "smart-merge"
    )


@dataclass
class ImportPreferences:
    """导入操作的用户偏好"""

    merge_existing: bool = True
    backup_before_import: bool = True


@dataclass
class ApiPreferences:
    """API配置偏好"""

    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    save_api_keys: bool = True


@dataclass
class GeneralPreferences:
    """通用偏好设置"""

    remember_paths: bool = True
    auto_mode: bool = False
    confirm_operations: bool = True


@dataclass
class PathHistory:
    """路径历史记录"""

    paths: List[str] = field(default_factory=list)
    max_length: int = 10
    last_used: Optional[str] = None


# ==================== 核心配置 ====================


@dataclass
class CoreConfig:
    """核心配置数据模型"""

    # 语言设置
    default_language: str = LanguageCode.CHINESE_SIMPLIFIED.value
    source_language: str = LanguageCode.ENGLISH.value

    # 目录设置
    keyed_dir: str = DEFAULT_DIRECTORIES["keyed"]
    definjected_dir: str = DEFAULT_DIRECTORIES["definjected"]

    # 文件设置
    output_csv: str = DEFAULT_FILENAMES["output_csv"]

    # 日志设置
    log_file: str = ""
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    debug_mode: bool = False

    # 预览设置
    preview_translatable_fields: int = 0

    # 过滤和处理配置
    filter_config: FilterConfig = field(default_factory=FilterConfig)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)

    def __post_init__(self):
        """初始化后处理"""
        if not self.log_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = (
                f"{DEFAULT_DIRECTORIES['logs']}/day_translation_{timestamp}.log"
            )

    @property
    def default_fields(self) -> Set[str]:
        """获取默认字段集合（向后兼容）"""
        return self.filter_config.included_fields

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "default_language": self.default_language,
            "source_language": self.source_language,
            "keyed_dir": self.keyed_dir,
            "definjected_dir": self.definjected_dir,
            "output_csv": self.output_csv,
            "log_file": self.log_file,
            "log_format": self.log_format,
            "debug_mode": self.debug_mode,
            "preview_translatable_fields": self.preview_translatable_fields,
            "filter_config": self.filter_config.__dict__,
            "processing_config": self.processing_config.to_dict(),
        }


@dataclass
class UserConfig:
    """用户配置数据模型"""

    # 用户偏好
    extraction: ExtractionPreferences = field(default_factory=ExtractionPreferences)
    import_prefs: ImportPreferences = field(default_factory=ImportPreferences)
    api: ApiPreferences = field(default_factory=ApiPreferences)
    general: GeneralPreferences = field(default_factory=GeneralPreferences)

    # 路径记忆
    remembered_paths: Dict[str, str] = field(default_factory=dict)
    path_history: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """确保子对象都是正确的类型"""
        if isinstance(self.extraction, dict):
            self.extraction = ExtractionPreferences(**self.extraction)
        if isinstance(self.import_prefs, dict):
            self.import_prefs = ImportPreferences(**self.import_prefs)
        if isinstance(self.api, dict):
            self.api = ApiPreferences(**self.api)
        if isinstance(self.general, dict):
            self.general = GeneralPreferences(**self.general)

    def get_extraction_pref(self, key: str, default: Any = None) -> Any:
        """获取提取偏好设置"""
        return getattr(self.extraction, key, default)

    def set_extraction_pref(self, key: str, value: Any):
        """设置提取偏好"""
        setattr(self.extraction, key, value)

    def get_api_key(self, key: str) -> Optional[str]:
        """获取API密钥"""
        if key == "ALIYUN_ACCESS_KEY_ID":
            return self.api.aliyun_access_key_id
        elif key == "ALIYUN_ACCESS_KEY_SECRET":
            return self.api.aliyun_access_key_secret
        return None

    def set_api_key(self, key: str, value: str):
        """设置API密钥"""
        if key == "ALIYUN_ACCESS_KEY_ID":
            self.api.aliyun_access_key_id = value
        elif key == "ALIYUN_ACCESS_KEY_SECRET":
            self.api.aliyun_access_key_secret = value

    def remember_path(self, path_type: str, path: str):
        """记住路径"""
        self.remembered_paths[path_type] = path

    def get_remembered_path(self, path_type: str) -> Optional[str]:
        """获取记住的路径"""
        return self.remembered_paths.get(path_type)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "extraction": asdict(self.extraction),
            "import_prefs": asdict(self.import_prefs),
            "api": asdict(self.api),
            "general": asdict(self.general),
            "remembered_paths": self.remembered_paths,
            "path_history": self.path_history,
        }


# ==================== 统一配置管理 ====================


@dataclass
class UnifiedConfig:
    """统一配置类 - 整合所有配置管理功能"""

    version: str = CONFIG_VERSION
    core: CoreConfig = field(default_factory=CoreConfig)
    user: UserConfig = field(default_factory=UserConfig)

    def __post_init__(self):
        # 确保子对象都是正确的类型
        if isinstance(self.core, dict):
            self.core = CoreConfig(**self.core)
        if isinstance(self.user, dict):
            self.user = UserConfig(**self.user)

        # 动态生成日志文件名
        if not self.core.log_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                DEFAULT_DIRECTORIES["logs"],
            )
            self.core.log_file = os.path.join(
                log_dir, f"day_translation_{timestamp}.log"
            )

        self._setup_logging()
        self._setup_path_validators()

    def _setup_logging(self) -> None:
        """设置日志系统"""
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return  # 已经初始化

        try:
            log_dir = os.path.dirname(self.core.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # 创建文件处理器和控制台处理器
            file_handler = logging.FileHandler(self.core.log_file, encoding="utf-8")
            file_handler.setLevel(
                logging.DEBUG if self.core.debug_mode else logging.INFO
            )
            file_handler.setFormatter(logging.Formatter(self.core.log_format))

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(self.core.log_format))

            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            root_logger.setLevel(
                logging.DEBUG if self.core.debug_mode else logging.INFO
            )

        except (OSError, IOError) as e:
            print(f"日志文件创建失败: {e}")
        except ValueError as e:
            print(f"日志格式配置错误: {e}")
        except Exception as e:
            print(f"日志系统初始化失败: {e}")

    def _setup_path_validators(self):
        """设置路径验证器"""
        self._path_pattern = re.compile(
            r"^[a-zA-Z]:[\\/]|^[\\/]{2}|^[a-zA-Z0-9_\-\.]+[\\/]"
        )
        self._validators: Dict[str, Callable[[str], PathValidationResult]] = {
            "dir": self._validate_directory,
            "dir_create": self._validate_directory_create,
            "file": self._validate_file,
            "csv": self._validate_csv_file,
            "xml": self._validate_xml_file,
            "json": self._validate_json_file,
            "mod": self._validate_mod_directory,
        }

    # ==================== 路径验证功能 ====================

    def _validate_directory(self, path: str) -> PathValidationResult:
        """验证目录路径"""
        try:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_dir():
                return PathValidationResult(
                    is_valid=True,
                    normalized_path=str(path_obj.absolute()),
                    path_type="directory",
                )
            else:
                return PathValidationResult(
                    is_valid=False, error_message=f"目录不存在: {path}"
                )
        except (OSError, ValueError, TypeError) as e:
            return PathValidationResult(
                is_valid=False, error_message=f"路径验证失败: {e}"
            )

    def _validate_directory_create(self, path: str) -> PathValidationResult:
        """验证目录路径，如果不存在则允许创建"""
        try:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_dir():
                    return PathValidationResult(
                        is_valid=True,
                        normalized_path=str(path_obj.absolute()),
                        path_type="directory",
                    )
                else:
                    return PathValidationResult(
                        is_valid=False, error_message=f"路径存在但不是目录: {path}"
                    )
            else:
                # 检查父目录是否存在
                parent = path_obj.parent
                if parent.exists() and parent.is_dir():
                    return PathValidationResult(
                        is_valid=True,
                        normalized_path=str(path_obj.absolute()),
                        path_type="directory_create",
                    )
                else:
                    return PathValidationResult(
                        is_valid=False, error_message=f"父目录不存在: {parent}"
                    )
        except (OSError, ValueError, TypeError) as e:
            return PathValidationResult(
                is_valid=False, error_message=f"路径验证失败: {e}"
            )

    def _validate_file(self, path: str) -> PathValidationResult:
        """验证文件路径"""
        try:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_file():
                return PathValidationResult(
                    is_valid=True,
                    normalized_path=str(path_obj.absolute()),
                    path_type="file",
                )
            else:
                return PathValidationResult(
                    is_valid=False, error_message=f"文件不存在: {path}"
                )
        except Exception as e:
            return PathValidationResult(
                is_valid=False, error_message=f"文件验证失败: {e}"
            )

    def _validate_csv_file(self, path: str) -> PathValidationResult:
        """验证CSV文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith(".csv"):
            result.is_valid = False
            result.error_message = f"不是CSV文件: {path}"
        return result

    def _validate_xml_file(self, path: str) -> PathValidationResult:
        """验证XML文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith(".xml"):
            result.is_valid = False
            result.error_message = f"不是XML文件: {path}"
        return result

    def _validate_json_file(self, path: str) -> PathValidationResult:
        """验证JSON文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith(".json"):
            result.is_valid = False
            result.error_message = f"不是JSON文件: {path}"
        return result

    def _validate_mod_directory(self, path: str) -> PathValidationResult:
        """验证模组目录路径"""
        result = self._validate_directory(path)
        if result.is_valid:
            # 可以添加更多模组目录特有的验证逻辑
            pass
        return result

    def normalize_path(self, path: str) -> PathValidationResult:
        """规范化路径"""
        try:
            normalized = str(Path(path).resolve())
            return PathValidationResult(
                is_valid=True, normalized_path=normalized, path_type="normalized"
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False, error_message=f"路径规范化失败: {e}"
            )

    def validate_path(
        self, path: str, validator_type: str = "file"
    ) -> PathValidationResult:
        """验证路径"""
        if validator_type in self._validators:
            return self._validators[validator_type](path)
        else:
            return PathValidationResult(
                is_valid=False, error_message=f"未知验证器类型: {validator_type}"
            )

    # ==================== 路径记忆和历史记录功能 ====================

    def remember_path(self, path_type: str, path: str):
        """记住用户选择的路径"""
        if self.user.general.remember_paths:
            self.user.remember_path(path_type, path)

    def get_remembered_path(self, path_type: str) -> Optional[str]:
        """获取记住的路径"""
        return self.user.get_remembered_path(path_type)

    def add_to_history(self, path_type: str, path: str):
        """添加路径到历史记录"""
        if path_type not in self.user.path_history:
            self.user.path_history[path_type] = {
                "paths": [],
                "max_length": 10,
                "last_used": None,
            }

        history = self.user.path_history[path_type]

        # 如果路径已存在，先移除
        if path in history["paths"]:
            history["paths"].remove(path)

        # 添加到开头
        history["paths"].insert(0, path)

        # 限制历史记录长度
        if len(history["paths"]) > history["max_length"]:
            history["paths"] = history["paths"][: history["max_length"]]

        history["last_used"] = path

    def get_path_history(self, path_type: str) -> List[str]:
        """获取路径历史记录"""
        return self.user.path_history.get(path_type, {}).get("paths", [])

    def get_last_used_path(self, path_type: str) -> Optional[str]:
        """获取最后使用的路径"""
        return self.user.path_history.get(path_type, {}).get("last_used")

    # ==================== 配置管理功能 ====================

    def save_config(self, config_path: Optional[str] = None):
        """保存配置到文件"""
        if not config_path:
            config_path = get_config_path()

        try:
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            config_data = {
                "version": self.version,
                "core": self.core.to_dict(),
                "user": self.user.to_dict(),
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logging.info(f"配置已保存到: {config_path}")

        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            logging.error(error_msg)
            raise ConfigError(error_msg)

    def show_config(self):
        """显示当前配置"""
        print(f"\n{Fore.BLUE}=== 当前配置 ==={Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}核心配置:{Style.RESET_ALL}")
        core_dict = asdict(self.core)
        for key, value in core_dict.items():
            if key not in ["filter_config", "processing_config"]:
                print(f"  {key}: {value}")

        print(f"\n{Fore.CYAN}用户偏好:{Style.RESET_ALL}")
        print("  提取偏好:")
        for key, value in asdict(self.user.extraction).items():
            print(f"    {key}: {value}")

        print("  通用设置:")
        for key, value in asdict(self.user.general).items():
            print(f"    {key}: {value}")

        print("  API配置:")
        api_dict = asdict(self.user.api)
        for key, value in api_dict.items():
            if "secret" in key.lower():
                value = "***" if value else ""
            print(f"    {key}: {value}")

    def reset_config(self):
        """重置配置为默认值"""
        self.core = CoreConfig()
        self.user = UserConfig()
        logging.info("配置已重置为默认值")

    @property
    def default_fields(self) -> Set[str]:
        """获取默认字段集合"""
        return self.core.default_fields


# ==================== 全局配置管理 ====================

_global_config_instance = None


def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(Path.home(), ".day_translation", "config.json")


def get_config() -> UnifiedConfig:
    """获取全局配置实例（单例模式）"""
    global _global_config_instance
    if _global_config_instance is None:
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                _global_config_instance = UnifiedConfig(**config_data)
                logging.info(f"已加载配置文件: {config_path}")
            except Exception as e:
                logging.warning(f"配置文件加载失败，使用默认配置: {e}")
                _global_config_instance = UnifiedConfig()
        else:
            _global_config_instance = UnifiedConfig()
            # 首次运行时保存默认配置
            _global_config_instance.save_config()
            logging.info("已创建默认配置文件")

    return _global_config_instance


def save_config():
    """保存当前配置"""
    config = get_config()
    config.save_config()


def reset_config():
    """重置并重新加载配置"""
    global _global_config_instance
    _global_config_instance = None
    config = get_config()
    config.reset_config()
    config.save_config()
    return config
