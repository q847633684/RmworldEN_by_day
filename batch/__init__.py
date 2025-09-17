"""
批量处理模块
处理多个模组的批量操作
"""

from .handler import handle_batch
from .batch_processor import BatchProcessor

__all__ = ["handle_batch", "BatchProcessor"]
