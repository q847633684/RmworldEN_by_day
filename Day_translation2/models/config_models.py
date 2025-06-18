"""
Day Translation 2 - 配置数据模型

定义配置相关的数据结构。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class PathValidationResult:
    """路径验证结果"""
    is_valid: bool
    message: str
    path: Optional[Path] = None

@dataclass
class CoreConfig:
    """核心配置数据模型"""
    # 路径配置
    mod_folder: str = ""
    language_folder: str = ""
    output_folder: str = ""
    template_folder: str = ""
    
    # 文件配置
    csv_filename: str = "translations.csv"
    encoding: str = "utf-8"
    
    # 处理配置
    batch_size: int = 100
    max_workers: int = 4
    
    # 验证配置
    validate_xml: bool = True
    backup_files: bool = True
    
    def __post_init__(self):
        """配置验证"""
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.max_workers <= 0:
            raise ValueError("Max workers must be positive")

@dataclass 
class UserConfig:
    """用户配置数据模型"""
    # 用户偏好
    preferred_language: str = "zh-CN"
    auto_backup: bool = True
    confirm_operations: bool = True
    show_progress: bool = True
    
    # 界面配置
    console_width: int = 80
    show_welcome: bool = True
    verbose_output: bool = False
    
    # 翻译配置
    use_machine_translation: bool = False
    translation_service: str = "google"
    api_key: str = ""
    
    # 历史记录
    max_history_items: int = 50
    save_history: bool = True

@dataclass
class FilterConfig:
    """过滤器配置"""
    exclude_empty: bool = True
    exclude_numbers_only: bool = True
    exclude_single_chars: bool = True
    min_length: int = 2
    max_length: int = 1000
    
    # 自定义过滤规则
    custom_excludes: List[str] = field(default_factory=list)
    custom_patterns: List[str] = field(default_factory=list)

@dataclass
class ProcessingConfig:
    """处理配置"""
    # XML 处理
    preserve_formatting: bool = True
    sort_attributes: bool = False
    pretty_print: bool = True
    
    # CSV 处理
    csv_delimiter: str = ","
    csv_quotechar: str = '"'
    csv_header: bool = True
    
    # 并发处理
    enable_parallel: bool = True
    chunk_size: int = 50
