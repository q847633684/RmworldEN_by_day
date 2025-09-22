"""
RimWorld 智能翻译合并器

提供高级的翻译数据合并功能，支持多种合并策略和历史记录管理：

核心功能：
- SmartMerger 类：主要的合并器实现
- 自动数据格式规范化（四元组/五元组统一处理）
- 智能合并策略（输入优先/输出优先/智能选择）
- 翻译历史记录和变更追踪

合并策略：
1. 内容无变化：保持原状，跳过处理
2. 内容有更新：替换翻译，保留历史记录
3. 新增内容：添加新翻译，包含英文注释

数据格式：
- 输入：四元组 (key, text, tag, rel_path) 或五元组 (key, text, tag, rel_path, en_text)
- 输出：六元组 (key, text, tag, rel_path, en_text, history)

主要方法：
- smart_merge_translations(): 静态方法，执行智能合并
- create_for_definjected(): 为 DefInjected 数据创建专用合并器
- create_for_keyed(): 为 Keyed 数据创建专用合并器
- get_quality_report(): 生成数据质量报告

特性：
- 支持 DefInjected 和 Keyed 两种数据类型
- 自动生成变更历史和时间戳
- 提供详细的合并统计和性能监控
- 支持元数据保留和策略选择
"""

from typing import List, Tuple, Any, Dict
import datetime
from utils.logging_config import get_logger, log_data_processing, log_performance


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
        self.logger = get_logger(f"{__name__}.SmartMerger")

        self.logger.info(
            "初始化SmartMerger: 输入数据 %d 条, 输出数据 %d 条",
            len(input_data),
            len(output_data),
        )

        self.input_data = [self._normalize_tuple(item) for item in input_data]
        self.output_data = [self._normalize_tuple(item) for item in output_data]
        self.input_map: Dict[str, Tuple[str, Any, Any, Any, Any]] = {
            item[0]: item for item in self.input_data
        }
        self.output_map: Dict[str, Tuple[str, Any, Any, Any, Any]] = {
            item[0]: item for item in self.output_data
        }

        self.logger.debug(
            "数据规范化完成: 输入 %d 条, 输出 %d 条",
            len(self.input_data),
            len(self.output_data),
        )

    def _normalize_tuple(self, item: tuple) -> Tuple[str, Any, Any, Any, Any]:
        """补齐为五元组，并规范化 key"""
        if not isinstance(item, tuple):
            raise ValueError(f"输入必须是元组类型，实际类型: {type(item)}")

        if len(item) < 4:
            raise ValueError(f"元组长度至少为4，实际长度: {len(item)}")

        key = self._normalize_key(item[0])

        if len(item) == 4:
            # 四元组补齐为五元组：(key, test, tag, rel_path) -> (key, test, tag, rel_path, test)
            return (key, item[1], item[2], item[3], item[1])
        elif len(item) == 5:
            # 五元组直接规范化key：(key, test, tag, rel_path, en_test)
            return (key, item[1], item[2], item[3], item[4])
        else:
            # 长度超过5的元组，只取前5个元素
            self.logger.warning("元组长度超过5，截取前5个元素: %s", item)
            return (key, item[1], item[2], item[3], item[4])

    def _normalize_key(self, key: str) -> str:
        """去除 DefType/ 前缀，规范化 key"""
        return key.split("/", 1)[-1] if "/" in key else key

    def merge(
        self, include_unchanged: bool = False
    ) -> List[Tuple[str, Any, Any, Any, Any, str]]:
        """
        执行智能合并操作

        Args:
            include_unchanged: 是否包含未变化的项目

        Returns:
            六元组列表：(key, test, tag, rel_path, en_test, history)
        """
        return SmartMerger.smart_merge_translations(
            self.input_data, self.output_data, include_unchanged
        )

    @staticmethod
    def smart_merge_translations(
        input_data: list,
        output_data: list,
        include_unchanged: bool = False,
        merge_strategy: str = "input_priority",
        preserve_metadata: bool = True,
    ) -> list:
        """
        通用智能合并方法，支持 DefInjected 和 Keyed。
        - 输入、输出均为五元组(key, test, tag, rel_path, en_test)
        - 返回六元组(key, test, tag, rel_path, en_test, history)

        Args:
            input_data: 输入数据列表
            output_data: 输出数据列表
            include_unchanged: 是否包含未变化的项目
            merge_strategy: 合并策略 ("input_priority", "output_priority", "smart")
            preserve_metadata: 是否保留输出数据的元数据（tag, rel_path）
        """
        import time

        start_time = time.time()
        logger = get_logger(f"{__name__}.smart_merge_translations")

        logger.info(
            "开始智能合并: 策略=%s, 保留元数据=%s, 包含未变化=%s",
            merge_strategy,
            preserve_metadata,
            include_unchanged,
        )

        # 验证输入数据格式
        SmartMerger._validate_data_format(input_data, "input_data")
        SmartMerger._validate_data_format(output_data, "output_data")

        input_map = {item[0]: item for item in input_data}
        output_map = {item[0]: item for item in output_data}

        logger.info(
            "数据映射完成: 输入 %d 条, 输出 %d 条", len(input_map), len(output_map)
        )

        merged = []
        unchanged_count = 0
        updated_count = 0
        new_count = 0
        today = datetime.date.today().isoformat()

        # 性能优化：预计算所有key的集合，避免重复查找
        output_keys = set(output_map.keys())

        for key, in_item in input_map.items():
            out_item = output_map.get(key)

            if out_item:
                # 根据设计文档5.1规则：比较input_text和output_en_text
                if in_item[1] == out_item[4]:  # 输入的翻译 == 输出的英文注释
                    unchanged_count += 1
                    if include_unchanged:
                        merged.append(
                            (
                                key,
                                out_item[1],  # 保持现有翻译
                                out_item[2],  # 保持现有tag
                                out_item[3],  # 保持现有rel_path
                                out_item[4],  # 保持现有en_test
                                "",  # 无历史记录
                            )
                        )
                    else:
                        continue
                else:
                    # 翻译内容不同，需要更新
                    updated_count += 1

                    # 根据合并策略选择元数据
                    if preserve_metadata and merge_strategy == "output_priority":
                        # 保留输出数据的元数据
                        tag, rel_path = out_item[2], out_item[3]
                    else:
                        # 使用输入数据的元数据
                        tag, rel_path = in_item[2], in_item[3]

                    merged.append(
                        (
                            key,
                            in_item[1],  # 使用新的翻译
                            tag,  # 根据策略选择tag
                            rel_path,  # 根据策略选择rel_path
                            out_item[4],  # 使用输出数据的英文原文
                            f"原中文: '{out_item[1]}', 原英文: '{out_item[4]}' -> 新英文: '{in_item[1]}',更新于{today}",
                        )
                    )
            else:
                # 新增项目
                new_count += 1
                merged.append(
                    (
                        key,
                        in_item[1],  # 新翻译
                        in_item[2],  # 新tag
                        in_item[3],  # 新rel_path
                        in_item[4],  # 英文原文
                        f"翻译内容: '{in_item[1]}',新增于{today}",
                    )
                )

        # 生成详细统计信息
        stats = {
            "total_input": len(input_data),
            "total_output": len(output_data),
            "merged_count": len(merged),
            "unchanged_count": unchanged_count,
            "updated_count": updated_count,
            "new_count": new_count,
            "merge_strategy": merge_strategy,
            "preserve_metadata": preserve_metadata,
        }

        # 记录性能统计
        duration = time.time() - start_time
        log_performance(
            "smart_merge_translations",
            duration,
            input_count=len(input_data),
            output_count=len(output_map),
            merged_count=len(merged),
        )

        # 记录数据处理统计
        log_data_processing(
            "智能合并",
            len(merged),
            unchanged=unchanged_count,
            updated=updated_count,
            new=new_count,
        )

        SmartMerger._log_merge_stats(
            merged_count=stats.get("merged_count", 0),
            unchanged_count=stats.get("unchanged_count", 0),
            updated_count=stats.get("updated_count", 0),
            new_count=stats.get("new_count", 0),
            total_input=stats.get("total_input", 0),
        )
        logger.info("智能合并完成: 耗时 %.3f秒, 输出 %d 条记录", duration, len(merged))
        return merged

    @staticmethod
    def _validate_data_format(data: list, data_name: str) -> None:
        """验证数据格式是否正确"""
        if not isinstance(data, list):
            raise ValueError(f"{data_name} 必须是列表类型")

        for i, item in enumerate(data):
            if not isinstance(item, tuple):
                raise ValueError(f"{data_name}[{i}] 必须是元组类型")

            if len(item) not in [4, 5]:
                raise ValueError(
                    f"{data_name}[{i}] 元组长度必须是4或5，实际长度: {len(item)}"
                )

            if not isinstance(item[0], str) or not item[0].strip():
                raise ValueError(f"{data_name}[{i}] key 不能为空")

    @staticmethod
    def _log_merge_stats(**stats) -> None:
        """记录合并统计信息"""
        logger = get_logger(f"{__name__}.SmartMerger")
        logger.info("智能合并统计:")
        logger.info("  总输入项目: %d", stats.get("total_input", 0))
        logger.info("  总输出项目: %d", stats.get("total_output", 0))
        logger.info("  未变化项目: %d (跳过)", stats.get("unchanged_count", 0))
        logger.info("  需要更新项目: %d", stats.get("updated_count", 0))
        logger.info("  新增项目: %d", stats.get("new_count", 0))
        logger.info("  最终输出项目: %d", stats.get("merged_count", 0))
        logger.info("  合并策略: %s", stats.get("merge_strategy", "unknown"))
        logger.info("  保留元数据: %s", stats.get("preserve_metadata", False))

    @classmethod
    def create_for_definjected(
        cls, input_data: list, output_data: list
    ) -> "SmartMerger":
        """
        为DefInjected数据创建专门的合并器

        Args:
            input_data: 输入数据（通常是提取的翻译）
            output_data: 输出数据（通常是现有的翻译）

        Returns:
            SmartMerger实例
        """
        return cls(input_data, output_data)

    def get_quality_report(self) -> Dict[str, Any]:
        """
        生成数据质量报告

        Returns:
            包含质量指标的字典
        """
        report = {
            "input_stats": self._analyze_data_quality(self.input_data, "输入数据"),
            "output_stats": self._analyze_data_quality(self.output_data, "输出数据"),
            "key_overlap": len(
                set(self.input_map.keys()) & set(self.output_map.keys())
            ),
            "input_only_keys": len(
                set(self.input_map.keys()) - set(self.output_map.keys())
            ),
            "output_only_keys": len(
                set(self.output_map.keys()) - set(self.input_map.keys())
            ),
        }
        return report

    def _analyze_data_quality(self, data: list, data_name: str) -> Dict[str, Any]:
        """分析数据质量"""
        if not data:
            return {"count": 0, "empty_keys": 0, "empty_translations": 0}

        empty_keys = sum(1 for item in data if not item[0].strip())
        empty_translations = sum(1 for item in data if not item[1].strip())

        return {
            "count": len(data),
            "empty_keys": empty_keys,
            "empty_translations": empty_translations,
            "quality_score": (
                (len(data) - empty_keys - empty_translations) / len(data) if data else 0
            ),
        }

    @classmethod
    def create_for_keyed(cls, input_data: list, output_data: list) -> "SmartMerger":
        """
        为Keyed数据创建专门的合并器

        Args:
            input_data: 输入数据（通常是提取的翻译）
            output_data: 输出数据（通常是现有的翻译）

        Returns:
            SmartMerger实例
        """
        return cls(input_data, output_data)
