"""
翻译器恢复功能基类
提供统一的恢复逻辑实现
"""

import csv
import os
from pathlib import Path
from typing import Optional
from utils.logging_config import get_logger


class ResumeBase:
    """翻译器恢复功能基类"""

    def __init__(self):
        self.logger = get_logger(__name__)

    def can_resume_translation(self, input_csv: str, output_csv: str) -> Optional[str]:
        """
        检查是否可以恢复翻译（基于文件对比）

        Args:
            input_csv: 输入CSV文件路径

        Returns:
            Optional[str]: 可恢复的输出文件路径，如果没有则返回None
        """

        # 检查是否可以恢复
        if self._can_resume_from_files(input_csv, output_csv):
            return output_csv

        return None

    def _can_resume_from_files(self, input_csv: str, output_csv: str) -> bool:
        """
        通过对比CSV文件检查是否可以恢复翻译

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            bool: 是否可以恢复
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(input_csv) or not os.path.exists(output_csv):
                return False

            # 读取输入文件行数
            input_data_lines = self._count_csv_lines(input_csv)
            # 读取输出文件行数
            output_data_lines = self._count_csv_lines(output_csv)

            # 如果输出文件行数小于输入文件，说明可以恢复
            # 但至少要有一行数据（不包括标题行）
            return 0 < output_data_lines < input_data_lines

        except (FileNotFoundError, PermissionError, csv.Error) as e:
            self.logger.debug("检查文件恢复状态失败: %s", e)
            return False

    def get_resume_line_from_files(self, input_csv: str, output_csv: str) -> int:
        """
        通过对比CSV文件获取恢复起始行号

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

        Returns:
            int: 恢复起始行号（从1开始）
        """
        try:
            output_data_lines = self._count_csv_lines(output_csv)
            # 返回下一行需要翻译的行号（从1开始）
            return max(1, output_data_lines + 1)
        except Exception:
            return 1

    def _count_csv_lines(self, csv_file: str) -> int:
        """
        计算CSV文件数据行数（不包括标题行）

        Args:
            csv_file: CSV文件路径

        Returns:
            int: 数据行数
        """
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                lines = list(reader)
                return len(lines) - 1  # 减去标题行
        except Exception:
            return 0

    def _get_resume_row(self, output_file: str, key_column: str) -> int:
        """
        获取恢复起始行号

        Args:
            output_file: 输出文件路径
            key_column: 键列名

        Returns:
            int: 恢复起始行号（从0开始）
        """
        try:
            if not os.path.exists(output_file):
                return 0

            with open(output_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return len(rows)
        except Exception:
            return 0

    def _save_progress(self, output_file: str, current_row: int) -> None:
        """
        保存翻译进度（空实现，子类可重写）

        Args:
            output_file: 输出文件路径
            current_row: 当前行号
        """
        # 默认空实现，子类可以重写此方法
        pass
