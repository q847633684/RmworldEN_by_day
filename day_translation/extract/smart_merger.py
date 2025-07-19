"""
智能合并器模块

该模块提供 SmartMerger 类，用于智能合并翻译数据，特别是处理 DefInjected 翻译的合并逻辑。

主要功能：
- 自动规范化翻译数据格式（补齐为五元组）
- 智能合并输入和输出翻译数据
- 处理翻译历史记录和变更追踪
"""

import logging
from typing import List, Tuple, Any, Dict
import datetime


class SmartMerger:
    """
    智能合并器类

    用于处理翻译数据的智能合并，支持：
    - 自动补齐数据为标准五元组格式
    - 规范化 key（去除 DefType/ 前缀）
    - 智能合并输入和输出数据
    - 生成包含历史记录的六元组结果
    """

    def __init__(self, input_data: List[tuple], output_data: List[tuple]) -> None:
        """
        初始化时：
        - 自动补齐为五元组 (key, test, tag, rel_path, en_test)
        - 统一规范化 key（去除 DefType/ 前缀）
        """
        self.input_data = [self._normalize_tuple(item) for item in input_data]
        self.output_data = [self._normalize_tuple(item) for item in output_data]
        self.input_map: Dict[str, Tuple[str, Any, Any, Any, Any]] = {
            item[0]: item for item in self.input_data
        }
        self.output_map: Dict[str, Tuple[str, Any, Any, Any, Any]] = {
            item[0]: item for item in self.output_data
        }

    def _normalize_tuple(self, item: tuple) -> Tuple[str, Any, Any, Any, Any]:
        """补齐为五元组，并规范化 key"""
        key = self._normalize_key(item[0])
        if len(item) == 4:
            return (key, item[1], item[2], item[3], item[1])  # en_test 用 test 填充
        elif len(item) == 5:
            return (key, item[1], item[2], item[3], item[4])
        else:
            raise ValueError(f"不支持的元组长度: {len(item)}，内容: {item}")

    def _normalize_key(self, key: str) -> str:
        """去除 DefType/ 前缀，规范化 key"""
        return key.split("/", 1)[-1] if "/" in key else key

    @staticmethod
    def smart_merge_translations(
        input_data: list,
        output_data: list,
        include_unchanged: bool = False,
    ) -> list:
        """
        通用智能合并方法，支持 DefInjected 和 Keyed。
        - 输入、输出均为五元组(key, test, tag, rel_path, en_test)
        - 返回六元组(key, test, tag, rel_path, en_test, history)
        """
        input_map = {item[0]: item for item in input_data}
        output_map = {item[0]: item for item in output_data}
        print(f"输入数据：{len(input_map)} 条")
        print(f"输出数据：{len(output_map)} 条")
        merged = []
        unchanged_count = 0
        updated_count = 0
        new_count = 0
        today = datetime.date.today().isoformat()
        for key, in_item in input_map.items():
            out_item = output_map.get(key)
            if out_item:
                if in_item[1] == out_item[4]:  # 输入的 test == 输出的 en_test
                    unchanged_count += 1
                    if include_unchanged:
                        merged.append(
                            (
                                key,
                                out_item[1],
                                in_item[2],
                                in_item[3],
                                in_item[1],
                                "",
                            )
                        )
                    else:
                        continue
                else:
                    updated_count += 1
                    merged.append(
                        (
                            key,
                            in_item[1],
                            in_item[2],
                            in_item[3],
                            in_item[1],
                            f"HISTORY: 原翻译内容：{out_item[1]}，替换于{today}",
                        )
                    )
            else:
                new_count += 1
                merged.append((key, in_item[1], in_item[2], in_item[3], in_item[1], ""))
        SmartMerger._log_merge_stats(
            len(merged), unchanged_count, updated_count, new_count, len(input_data)
        )
        return merged

    @staticmethod
    def _log_merge_stats(
        merged_count: int,
        unchanged_count: int,
        updated_count: int,
        new_count: int,
        input_data: int,
    ) -> None:
        """记录合并统计信息"""
        logging.info("智能合并统计:")
        logging.info("  总输入项目: %d", input_data)
        logging.info("  未变化项目: %d (跳过)", unchanged_count)
        logging.info("  需要更新项目: %d", updated_count)
        logging.info("  新增项目: %d", new_count)
        logging.info("  输出项目: %d", merged_count)
