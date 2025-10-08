"""
占位符保护功能，用于保护翻译中的占位符
记录占位符，和恢复占位符
1.保护占位符和保护词典
test，创建占位符文件，创建一个字典，把text列中的占位符保护起来，同时记录key值和占位符对应的value值，生成占位符处理后的csv文件，提供阿里云翻译。
2.恢复占位符和恢复词典
test，用记录key值和占位符对应的value值把translated列中的占位符恢复起来，同时恢复成人内容
"""

import csv
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from utils.logging_config import get_logger
from utils.ui_style import ui

logger = get_logger(__name__)


class PlaceholderManager:
    """占位符管理器"""

    def __init__(self, dictionary_type: str = "adult"):
        """
        初始化占位符管理器

        Args:
            dictionary_type: 词典类型 (adult, general, game, artist)
        """
        self.placeholder_map: Dict[str, Dict[str, str]] = {}
        self.dictionary_type = dictionary_type
        self.dictionary = self._load_dictionary()

    def protect_csv_file(
        self, csv_file: str
    ) -> Tuple[bool, Dict[str, Dict[str, str]], str]:
        """
        保护CSV文件中的占位符

        Args:
            csv_file: CSV文件路径

        Returns:
            Tuple[bool, Dict[str, Dict[str, str]], str]: (是否成功, 占位符映射, 保护后的文本字段名)
        """
        try:
            import csv
            from pathlib import Path

            if not Path(csv_file).exists():
                logger.error("CSV文件不存在: %s", csv_file)
                return False, {}, ""

            protected_count = 0
            total_count = 0
            logger.info("开始保护CSV文件中的占位符")
            logger.info("CSV文件路径: %s", csv_file)

            # 读取所有数据到内存
            rows = []
            with open(csv_file, "r", encoding="utf-8") as infile:
                reader = csv.DictReader(infile)
                # 过滤掉None字段名
                fieldnames = (
                    [f for f in reader.fieldnames if f is not None]
                    if reader.fieldnames
                    else []
                )

                # 确保包含所有必要字段
                required_fields = [
                    "key",
                    "text",
                    "tag",
                    "file",
                    "type",
                    "protected_text",
                ]
                for field in required_fields:
                    if field not in fieldnames:
                        fieldnames.append(field)

                for row in reader:
                    total_count += 1

                    # 获取key值
                    csv_key = row.get("key", f"row_{total_count}")

                    # 获取text内容
                    text = row.get("text", "")

                    if text:
                        # 使用protect_text保护占位符
                        protected_text, all_placeholders = self.protect_text(
                            text, csv_key
                        )

                        # 添加新的字段存储保护后的内容
                        row["protected_text"] = protected_text

                        # 记录保护信息
                        if all_placeholders:
                            protected_count += 1
                            logger.debug(
                                "保护了 %s 的 %d 个占位符: %s",
                                csv_key,
                                len(all_placeholders),
                                all_placeholders,
                            )

                    # 确保必要字段存在
                    if "tag" not in row:
                        row["tag"] = ""
                    if "file" not in row:
                        row["file"] = ""
                    if "type" not in row:
                        row["type"] = ""
                    if "protected_text" not in row:
                        row["protected_text"] = ""

                    rows.append(row)

            # 写回文件
            with open(csv_file, "w", encoding="utf-8", newline="") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            ui.print_success(
                f"✅ CSV文件保护完成: {protected_count}/{total_count} 条记录"
            )
            logger.info("CSV文件保护完成: %d/%d 条记录", protected_count, total_count)
            return True, self.placeholder_map.copy(), "protected_text"

        except Exception as e:
            logger.error("CSV文件保护失败: %s", e)
            ui.print_error(f"❌ CSV文件保护失败: {e}")
            return False, {}, ""

    def restore_csv_file(
        self,
        csv_file: str,
        placeholder_map: Dict[str, Dict[str, str]],
    ) -> bool:
        """
        恢复CSV文件中的占位符

        Args:
            csv_file: CSV文件路径（直接修改原文件）
            placeholder_map: 占位符映射字典

        Returns:
            bool: 是否成功
        """
        try:
            import csv
            from pathlib import Path

            if not Path(csv_file).exists():
                logger.error("CSV文件不存在: %s", csv_file)
                return False

            restored_count = 0
            total_count = 0
            logger.info("开始恢复CSV文件中的占位符")
            logger.info("占位符映射: %s", placeholder_map)
            logger.info("CSV文件路径: %s", csv_file)
            # 读取所有数据到内存
            rows = []
            with open(csv_file, "r", encoding="utf-8") as infile:
                reader = csv.DictReader(infile)
                # 过滤掉None字段名
                fieldnames = (
                    [f for f in reader.fieldnames if f is not None]
                    if reader.fieldnames
                    else []
                )

                for row in reader:
                    total_count += 1
                    csv_key = row.get("key", f"row_{total_count}")

                    # 恢复translated列中的占位符
                    if "translated" in row and row["translated"]:
                        # 临时设置占位符映射
                        original_map = self.placeholder_map.copy()
                        self.placeholder_map = placeholder_map

                        restored_text = self.restore_text(row["translated"], csv_key)

                        # 恢复原始映射
                        self.placeholder_map = original_map

                        if restored_text != row["translated"]:
                            row["translated"] = restored_text
                            restored_count += 1

                    rows.append(row)

            # 写回文件
            with open(csv_file, "w", encoding="utf-8", newline="") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            ui.print_success(f"✅ CSV文件恢复完成: {restored_count} 条记录")
            logger.info("CSV文件恢复完成: %d 条记录", restored_count)
            return True

        except Exception as e:
            logger.error("CSV文件恢复失败: %s", e)
            ui.print_error(f"❌ CSV文件恢复失败: {e}")
            return False

    def protect_text(
        self, text: str, csv_key: str = "single_text"
    ) -> Tuple[str, List[str]]:
        """
        保护单个文本中的占位符和成人内容

        Args:
            text: 要保护的文本
            csv_key: CSV行的键值（用于占位符映射）

        Returns:
            Tuple[str, List[str]]: (保护后的文本, 占位符列表)
        """
        if not text or not isinstance(text, str):
            return text, []

        # 初始化该行的占位符映射
        if csv_key not in self.placeholder_map:
            self.placeholder_map[csv_key] = {}

        protected_text = text

        # 步骤1: 保护占位符
        all_placeholders = []
        protected_text, placeholders = self._protect_placeholders_in_text(
            protected_text, csv_key
        )
        all_placeholders.extend(placeholders)

        # 步骤2: 保护成人内容词汇
        protected_text, used_dict = self._protect_adult_content(protected_text)
        if used_dict:
            logger.debug("保护了成人内容词汇")

        return protected_text, all_placeholders

    def restore_text(self, text: str, csv_key: str = "single_text") -> str:
        """
        恢复单个文本中的占位符和成人内容

        Args:
            text: 包含占位符的文本
            csv_key: CSV行的键值（用于占位符映射）

        Returns:
            str: 恢复后的文本
        """
        if not text:
            return text

        restored_text = text

        # 步骤1: 恢复占位符
        restored_text = self._restore_placeholders_in_text(restored_text, csv_key)

        # 步骤2: 翻译成人内容词汇（直接翻译英文成人词汇）
        restored_text = self._translate_remaining_adult_words(restored_text)

        return restored_text

    def _load_dictionary(self):
        """加载词典文件"""
        try:
            # 构建词典文件路径
            config_path = Path(__file__).parent.parent.parent / "user_config" / "config"
            dictionary_file = config_path / f"{self.dictionary_type}_dictionary.yaml"

            if not dictionary_file.exists():
                logger.warning("词典文件不存在: %s", dictionary_file)
                return {}

            with open(dictionary_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 提取所有词汇
            dictionary = {}
            for category, category_data in data.items():
                if isinstance(category_data, dict) and "entries" in category_data:
                    entries = category_data["entries"]
                    if isinstance(entries, list):
                        for entry in entries:
                            if (
                                isinstance(entry, dict)
                                and "english" in entry
                                and "chinese" in entry
                            ):
                                english_word = entry["english"]
                                dictionary[english_word] = {
                                    "chinese": entry["chinese"],
                                    "priority": entry.get("priority", "medium"),
                                }

            self.dictionary = dictionary
            logger.info(
                "已加载%s词典，共%d个词汇", self.dictionary_type, len(self.dictionary)
            )
            return self.dictionary

        except Exception as e:
            logger.error("加载词典失败: %s", e)
            import traceback

            logger.error("详细错误信息: %s", traceback.format_exc())
            self.dictionary = {}
            return self.dictionary

    def _protect_adult_content(self, text: str) -> Tuple[str, bool]:
        """
        保护文本中的成人内容词汇

        Args:
            text: 要保护的文本

        Returns:
            Tuple[str, bool]: (保护后的文本, 是否使用了词典)
        """
        if not text or not isinstance(text, str) or not self.dictionary:
            return text, False

        import re

        text_lower = text.lower()
        used_custom_dict = False
        protected_text = text

        # 按优先级排序的词汇（长词汇优先，避免部分匹配问题）
        sorted_entries = sorted(
            self.dictionary.items(), key=lambda x: len(x[0]), reverse=True
        )

        for english_word, entry_data in sorted_entries:
            if english_word in text_lower:
                # 使用正则表达式进行精确匹配
                pattern = r"\b" + re.escape(english_word) + r"\b"
                if re.search(pattern, text_lower):
                    # 用ALIMT标签保护英文原文，等待后续翻译
                    protected_english = f"<ALIMT >{english_word}</ALIMT>"
                    protected_text = re.sub(
                        pattern, protected_english, protected_text, flags=re.IGNORECASE
                    )
                    used_custom_dict = True
                    logger.debug(
                        "保护英文原文: %s -> %s",
                        english_word,
                        protected_english,
                    )

        return protected_text, used_custom_dict

    def _protect_placeholders_in_text(
        self, text: str, csv_key: str
    ) -> Tuple[str, List[str]]:
        """
        保护文本中的占位符

        Args:
            text: 要保护的文本
            csv_key: CSV行的键值

        Returns:
            Tuple[str, List[str]]: (保护后的文本, 占位符列表)
        """
        if not text or not isinstance(text, str):
            return text, []

        # 定义保护模式（与Java代码保持一致）
        patterns = [
            r"\\n",  # \n 换行符
            r"\[[^\]]+\]",  # [xxx]
            r"\{[^}]+\}%",  # {VALUE}%, {COUNT}% 等带百分号的占位符（必须先匹配，避免被通用模式截断）
            r"\{[^}]+\}",  # {所有内容} - 包括 {0}, {0_labelShort}, {RAPIST}, {RAPIST_possessive} 等
            r"%[sdif]",  # %s, %d, %i, %f
            r"</?(?!ALIMT\s*>)[^>]+>",  # <color> 或 <br>，但排除ALIMT标签
            r"[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)",  # 函数调用
            r"[a-zA-Z_][a-zA-Z0-9_]*->",  # 任意前缀-> 格式，如 r_logentry->, sent->, name-> 等
            r"\bpawn\b",  # pawn 游戏术语
        ]

        protected_text = text
        placeholders = []
        idx = 1

        # 首先标准化换行符
        protected_text = protected_text.replace("\r\n", "\\n").replace("\n", "\\n")

        # 合并所有模式为一个正则表达式
        combined_pattern = "|".join(f"({pattern})" for pattern in patterns)

        # 一次性匹配所有模式
        matches = list(re.finditer(combined_pattern, protected_text))

        # 只有当有匹配的占位符时才记录到placeholder_map
        if matches:
            # 初始化该行的占位符映射
            if csv_key not in self.placeholder_map:
                self.placeholder_map[csv_key] = {}

            # 从后往前替换，避免位置偏移
            for match in reversed(matches):
                placeholder_text = match.group()
                # 记录占位符映射
                placeholder_id = f"PH_{idx}"
                self.placeholder_map[csv_key][placeholder_id] = placeholder_text
                placeholders.append(placeholder_text)

                # 用ALIMT标签保护
                alimt_tag = f"<ALIMT >({placeholder_id})</ALIMT>"

                start, end = match.span()
                protected_text = (
                    protected_text[:start] + alimt_tag + protected_text[end:]
                )
                idx += 1

        return protected_text, placeholders

    def _translate_remaining_adult_words(self, text: str) -> str:
        """
        翻译文本中剩余的英文成人词汇

        Args:
            text: 要翻译的文本

        Returns:
            str: 翻译后的文本
        """
        if not self.dictionary or not text:
            return text

        import re

        text_lower = text.lower()
        translated_text = text

        # 按优先级排序的词汇（长词汇优先，避免部分匹配问题）
        sorted_entries = sorted(
            self.dictionary.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )

        for english_word, entry_data in sorted_entries:
            if english_word in text_lower:
                # 使用正则表达式进行精确匹配，支持中英文混合文本
                # 匹配英文词汇，前后可以是中文、标点符号或边界
                pattern = r"(?<![a-zA-Z])" + re.escape(english_word) + r"(?![a-zA-Z])"
                if re.search(pattern, text_lower):
                    # 获取翻译和优先级
                    chinese_word = entry_data["chinese"]
                    priority = entry_data.get("priority", "medium")

                    # 处理多个翻译选项
                    if "|" in chinese_word:
                        translations = [t.strip() for t in chinese_word.split("|")]
                        selected_translation = self._select_translation_by_priority(
                            translations, priority
                        )
                        logger.debug(
                            "翻译英文成人词汇: %s -> %s (从 %s 中选择，优先级: %s)",
                            english_word,
                            selected_translation,
                            translations,
                            priority,
                        )
                    else:
                        selected_translation = chinese_word
                        logger.debug(
                            "翻译英文成人词汇: %s -> %s (优先级: %s)",
                            english_word,
                            selected_translation,
                            priority,
                        )

                    # 直接替换为中文翻译
                    translated_text = re.sub(
                        pattern,
                        selected_translation,
                        translated_text,
                        flags=re.IGNORECASE,
                    )
                    text_lower = translated_text.lower()  # 更新小写版本

        return translated_text

    def _select_translation_by_priority(self, translations: list, priority: str) -> str:
        """
        根据优先级选择翻译

        Args:
            translations: 翻译选项列表
            priority: 优先级 (high, medium, low)

        Returns:
            str: 选择的翻译
        """
        if not translations:
            return ""

        # 优先级映射
        priority_map = {
            "high": 0,  # 高优先级，选择第一个
            "medium": 1,  # 中优先级，选择中间
            "low": -1,  # 低优先级，选择最后一个
        }

        priority_index = priority_map.get(priority, 1)  # 默认中优先级

        if priority_index == 0:  # high - 选择第一个
            return translations[0]
        elif priority_index == -1:  # low - 选择最后一个
            return translations[-1]
        else:  # medium - 选择中间
            middle_index = len(translations) // 2
            return translations[middle_index]

    def _restore_placeholders_in_text(self, text: str, csv_key: str) -> str:
        """
        恢复文本中的占位符

        Args:
            text: 包含占位符的文本
            csv_key: CSV行的键值

        Returns:
            str: 恢复后的文本
        """
        if not text or csv_key not in self.placeholder_map:
            return text

        restored_text = text
        placeholder_map = self.placeholder_map[csv_key]

        # 恢复占位符
        for placeholder_id, original_value in placeholder_map.items():
            # 处理直接格式的占位符（如 (PH_1)）
            direct_pattern = f"({placeholder_id})"
            restored_text = restored_text.replace(direct_pattern, original_value)

        # 恢复换行符
        restored_text = restored_text.replace("\\n", "\n")

        return restored_text
