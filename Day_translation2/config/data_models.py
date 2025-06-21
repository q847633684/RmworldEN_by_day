"""
Day Translation 2 - 纯配置数据模型

只包含数据结构定义，无任何业务逻辑。
遵循"配置只做配置"的架构原则。
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set

from constants.complete_definitions import (
    DEFAULT_DIRECTORIES,
    DEFAULT_FILENAMES,
    DEFAULT_TRANSLATION_FIELDS,
    ENCODING_SETTINGS,
    LanguageCode,
)

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
@dataclass
class PathValidationResult:
    """路径验证结果"""

    is_valid: bool
    path: Optional[str] = None
    normalized_path: Optional[str] = None
    error_message: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class GeneralConfig:
    """通用配置数据模型"""

    auto_mode: bool = False
    remember_paths: bool = True
    confirm_operations: bool = True
    max_history_items: int = 10


@dataclass
class ExtractionConfig:
    """提取配置数据模型"""

    structure_choice: str = "original"
    merge_mode: str = "smart-merge"
    output_location: str = "external"
    output_dir: Optional[str] = None
    en_keyed_dir: Optional[str] = None
    auto_detect_en_keyed: bool = True
    auto_choose_definjected: bool = False


@dataclass
class APIConfig:
    """API配置数据模型"""

    aliyun_access_key_id: Optional[str] = None
    aliyun_access_key_secret: Optional[str] = None
    save_api_keys: bool = False
    request_timeout: int = 30
    max_retries: int = 3


@dataclass
class ProcessingConfig:
    """处理配置数据模型"""

    max_workers: int = 4
    chunk_size: int = 100
    enable_parallel: bool = True
    memory_limit_mb: int = 512


@dataclass
class FilterConfig:
    """过滤配置数据模型"""

    default_fields: Set[str] = field(default_factory=_default_translation_fields)
    ignore_fields: Set[str] = field(default_factory=set)
    file_extensions: Set[str] = field(default_factory=_default_file_extensions)
    min_text_length: int = 1
    max_text_length: int = 1000
    enable_smart_filter: bool = True


@dataclass
class PathHistory:
    """路径历史记录数据模型"""

    paths: List[str] = field(default_factory=list)
    last_used: Optional[str] = None
    max_items: int = 10


# ==================== 核心配置 ====================


@dataclass
class CoreConfig:
    """核心配置数据模型"""

    version: str = CONFIG_VERSION
    default_language: str = LanguageCode.CHINESE_SIMPLIFIED.value
    source_language: str = LanguageCode.ENGLISH.value
    debug_mode: bool = False
    encoding: str = ENCODING_SETTINGS["default"]
    backup_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoreConfig":
        """从字典创建实例"""
        return cls(**data)


@dataclass
class UserConfig:
    """用户配置数据模型"""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    api: APIConfig = field(default_factory=APIConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    filter: FilterConfig = field(default_factory=FilterConfig)
    remembered_paths: Dict[str, str] = field(default_factory=dict)
    path_history: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 处理 Set 类型字段
        if "filter" in result and "default_fields" in result["filter"]:
            result["filter"]["default_fields"] = list(result["filter"]["default_fields"])
        if "filter" in result and "ignore_fields" in result["filter"]:
            result["filter"]["ignore_fields"] = list(result["filter"]["ignore_fields"])
        if "filter" in result and "file_extensions" in result["filter"]:
            result["filter"]["file_extensions"] = list(result["filter"]["file_extensions"])
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserConfig":
        """从字典创建实例"""
        # 处理 Set 类型字段
        if "filter" in data:
            filter_data = data["filter"]
            if "default_fields" in filter_data and isinstance(filter_data["default_fields"], list):
                filter_data["default_fields"] = set(filter_data["default_fields"])
            if "ignore_fields" in filter_data and isinstance(filter_data["ignore_fields"], list):
                filter_data["ignore_fields"] = set(filter_data["ignore_fields"])
            if "file_extensions" in filter_data and isinstance(
                filter_data["file_extensions"], list
            ):
                filter_data["file_extensions"] = set(filter_data["file_extensions"])

        return cls(**data)


# ==================== 统一配置容器 ====================


@dataclass
class UnifiedConfig:
    """统一配置数据容器 - 纯数据模型，无业务逻辑"""

    core: CoreConfig = field(default_factory=CoreConfig)
    user: UserConfig = field(default_factory=UserConfig)
    version: str = CONFIG_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "core": self.core.to_dict(),
            "user": self.user.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedConfig":
        """从字典创建实例"""
        return cls(
            version=data.get("version", CONFIG_VERSION),
            core=CoreConfig.from_dict(data.get("core", {})),
            user=UserConfig.from_dict(data.get("user", {})),
        )

    def __post_init__(self):
        """后初始化处理"""
        # 确保版本一致性
        if self.core.version != self.version:
            self.core.version = self.version
