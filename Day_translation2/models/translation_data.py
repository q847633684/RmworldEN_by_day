"""
Day Translation 2 - 翻译数据模型

定义翻译数据结构，包括Keyed翻译、DefInjected翻译等核心数据模型。
遵循提示文件标准：游戏UI术语统一，专有名词对照表支持。
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class TranslationType(Enum):
    """翻译类型枚举"""

    KEYED = "keyed"
    DEFINJECTED = "definjected"
    CORPUS = "corpus"
    BACKSTORY = "backstory"  # 添加缺失的BACKSTORY类型

    def __str__(self) -> str:
        """返回用户友好的类型描述"""
        type_names = {
            self.KEYED: "界面文本",
            self.DEFINJECTED: "游戏内容",
            self.CORPUS: "平行语料",
            self.BACKSTORY: "背景故事",
        }
        return type_names.get(self.value, self.value)


class TranslationStatus(Enum):
    """翻译状态枚举"""

    PENDING = "pending"
    TRANSLATED = "translated"
    REVIEWED = "reviewed"
    APPROVED = "approved"

    def __str__(self) -> str:
        """返回用户友好的状态描述"""
        status_names = {
            self.PENDING: "待翻译",
            self.TRANSLATED: "已翻译",
            self.REVIEWED: "已审核",
            self.APPROVED: "已批准",
        }
        return status_names.get(self.value, self.value)


@dataclass
class TranslationData:
    """基础翻译数据模型"""

    key: str  # 翻译键
    original_text: str  # 原文
    translated_text: str = ""  # 译文
    context: str = ""  # 上下文信息
    file_path: str = ""  # 源文件路径

    # 元数据
    translation_type: TranslationType = TranslationType.KEYED
    status: TranslationStatus = TranslationStatus.PENDING
    tag: str = ""  # XML标签名

    # 质量信息
    confidence: float = 0.0  # 翻译置信度 (0.0-1.0)
    is_machine_translated: bool = False  # 是否机器翻译
    reviewer: str = ""  # 审核者

    # 时间戳
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 附加信息
    notes: str = ""  # 翻译备注
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        from datetime import datetime

        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    @property
    def is_translated(self) -> bool:
        """是否已翻译"""
        return bool(self.translated_text.strip())

    @property
    def relative_file_path(self) -> str:
        """相对文件路径"""
        if self.file_path:
            return str(Path(self.file_path).name)
        return ""

    def update_translation(
        self, translated_text: str, is_machine: bool = False, confidence: float = 0.0
    ):
        """更新翻译"""
        from datetime import datetime

        self.translated_text = translated_text
        self.is_machine_translated = is_machine
        self.confidence = confidence
        self.status = TranslationStatus.TRANSLATED
        self.updated_at = datetime.now().isoformat()

    def to_tuple(self) -> Tuple[str, str, str, str]:
        """转换为元组格式（兼容旧接口）"""
        return (self.key, self.original_text, self.tag, self.file_path)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "key": self.key,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "context": self.context,
            "file_path": self.file_path,
            "translation_type": self.translation_type.value,
            "status": self.status.value,
            "tag": self.tag,
            "confidence": self.confidence,
            "is_machine_translated": self.is_machine_translated,
            "reviewer": self.reviewer,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class KeyedTranslation(TranslationData):
    """Keyed翻译数据模型

    专门用于游戏UI界面文本的翻译数据。
    """

    ui_category: str = ""  # UI分类
    tooltip: str = ""  # 工具提示

    def __post_init__(self):
        super().__post_init__()
        self.translation_type = TranslationType.KEYED


@dataclass
class DefInjectedTranslation(TranslationData):
    """DefInjected翻译数据模型

    专门用于游戏内容定义的翻译数据。
    """

    def_type: str = ""  # 定义类型 (ThingDef, PawnKindDef等)
    def_name: str = ""  # 定义名称
    field_path: str = ""  # 字段路径

    def __post_init__(self):
        super().__post_init__()
        self.translation_type = TranslationType.DEFINJECTED

        # 从key中解析def信息
        if "/" in self.key and "." in self.key:
            try:
                type_and_name, self.field_path = self.key.split(".", 1)
                if "/" in type_and_name:
                    self.def_type, self.def_name = type_and_name.split("/", 1)
            except ValueError:
                pass  # 解析失败时保持默认值

    @property
    def full_def_path(self) -> str:
        """完整的定义路径"""
        return f"{self.def_type}/{self.def_name}"


@dataclass
class CorpusEntry:
    """平行语料条目"""

    source_text: str  # 源语言文本
    target_text: str  # 目标语言文本
    source_language: str = "English"  # 源语言
    target_language: str = "ChineseSimplified"  # 目标语言

    # 来源信息
    source_file: str = ""  # 源文件
    context: str = ""  # 上下文
    quality_score: float = 0.0  # 质量评分

    def to_tuple(self) -> Tuple[str, str]:
        """转换为元组格式"""
        return (self.source_text, self.target_text)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "source_text": self.source_text,
            "target_text": self.target_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "source_file": self.source_file,
            "context": self.context,
            "quality_score": self.quality_score,
        }


@dataclass
class TranslationCollection:
    """翻译数据集合"""

    name: str
    description: str = ""
    translations: List[TranslationData] = field(default_factory=list)

    # 统计信息
    total_count: int = 0
    translated_count: int = 0

    def __post_init__(self):
        """初始化后更新统计信息"""
        self.update_statistics()

    def add_translation(self, translation: TranslationData):
        """添加翻译数据"""
        self.translations.append(translation)
        self.update_statistics()

    def update_statistics(self):
        """更新统计信息"""
        self.total_count = len(self.translations)
        self.translated_count = sum(1 for t in self.translations if t.is_translated)

    @property
    def translation_progress(self) -> float:
        """翻译进度"""
        if self.total_count > 0:
            return self.translated_count / self.total_count
        return 0.0

    def get_by_type(self, translation_type: TranslationType) -> List[TranslationData]:
        """按类型获取翻译数据"""
        return [t for t in self.translations if t.translation_type == translation_type]

    def get_by_status(self, status: TranslationStatus) -> List[TranslationData]:
        """按状态获取翻译数据"""
        return [t for t in self.translations if t.status == status]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "total_count": self.total_count,
            "translated_count": self.translated_count,
            "translation_progress": self.translation_progress,
            "translations": [t.to_dict() for t in self.translations],
        }


# 类型别名，用于向后兼容
TranslationTuple = Tuple[str, str, str, str]  # (key, text, tag, file)
CorpusTuple = Tuple[str, str]  # (source, target)
