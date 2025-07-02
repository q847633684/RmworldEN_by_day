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

    def smart_merge_definjected_translations(
        self, include_unchanged: bool = False
    ) -> List[Tuple[str, Any, Any, Any, Any, Any]]:
        """
        智能合并 DefInjected 翻译：
        - 输入、输出均为五元组(key, test, tag, rel_path, en_test)
        - 返回六元组(key, test, tag, rel_path, en_test, history)
        - 自动跳过非 DefInjected 数据（如 Keyed 四元组）

        Args:
            include_unchanged: 是否包含未变化的项目，默认 False（符合 5.1 增量合并逻辑）
        """
        merged = []
        unchanged_count = 0
        updated_count = 0
        new_count = 0

        for key, in_item in self.input_map.items():
            out_item = self.output_map.get(key)
            if out_item:
                # 5.1 逻辑：key 相同，test 和 EN 相同的情况
                if in_item[1] == out_item[4]:  # 输入的 test == 输出的 en_test
                    unchanged_count += 1
                    if include_unchanged:
                        # 如果需要包含未变化项，保持原有翻译
                        merged.append(
                            (
                                key,
                                out_item[1],  # 保持原有翻译
                                in_item[2],
                                in_item[3],
                                in_item[1],  # 更新 en_test 为当前英文
                                "",  # 无历史记录
                            )
                        )
                    else:
                        continue  # 5.1 逻辑：删除这个参数（不输出）
                else:
                    # 5.1 逻辑：key 相同，test 和 EN 不同，需要更新
                    updated_count += 1
                    merged.append(
                        (
                            key,
                            in_item[1],  # 新的英文文本
                            in_item[2],
                            in_item[3],
                            in_item[1],  # 更新 en_test
                            out_item[1],  # 保留原翻译作为历史记录
                        )
                    )
            else:
                # 5.1 逻辑：key 没有，新增，带 EN 注释
                new_count += 1
                merged.append(
                    (
                        key,
                        in_item[1],
                        in_item[2],
                        in_item[3],
                        in_item[1],
                        "",  # 新增，history为空
                    )
                )

        # 记录合并统计信息
        self._log_merge_stats(
            len(merged), unchanged_count, updated_count, new_count, len(self.input_data)
        )

        return merged

    def _log_merge_stats(
        self,
        merged_count: int,
        unchanged_count: int,
        updated_count: int,
        new_count: int,
        total_input: int,
    ) -> None:
        """记录合并统计信息"""
        logging.info("智能合并统计:")
        logging.info("  总输入项目: %d", total_input)
        logging.info("  未变化项目: %d (跳过)", unchanged_count)
        logging.info("  需要更新项目: %d", updated_count)
        logging.info("  新增项目: %d", new_count)
        logging.info("  输出项目: %d", merged_count)
