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
    ) -> list:
        """
        通用智能合并方法，支持 DefInjected 和 Keyed。
        - 输入、输出均为五元组(key, text, tag, rel_path, en_text)
        - 返回六元组(key, text, tag, rel_path, en_text, history)

        Args:
            input_data: 输入数据列表
            output_data: 输出数据列表
            include_unchanged: 是否包含未变化的项目
            merge_strategy: 合并策略，("input_priority", "output_priority")，预留；当前调用方固定传 output_priority
            preserve_metadata: 是否保留输出数据的元数据（tag, rel_path），预留；当前固定 True
        """
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

        def _scope_from_rel_path(r: str) -> str:
            p = (r or "").replace("\\", "/").strip()
            return p.split("/")[0] if "/" in p else p

        # 输入按 Def 类型分组：若为六元组 (含 def_type)，则 (key, def_type) -> item，避免不同 Def 类型同 key 互相覆盖
        has_def_type = any(len(it) >= 6 for it in input_data)
        input_map: Dict[Any, tuple] = {}
        if has_def_type:
            for it in input_data:
                input_map[(it[0], it[5])] = it  # (key, def_type)
        else:
            for it in input_data:
                input_map[it[0]] = it

        # 同一 key 可能出现在多个输出文件中（不同 Def 类型），按 key -> [item, ...] 保留全部
        output_map: Dict[str, List[tuple]] = {}
        for item in output_data:
            output_map.setdefault(item[0], []).append(item)

        def _get_in_item(key: str, scope: str):
            if has_def_type:
                return input_map.get((key, scope))
            return input_map.get(key)

        logger.info(
            "数据映射完成: 输入 %d 条(按类型=%s), 输出 %d 条(key 去重后 %d)",
            len(input_data),
            has_def_type,
            len(output_data),
            len(output_map),
        )

        merged = []
        unchanged_count = 0
        updated_count = 0
        new_count = 0
        today = datetime.date.today().isoformat()
        processed_input_keys: Set[Any] = set()  # (key, scope) 或 key，用于最后补「新增」

        for key, out_items in output_map.items():
            # 按 Def 类型分组：同一 key 在不同 Def 类型分别合并，不冲突
            by_scope: Dict[str, List[tuple]] = {}
            for out_item in out_items:
                scope = _scope_from_rel_path(out_item[3])
                by_scope.setdefault(scope, []).append(out_item)
            for scope, items_in_file in by_scope.items():
                in_item = _get_in_item(key, scope)
                for idx, out_item in enumerate(items_in_file):
                    is_duplicate_extra = len(items_in_file) > 1 and idx > 0
                    if is_duplicate_extra:
                        # 同一 Def 类型内重复 key：第二个及以后标「重复key，需删除」
                        # use_out 时用 output 的 tag/rel_path；否则用 input 的（预留，merge_strategy=input_priority 时）
                        _meta = (
                            (out_item[2], out_item[3])
                            if preserve_metadata and merge_strategy == "output_priority"
                            else (in_item[2], in_item[3]) if in_item else (out_item[2], out_item[3])
                        )
                        merged.append((key, out_item[1], *_meta, "", "重复key，需删除"))
                        continue
                    if in_item:
                        processed_input_keys.add((key, scope) if has_def_type else key)
                        normalized_input = SmartMerger._normalize_html_entities(in_item[1])
                        normalized_output = SmartMerger._normalize_html_entities(out_item[4])
                        if normalized_input == normalized_output:
                            unchanged_count += 1
                            if include_unchanged:
                                merged.append(
                                    (key, out_item[1], out_item[2], out_item[3], out_item[4], "")
                                )
                        else:
                            updated_count += 1
                            # True=用 output 的 tag/rel_path；False=用 input 的（预留）
                            use_out_meta = (
                                preserve_metadata and merge_strategy == "output_priority"
                            )
                            old_en = (out_item[4] or "").strip()
                            old_zh = (out_item[1] or "").strip()
                            no_original_en = not old_en or old_en == old_zh
                            if no_original_en:
                                # 输出无英文或英文同中文：保留现有译文，更新 en_text 为新英文
                                merged.append(
                                    (
                                        key,
                                        out_item[1],
                                        out_item[2] if use_out_meta else in_item[2],
                                        out_item[3] if use_out_meta else in_item[3],
                                        in_item[1],
                                        f"原中文: '{out_item[1]}', 无原英文；新英文: '{in_item[1]}', 更新于{today}",
                                    )
                                )
                            else:
                                # 英文源有更新：旧译文已不对应新英文，用新英文占位待重翻，history 保留原译文供参考
                                orig_en_display = f"'{out_item[4]}'"
                                merged.append(
                                    (
                                        key,
                                        in_item[1],
                                        out_item[2] if use_out_meta else in_item[2],
                                        out_item[3] if use_out_meta else in_item[3],
                                        in_item[1],
                                        f"英文源已更新，待重新翻译；原译文: '{out_item[1]}', 原英文: {orig_en_display} -> 新英文: '{in_item[1]}', 更新于{today}",
                                    )
                                )
                    else:
                        # 该 (key, scope) 在输出有、输入无，放到后面「过时」逻辑统一标
                        pass

        # 过时：输出中有、输入中该 key+scope 无的，下面循环会处理
        # 新增：输入中有、输出中该 key+scope 无的
        if has_def_type:
            for (key, scope), in_item in input_map.items():
                if (key, scope) in processed_input_keys:
                    continue
                out_items = output_map.get(key)
                if out_items and any(_scope_from_rel_path(o[3]) == scope for o in out_items):
                    continue
                new_count += 1
                merged.append(
                    (
                        key,
                        in_item[1],
                        in_item[2],
                        in_item[3],
                        in_item[4],
                        f"翻译内容: '{in_item[1]}',新增于{today}",
                    )
                )
        else:
            for key, in_item in input_map.items():
                if key in processed_input_keys:
                    continue
                if key in output_map:
                    continue
                new_count += 1
                merged.append(
                    (
                        key,
                        in_item[1],
                        in_item[2],
                        in_item[3],
                        in_item[4],
                        f"翻译内容: '{in_item[1]}',新增于{today}",
                    )
                )

        # 输出中有、输入（Defs）中该 key+scope 没有的：标「过时key，需删除」或「未识别字段，谨慎删除」
        outdated_count = 0
        _translation_fields: Set[str] = set()
        try:
            from user_config import UserConfigManager
            _translation_fields = UserConfigManager.get_instance().system_config.get_translation_fields() or set()
            _translation_fields = {f.lower() for f in _translation_fields if isinstance(f, str)}
        except Exception:  # 配置不可用时全部标为过时
            _translation_fields = set()

        for key, out_items in output_map.items():
            field = key.split(".")[-1].strip() if "." in key else key.strip()
            field_lower = (field or "").lower()
            history_outdated = (
                "过时key，需删除"
                if field_lower in _translation_fields
                else "未识别字段，谨慎删除"
            )
            for out_item in out_items:
                scope = _scope_from_rel_path(out_item[3])
                if _get_in_item(key, scope) is not None:
                    continue  # 该 (key, scope) 在输入中有，已在上方合并过
                outdated_count += 1
                merged.append(
                    (key, out_item[1], out_item[2], out_item[3], "", history_outdated)
                )

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

