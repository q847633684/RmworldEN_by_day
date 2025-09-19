"""
批量处理器 - 处理多个模组的批量操作
"""

import logging
from utils.logging_config import get_logger, log_error_with_context
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from colorama import Fore, Style

from utils.config import get_config
from utils.path_manager import PathManager
from dataclasses import dataclass

CONFIG = get_config()


@dataclass
class ModProcessResult:
    """模组处理结果"""

    mod_dir: str
    success: bool
    error: Optional[str] = None
    config_generated: bool = False
    xml_updated: bool = False
    files_processed: int = 0
    files_updated: int = 0
    processing_time: float = 0.0


class BatchProcessor:
    """批量处理多个模组的翻译任务"""

    def __init__(self):
        """初始化 BatchProcessor"""
        self.logger = get_logger(f"{__name__}.BatchProcessor")
        self._results: Dict[str, ModProcessResult] = {}
        self.logger.debug("初始化 BatchProcessor")

    def _show_processing_summary(self) -> None:
        """显示处理结果统计"""
        if not self._results:
            return

        total_mods = len(self._results)
        successful_mods = sum(1 for r in self._results.values() if r.success)
        failed_mods = total_mods - successful_mods

        total_files_processed = sum(r.files_processed for r in self._results.values())
        total_files_updated = sum(r.files_updated for r in self._results.values())
        total_time = sum(r.processing_time for r in self._results.values())

        print(f"\n{Fore.BLUE}=== 处理结果统计 ==={Style.RESET_ALL}")
        print(f"总模组数: {total_mods}")
        print(f"成功: {Fore.GREEN}{successful_mods}{Style.RESET_ALL}")
        print(f"失败: {Fore.RED}{failed_mods}{Style.RESET_ALL}")
        print(f"处理文件数: {total_files_processed}")
        print(f"更新文件数: {total_files_updated}")
        print(f"总处理时间: {total_time:.2f}秒")

        if failed_mods > 0:
            print(f"\n{Fore.RED}=== 失败详情 ==={Style.RESET_ALL}")
            for mod_dir, result in self._results.items():
                if not result.success:
                    print(f"{Path(mod_dir).name}: {result.error}")

        print(f"{Fore.BLUE}==================={Style.RESET_ALL}\n")
