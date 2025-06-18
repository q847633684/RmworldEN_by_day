"""
Day Translation 2 - 配置数据模型

定义配置相关的数据结构，包括核心配置、用户配置、路径验证等。
遵循提示文件标准：PascalCase类命名，完善的类型注解。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from pathlib import Path


class LanguageCode(Enum):
    """支持的语言代码"""
    ENGLISH = "English"
    CHINESE_SIMPLIFIED = "ChineseSimplified"
    CHINESE_TRADITIONAL = "ChineseTraditional"
    JAPANESE = "Japanese"
    KOREAN = "Korean"
    
    def __str__(self) -> str:
        """返回用户友好的语言名称"""
        language_names = {
            self.ENGLISH: "英语",
            self.CHINESE_SIMPLIFIED: "简体中文",
            self.CHINESE_TRADITIONAL: "繁体中文",
            self.JAPANESE: "日语",
            self.KOREAN: "韩语"
        }
        return language_names.get(self, self.value)


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
    
    # 字段过滤
    included_fields: Set[str] = field(default_factory=lambda: {
        'label', 'description', 'labelShort', 'descriptionShort',
        'title', 'text', 'message', 'tooltip', 'baseDesc',
        'skillDescription', 'backstoryDesc', 'jobString',
        'gerundLabel', 'verb', 'deathMessage', 'summary'
    })
    
    excluded_fields: Set[str] = field(default_factory=set)
    
    # 内容过滤
    min_length: int = 1
    max_length: int = 1000
    exclude_numbers_only: bool = True
    exclude_single_chars: bool = True
    exclude_special_chars_only: bool = True
    
    # 文件类型过滤
    included_file_extensions: Set[str] = field(default_factory=lambda: {'.xml'})
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
        
        if self.exclude_special_chars_only and not any(c.isalnum() for c in content_stripped):
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
    xml_encoding: str = "utf-8"
    csv_encoding: str = "utf-8-sig"
    
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
            "csv_encoding": self.csv_encoding
        }


@dataclass
class CoreConfig:
    """核心配置数据模型"""
    
    # 语言设置
    default_language: str = LanguageCode.CHINESE_SIMPLIFIED.value
    source_language: str = LanguageCode.ENGLISH.value
    
    # 目录设置
    keyed_dir: str = "Keyed"
    definjected_dir: str = "DefInjected"
    
    # 文件设置
    output_csv: str = "extracted_translations.csv"
    
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
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"logs/day_translation_{timestamp}.log"
    
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
            "processing_config": self.processing_config.to_dict()
        }


@dataclass
class UserConfig:
    """用户配置数据模型"""
    
    # 提取偏好
    extraction: Dict[str, Any] = field(default_factory=dict)
    
    # 导入偏好
    import_prefs: Dict[str, Any] = field(default_factory=dict)
    
    # API配置
    api: Dict[str, Any] = field(default_factory=dict)
    
    # 通用设置
    general: Dict[str, Any] = field(default_factory=dict)
    
    # 路径记忆
    remembered_paths: Dict[str, str] = field(default_factory=dict)
    path_history: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_extraction_pref(self, key: str, default: Any = None) -> Any:
        """获取提取偏好设置"""
        return self.extraction.get(key, default)
    
    def set_extraction_pref(self, key: str, value: Any):
        """设置提取偏好"""
        self.extraction[key] = value
    
    def get_api_key(self, key: str) -> Optional[str]:
        """获取API密钥"""
        return self.api.get(key)
    
    def set_api_key(self, key: str, value: str):
        """设置API密钥"""
        self.api[key] = value
    
    def remember_path(self, path_type: str, path: str):
        """记住路径"""
        self.remembered_paths[path_type] = path
    
    def get_remembered_path(self, path_type: str) -> Optional[str]:
        """获取记住的路径"""
        return self.remembered_paths.get(path_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "extraction": self.extraction,
            "import_prefs": self.import_prefs,
            "api": self.api,
            "general": self.general,
            "remembered_paths": self.remembered_paths,
            "path_history": self.path_history
        }


@dataclass
class ProjectConfig:
    """项目完整配置"""
    
    version: str = "2.0.0"
    core: CoreConfig = field(default_factory=CoreConfig)
    user: UserConfig = field(default_factory=UserConfig)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保子配置对象的类型正确
        if isinstance(self.core, dict):
            self.core = CoreConfig(**self.core)
        if isinstance(self.user, dict):
            self.user = UserConfig(**self.user)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "version": self.version,
            "core": self.core.to_dict(),
            "user": self.user.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """从字典创建配置对象"""
        return cls(
            version=data.get("version", "2.0.0"),
            core=CoreConfig(**data.get("core", {})),
            user=UserConfig(**data.get("user", {}))
        )
