"""
Day Translation 2 - 翻译数据模型

定义翻译数据的结构和类型。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class TranslationData:
    """翻译数据基础类"""
    key: str
    original: str
    translation: str
    context: Optional[str] = None
    file_path: Optional[str] = None
    
    def __post_init__(self):
        """数据校验"""
        if not self.key:
            raise ValueError("Translation key cannot be empty")
        if not self.original:
            raise ValueError("Original text cannot be empty")

@dataclass
class KeyedTranslation(TranslationData):
    """Keyed 类型的翻译数据"""
    section: Optional[str] = None
    
@dataclass
class DefInjectedTranslation(TranslationData):
    """DefInjected 类型的翻译数据"""
    def_type: str = ""
    field_name: str = ""
    def_name: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.def_type:
            raise ValueError("DefType cannot be empty")
        if not self.field_name:
            raise ValueError("Field name cannot be empty")

@dataclass
class TranslationBatch:
    """翻译批次数据"""
    translations: List[TranslationData]
    source_file: str
    target_file: str
    batch_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.translations:
            raise ValueError("Translation batch cannot be empty")
        if not self.source_file:
            raise ValueError("Source file cannot be empty")
        if not self.target_file:
            raise ValueError("Target file cannot be empty")

# 类型别名
TranslationDict = Dict[str, str]
TranslationList = List[TranslationData]
