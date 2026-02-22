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

特性：
- 支持 DefInjected 和 Keyed 两种数据类型
- 自动生成变更历史和时间戳
- 提供详细的合并统计和性能监控
- 支持元数据保留和策略选择
"""

from typing import List, Tuple, Any, Dict, Set
import datetime
import os
import html
import re
import time
from utils.logging_config import get_logger, log_data_processing, log_performance


def dedupe_translations_by_key(
    keyed_list: List, def_list: List
) -> Tuple[List, List]:
    """
    多根合并时按 key 去重，保留首次出现。
    避免同一 Keyed/Def 目录被多个根解析到导致重复，或不同根产出相同 key 时重复。
    """
    seen_k, seen_d = set(), set()
    out_k, out_d = [], []
    for item in keyed_list:
        k = item[0] if item else None
        if k is not None and k not in seen_k:
            seen_k.add(k)
            out_k.append(item)
    for item in def_list:
        k = item[0] if item else None
        if k is not None and k not in seen_d:
            seen_d.add(k)
            out_d.append(item)
    return out_k, out_d


class SmartMerger:
    """
    智能合并器类

    用于处理翻译数据的智能合并，支持：
    - 自动补齐数据为标准五元组格式
    - 智能合并输入和输出数据
    - 生成包含历史记录的六元组结果
    """

    def __init__(self, input_data: List[tuple], output_data: List[tuple]) -> None:
        """
        初始化时：
        - 自动补齐为五元组 (key, text, tag, rel_path, en_text)
        - 创建输入和输出数据的映射表
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
        """补齐为五元组（忽略额外的def_type信息）"""
        if not isinstance(item, tuple):
            raise ValueError(f"输入必须是元组类型，实际类型: {type(item)}")

        if len(item) < 4:
            raise ValueError(f"元组长度至少为4，实际长度: {len(item)}")

        if len(item) == 4:
            # 四元组补齐为五元组：(key, text, tag, rel_path) -> (key, text, tag, rel_path, text)
            return (*item[:4], item[1])
        elif len(item) == 5:
            # 五元组直接返回：(key, text, tag, rel_path, en_text)
            return item[:5]
        else:
            # 六元组或更长：只取前5个元素
            if len(item) > 6:
                self.logger.warning("元组长度超过6，截取前5个元素: %s", item)
            return item[:5]

    @staticmethod
    def _normalize_html_entities(text: str) -> str:
        """
        规范化HTML实体，用于文本比较

        Args:
            text: 要规范化的文本

        Returns:
            str: 规范化后的文本
        """
        if not text or not isinstance(text, str):
            return ""

        # 规范化HTML实体
        normalized = html.unescape(text)

        # 处理全角字符（＆ -> &）
        normalized = normalized.replace("＆", "&")

        # 处理XML实体（如 &apos;）
        xml_entities = {
            "&apos;": "'",
            "&quot;": '"',
            "&lt;": "<",
            "&gt;": ">",
            "&amp;": "&",
        }

        for entity, char in xml_entities.items():
            normalized = normalized.replace(entity, char)

        # 规范化空白字符
        normalized = re.sub(r"\s+", " ", normalized.strip())

        return normalized

    @staticmethod
    def smart_merge_translations(
        input_data: list,
        output_data: list,
        include_unchanged: bool = False,
        merge_strategy: str = "output_priority",
        preserve_metadata: bool = True,
        strip_def_type_from_key: bool = False,
        match_by_rel_path: bool = False,
    ) -> list:
        """
        智能合并，默认按 key 匹配。
        - strip_def_type_from_key=True 时，写出用 key 去除 def_type 前缀
        - match_by_rel_path=True 时，按 (key, rel_path) 匹配，输入 rel_path 需已规范为 def_type/文件名.xml
        """
        start_time = time.time()
        logger = get_logger(f"{__name__}.smart_merge_translations")
        SmartMerger._validate_data_format(input_data, "input_data")
        SmartMerger._validate_data_format(output_data, "output_data")

        def _write_key(k: str) -> str:
            return k.split("/", 1)[-1] if strip_def_type_from_key and "/" in k else k

        def _map_key(it: tuple) -> Any:
            k, rp = it[0], (it[3] or "").replace("\\", "/")
            return (k, rp) if match_by_rel_path else k

        input_map: Dict[Any, tuple] = {_map_key(it): it for it in input_data}
        output_map: Dict[Any, List[tuple]] = {}
        for item in output_data:
            mk = _map_key(item)
            output_map.setdefault(mk, []).append(item)

        merged = []
        unchanged_count = 0
        updated_count = 0
        new_count = 0
        today = datetime.date.today().isoformat()
        processed_input_keys: Set[Any] = set()

        for map_key, out_items in output_map.items():
            in_item = input_map.get(map_key)
            key = out_items[0][0] if out_items else (in_item[0] if in_item else "")
            for idx, out_item in enumerate(out_items):
                is_duplicate = len(out_items) > 1 and idx > 0
                if is_duplicate:
                    wk = _write_key(key)
                    merged.append((wk, out_item[1], out_item[2], out_item[3], "", "重复key，需删除"))
                    continue
                if in_item:
                    processed_input_keys.add(map_key)
                    norm_in = SmartMerger._normalize_html_entities(in_item[1])
                    norm_out = SmartMerger._normalize_html_entities(out_item[4])
                    if norm_in == norm_out:
                        unchanged_count += 1
                        if include_unchanged:
                            merged.append((_write_key(key), out_item[1], out_item[2], out_item[3], out_item[4], ""))
                    else:
                        updated_count += 1
                        use_out = preserve_metadata and merge_strategy == "output_priority"
                        old_en = (out_item[4] or "").strip()
                        old_zh = (out_item[1] or "").strip()
                        no_orig_en = not old_en or old_en == old_zh
                        wk = _write_key(key)
                        meta = (out_item[2], out_item[3]) if use_out else (in_item[2], in_item[3])
                        if no_orig_en:
                            merged.append((
                                wk, out_item[1], *meta, in_item[1],
                                f"原中文: '{out_item[1]}', 无原英文；新英文: '{in_item[1]}', 更新于{today}",
                            ))
                        else:
                            merged.append((
                                wk, in_item[1], *meta, in_item[1],
                                f"英文源已更新，待重新翻译；原译文: '{out_item[1]}', 原英文: '{out_item[4]}' -> 新英文: '{in_item[1]}', 更新于{today}",
                            ))

        for map_key, in_item in input_map.items():
            if map_key in processed_input_keys or map_key in output_map:
                continue
            key = in_item[0]
            new_count += 1
            def_type = key.split("/", 1)[0] if "/" in key else ""
            orig_rel = (in_item[3] or "").replace("\\", "/")
            filename = os.path.basename(orig_rel) or (f"{def_type}.xml" if def_type else "def.xml")
            rel_path = f"{def_type}/{filename}" if def_type else orig_rel
            merged.append((
                _write_key(key), in_item[1], in_item[2], rel_path, in_item[4],
                f"翻译内容: '{in_item[1]}',新增于{today}",
            ))

        outdated_count = 0
        _translation_fields: Set[str] = set()
        try:
            from user_config import UserConfigManager
            _translation_fields = UserConfigManager.get_instance().system_config.get_translation_fields() or set()
            _translation_fields = {f.lower() for f in _translation_fields if isinstance(f, str)}
        except Exception:
            pass

        for map_key, out_items in output_map.items():
            if input_map.get(map_key) is not None:
                continue
            key = out_items[0][0] if out_items else (map_key[0] if isinstance(map_key, tuple) else map_key)
            field = key.split(".")[-1].strip() if "." in key else key.strip()
            field_lower = (field or "").lower()
            history_outdated = "过时key，需删除" if field_lower in _translation_fields else "未识别字段，谨慎删除"
            for out_item in out_items:
                outdated_count += 1
                merged.append((_write_key(key), out_item[1], out_item[2], out_item[3], "", history_outdated))

        # 生成详细统计信息
        stats = {
            "total_input": len(input_data),
            "total_output": len(output_data),
            "merged_count": len(merged),
            "unchanged_count": unchanged_count,
            "updated_count": updated_count,
            "new_count": new_count,
            "outdated_count": outdated_count,
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
            outdated_count=stats.get("outdated_count", 0),
            total_input=stats.get("total_input", 0),
        )
        logger.info("智能合并完成: 耗时 %.3f秒, 输出 %d 条记录", duration, len(merged))
        return merged, stats

    @staticmethod
    def _validate_data_format(data: list, data_name: str) -> None:
        """验证数据格式是否正确"""
        if not isinstance(data, list):
            raise ValueError(f"{data_name} 必须是列表类型")

        for i, item in enumerate(data):
            if not isinstance(item, tuple):
                raise ValueError(f"{data_name}[{i}] 必须是元组类型")

            if len(item) not in [4, 5, 6]:
                raise ValueError(
                    f"{data_name}[{i}] 元组长度必须是4、5或6，实际长度: {len(item)}"
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
        logger.info("  过时项目: %d (需删除)", stats.get("outdated_count", 0))
        logger.info("  最终输出项目: %d", stats.get("merged_count", 0))
        logger.info("  合并策略: %s", stats.get("merge_strategy", "unknown"))
        logger.info("  保留元数据: %s", stats.get("preserve_metadata", False))

