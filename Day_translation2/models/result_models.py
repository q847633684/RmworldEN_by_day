"""
Day Translation 2 - 结果数据模型

定义操作结果的数据结构。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class OperationStatus(Enum):
    """操作状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    PENDING = "pending"

class OperationType(Enum):
    """操作类型枚举"""
    EXTRACTION = "extraction"
    TRANSLATION = "translation" 
    IMPORT = "import"
    EXPORT = "export"
    GENERATION = "generation"
    VALIDATION = "validation"
    BATCH_PROCESSING = "batch_processing"

@dataclass
class OperationResult:
    """操作结果基础类"""
    status: OperationStatus
    operation_type: OperationType
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 详细信息
    details: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    
    # 错误信息
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == OperationStatus.SUCCESS
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return bool(self.errors)
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return bool(self.warnings)

@dataclass
class ModProcessResult:
    """Mod处理结果"""
    mod_name: str
    status: OperationStatus
    message: str
    
    # 文件统计
    files_processed: int = 0
    files_success: int = 0
    files_failed: int = 0
    
    # 翻译统计
    translations_extracted: int = 0
    translations_imported: int = 0
    translations_exported: int = 0
    
    # 时间信息
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # 详细信息
    processed_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        """处理耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.files_processed == 0:
            return 0.0
        return self.files_success / self.files_processed

@dataclass
class BatchProcessResult:
    """批量处理结果"""
    operation_type: OperationType
    status: OperationStatus
    message: str
    
    # 批次统计
    total_mods: int = 0
    processed_mods: int = 0
    success_mods: int = 0
    failed_mods: int = 0
    
    # 详细结果
    mod_results: List[ModProcessResult] = field(default_factory=list)
    
    # 时间信息
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """处理耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_mods == 0:
            return 0.0
        return self.success_mods / self.total_mods
