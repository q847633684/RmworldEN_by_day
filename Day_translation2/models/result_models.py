"""
Day Translation 2 - 操作结果数据模型

定义操作结果、状态枚举等数据结构，提供统一的操作反馈机制。
遵循提示文件标准：使用PascalCase类命名，提供用户友好的信息。
"""

# 标准库
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# 第三方库
from dataclasses import dataclass, field


class OperationStatus(Enum):
    """操作状态枚举"""

    SUCCESS = "success"
    ERROR = "error"  # 修改为ERROR以匹配测试期望
    FAILED = "failed"  # 保留FAILED作为别名
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    WARNING = "warning"

    def __str__(self) -> str:
        """返回用户友好的状态描述"""
        status_names = {
            OperationStatus.SUCCESS: "成功",
            OperationStatus.ERROR: "错误",
            OperationStatus.FAILED: "失败",
            OperationStatus.PARTIAL: "部分成功",
            OperationStatus.CANCELLED: "已取消",
            OperationStatus.IN_PROGRESS: "进行中",
            OperationStatus.WARNING: "警告",
        }
        return status_names.get(self, self.value)


class OperationType(Enum):
    """操作类型枚举"""

    EXTRACTION = "extraction"
    IMPORT = "import"
    EXPORT = "export"
    TRANSLATION = "translation"
    VALIDATION = "validation"
    GENERATION = "generation"
    BATCH_PROCESSING = "batch_processing"
    WORKFLOW = "workflow"

    def __str__(self) -> str:
        """返回用户友好的操作类型描述"""
        type_names = {
            OperationType.EXTRACTION: "提取",
            OperationType.IMPORT: "导入",
            OperationType.EXPORT: "导出",
            OperationType.TRANSLATION: "翻译",
            OperationType.VALIDATION: "验证",
            OperationType.GENERATION: "生成",
            OperationType.BATCH_PROCESSING: "批量处理",
            OperationType.WORKFLOW: "工作流",
        }
        return type_names.get(self, self.value)


@dataclass
class OperationResult:
    """操作结果数据模型

    提供统一的操作结果反馈，包含状态、消息、详细信息等。
    """

    status: OperationStatus
    operation_type: OperationType
    message: str

    # 可选的详细信息
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 统计信息
    processed_count: int = 0
    success_count: int = 0
    error_count: int = 0

    # 时间信息
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None  # 支持直接设置执行时间

    # 相关文件路径
    input_files: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if self.start_time is None:
            self.start_time = datetime.now()

        # 如果设置了execution_time，自动计算end_time
        if self.execution_time is not None and self.start_time:
            from datetime import timedelta

            self.end_time = self.start_time + timedelta(seconds=self.execution_time)

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == OperationStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == OperationStatus.FAILED

    @property
    def is_partial(self) -> bool:
        """是否部分成功"""
        return self.status == OperationStatus.PARTIAL

    @property
    def duration(self) -> Optional[float]:
        """操作持续时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.processed_count > 0:
            return self.success_count / self.processed_count
        return 0.0

    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0 or self.status == OperationStatus.WARNING

    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.error_count += 1

    def add_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)

    def add_detail(self, key: str, value: Any):
        """添加详细信息"""
        # 如果 details 是列表，转换为字典
        if isinstance(self.details, list):
            # 将现有列表转换为字典
            old_details = self.details.copy()
            self.details = {}
            # 添加原来的列表项作为编号键
            for i, item in enumerate(old_details):
                self.details[f"detail_{i}"] = item

        # 现在可以安全地添加新的键值对
        if isinstance(self.details, dict):
            self.details[key] = value

    def complete(self, status: Optional[OperationStatus] = None):
        """标记操作完成"""
        self.end_time = datetime.now()
        if status:
            self.status = status
        elif not self.is_failed and not self.is_partial:
            # 如果没有明确设置状态，根据错误数量自动判断
            if self.error_count == 0:
                self.status = OperationStatus.SUCCESS
            elif self.success_count > 0:
                self.status = OperationStatus.PARTIAL
            else:
                self.status = OperationStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "operation_type": self.operation_type.value,
            "message": self.message,
            "details": self.details,
            "errors": self.errors,
            "warnings": self.warnings,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "success_rate": self.success_rate,
            "input_files": self.input_files,
            "output_files": self.output_files,
        }

    def get_summary(self) -> str:
        """获取操作摘要"""
        summary_parts = [
            f"操作: {self.operation_type}",
            f"状态: {self.status}",
            f"消息: {self.message}",
        ]

        if self.processed_count > 0:
            summary_parts.append(f"处理: {self.processed_count}项")
            summary_parts.append(f"成功: {self.success_count}项")
            if self.error_count > 0:
                summary_parts.append(f"错误: {self.error_count}项")

        if self.duration:
            summary_parts.append(f"耗时: {self.duration:.2f}秒")

        return " | ".join(summary_parts)

    @classmethod
    def success(
        cls,
        message: str,
        operation_type: OperationType = OperationType.EXTRACTION,
        **kwargs,
    ) -> "OperationResult":
        """创建成功结果"""
        return cls(
            status=OperationStatus.SUCCESS,
            operation_type=operation_type,
            message=message,
            **kwargs,
        )

    @classmethod
    def failed(
        cls,
        message: str,
        operation_type: OperationType = OperationType.EXTRACTION,
        **kwargs,
    ) -> "OperationResult":
        """创建失败结果"""
        return cls(
            status=OperationStatus.FAILED,
            operation_type=operation_type,
            message=message,
            **kwargs,
        )

    @classmethod
    def warning(
        cls,
        message: str,
        operation_type: OperationType = OperationType.EXTRACTION,
        **kwargs,
    ) -> "OperationResult":
        """创建警告结果"""
        return cls(
            status=OperationStatus.WARNING,
            operation_type=operation_type,
            message=message,
            **kwargs,
        )

    def __str__(self) -> str:
        """返回用户友好的字符串表示"""
        parts = [self.message, self.status.name]  # 使用.name获取枚举名称(如SUCCESS)

        if self.processed_count > 0:
            parts.append(f"{self.success_count}/{self.processed_count}")

        return " | ".join(parts)


@dataclass
class BatchResult:
    """批量操作结果"""

    total_items: int
    results: List[OperationResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """成功的操作数量"""
        return sum(1 for r in self.results if r.is_success)

    @property
    def failed_count(self) -> int:
        """失败的操作数量"""
        return sum(1 for r in self.results if r.is_failed)

    @property
    def partial_count(self) -> int:
        """部分成功的操作数量"""
        return sum(1 for r in self.results if r.is_partial)

    @property
    def overall_status(self) -> OperationStatus:
        """整体状态"""
        if self.failed_count == 0:
            return OperationStatus.SUCCESS
        elif self.success_count > 0:
            return OperationStatus.PARTIAL
        else:
            return OperationStatus.FAILED

    def add_result(self, result: OperationResult):
        """添加操作结果"""
        self.results.append(result)

    def get_summary(self) -> str:
        """获取批量操作摘要"""
        return (
            f"批量操作完成: 总计{self.total_items}项, "
            f"成功{self.success_count}项, "
            f"失败{self.failed_count}项, "
            f"部分成功{self.partial_count}项"
        )


@dataclass
class ModProcessResult:
    """模组处理结果"""

    mod_path: str
    mod_name: str
    success: bool
    message: str
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "mod_path": self.mod_path,
            "mod_name": self.mod_name,
            "success": self.success,
            "message": self.message,
            "error": self.error,
            "details": self.details,
        }
