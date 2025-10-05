"""
词典翻译处理器
处理翻译API无法处理的敏感内容，使用自定义词典进行翻译
支持成人内容和游戏内容两种词典类型
"""

try:
    import yaml
except ImportError:
    yaml = None
from pathlib import Path
from typing import Dict, Optional, Tuple
from utils.logging_config import get_logger
from utils.ui_style import ui

logger = get_logger(__name__)


class DictionaryTranslator:
    """词典翻译器"""

    def __init__(
        self, dictionary_type: str = "adult", dictionary_path: Optional[str] = None
    ):
        """
        初始化词典翻译器

        Args:
            dictionary_type: 词典类型 ("adult" 或 "game")
            dictionary_path: 自定义词典文件路径
        """
        self.dictionary_type = dictionary_type
        self.dictionary = {}
        self.dictionary_path = dictionary_path or self._get_default_dictionary_path()
        self._load_dictionary()

    def _get_default_dictionary_path(self) -> str:
        """获取默认词典路径"""
        filename = f"{self.dictionary_type}_dictionary.yaml"
        # 从当前文件路径向上找到项目根目录
        current_file = Path(__file__).resolve()
        # translate/core/dictionary_translator.py -> 项目根目录
        project_root = current_file.parent.parent.parent
        return str(project_root / "user_config" / "config" / filename)

    def _load_dictionary(self) -> None:
        """加载自定义词典"""
        try:
            if not Path(self.dictionary_path).exists():
                logger.warning(
                    f"{self.dictionary_type}词典文件不存在: %s", self.dictionary_path
                )
                return

            if yaml is None:
                logger.error("yaml库未安装，无法加载自定义词典")
                return

            with open(self.dictionary_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 加载词典（新格式）
            total_entries = 0
            for category_name, category_data in data.items():
                if isinstance(category_data, dict) and "entries" in category_data:
                    for entry in category_data["entries"]:
                        english = entry.get("english", "").lower().strip()
                        chinese = entry.get("chinese", "").strip()
                        priority = entry.get("priority", "medium")

                        if english and chinese:
                            # 存储完整的条目信息，包括优先级
                            self.dictionary[english] = {
                                "chinese": chinese,
                                "priority": priority,
                            }
                            total_entries += 1

            if total_entries > 0:
                logger.info(
                    "已加载 %d 个%s内容翻译条目", total_entries, self.dictionary_type
                )
            else:
                logger.warning("词典文件中未找到%s内容翻译条目", self.dictionary_type)

        except (OSError, IOError, yaml.YAMLError) as e:
            logger.error("加载自定义词典失败: %s", e)

    def translate_text(self, text: str) -> Tuple[str, bool]:
        """
        翻译文本，优先使用自定义词典，支持ALIMT标签保护

        Args:
            text: 要翻译的文本

        Returns:
            Tuple[str, bool]: (翻译后的文本, 是否使用了自定义词典)
        """
        if not text or not isinstance(text, str):
            return text, False

        # 检查是否包含成人内容词汇
        import re

        text_lower = text.lower()
        used_custom_dict = False
        translated_text = text

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
                    translated_text = re.sub(
                        pattern, protected_english, translated_text, flags=re.IGNORECASE
                    )
                    used_custom_dict = True
                    logger.debug(
                        "保护英文原文: %s -> %s",
                        english_word,
                        protected_english,
                    )

        return translated_text, used_custom_dict

    def translate_protected_content(self, text: str) -> str:
        """
        翻译文本中的成人内容（阿里云翻译后，直接翻译英文内容）

        Args:
            text: 要翻译的文本

        Returns:
            str: 翻译后的文本
        """
        if not text or not isinstance(text, str):
            return text

        import re

        text_lower = text.lower()
        translated_text = text

        # 按优先级排序的词汇（长词汇优先，避免部分匹配问题）
        sorted_entries = sorted(
            self.dictionary.items(), key=lambda x: len(x[0]), reverse=True
        )

        for english_word, entry_data in sorted_entries:
            if english_word in text_lower:
                # 使用正则表达式进行精确匹配
                pattern = r"\b" + re.escape(english_word) + r"\b"
                if re.search(pattern, text_lower):
                    # 获取翻译和优先级
                    chinese_word = entry_data["chinese"]
                    priority = entry_data.get("priority", "medium")

                    # 处理多个翻译选择（用|分隔），根据优先级选择
                    if "|" in chinese_word:
                        translations = [t.strip() for t in chinese_word.split("|")]
                        selected_translation = self._select_translation_by_priority(
                            translations, priority
                        )
                        logger.debug(
                            "翻译成人内容: %s -> %s (优先级: %s)",
                            english_word,
                            selected_translation,
                            priority,
                        )
                    else:
                        selected_translation = chinese_word
                        logger.debug(
                            "翻译成人内容: %s -> %s",
                            english_word,
                            selected_translation,
                        )

                    # 直接替换为中文翻译
                    translated_text = re.sub(
                        pattern,
                        selected_translation,
                        translated_text,
                        flags=re.IGNORECASE,
                    )

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

    def translate_csv_file(
        self, input_csv: str, output_csv: str, mode: str = "protect"
    ) -> bool:
        """
        翻译CSV文件中的内容

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径
            mode: 处理模式 ("protect" 保护英文原文, "translate" 翻译保护内容)

        Returns:
            bool: 是否成功
        """
        try:
            import csv

            if not Path(input_csv).exists():
                logger.error("输入CSV文件不存在: %s", input_csv)
                return False

            translated_count = 0
            total_count = 0

            with open(input_csv, "r", encoding="utf-8") as infile, open(
                output_csv, "w", encoding="utf-8", newline=""
            ) as outfile:

                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in reader:
                    total_count += 1

                    # 处理text列
                    if "text" in row and row["text"]:
                        original_text = row["text"]
                        if mode == "protect":
                            # 保护模式：用ALIMT标签保护英文原文
                            translated_text, used_dict = self.translate_text(
                                original_text
                            )
                            if used_dict:
                                row["text"] = translated_text
                                translated_count += 1
                        elif mode == "translate":
                            # 翻译模式：翻译ALIMT标签内的内容
                            translated_text = self.translate_protected_content(
                                original_text
                            )
                            if translated_text != original_text:
                                row["text"] = translated_text
                                translated_count += 1

                    # 处理translated列（如果存在）
                    if "translated" in row and row["translated"]:
                        original_translated = row["translated"]
                        if mode == "protect":
                            # 保护模式：用ALIMT标签保护英文原文
                            translated_translated, used_dict = self.translate_text(
                                original_translated
                            )
                            if used_dict:
                                row["translated"] = translated_translated
                                translated_count += 1
                        elif mode == "translate":
                            # 翻译模式：翻译ALIMT标签内的内容
                            translated_translated = self.translate_protected_content(
                                original_translated
                            )
                            if translated_translated != original_translated:
                                row["translated"] = translated_translated
                                translated_count += 1

                    writer.writerow(row)

            logger.info(
                "%s内容翻译完成: %d/%d 条记录使用了自定义词典",
                self.dictionary_type,
                translated_count,
                total_count,
            )
            ui.print_success(
                f"✅ {self.dictionary_type}内容翻译完成: {translated_count}/{total_count} 条记录"
            )
            return True

        except (OSError, IOError, csv.Error) as e:
            logger.error("翻译CSV文件失败: %s", e)
            ui.print_error(f"❌ {self.dictionary_type}内容翻译失败: {e}")
            return False

    def add_custom_translation(self, english: str, chinese: str) -> bool:
        """
        添加自定义翻译

        Args:
            english: 英文词汇
            chinese: 中文翻译

        Returns:
            bool: 是否成功
        """
        try:
            english_lower = english.lower().strip()
            chinese_stripped = chinese.strip()

            if not english_lower or not chinese_stripped:
                return False

            self.dictionary[english_lower] = {
                "chinese": chinese_stripped,
                "priority": "medium",  # 默认中优先级
            }
            logger.info(
                "添加%s自定义翻译: %s -> %s",
                self.dictionary_type,
                english_lower,
                chinese_stripped,
            )
            return True

        except (ValueError, TypeError) as e:
            logger.error("添加%s自定义翻译失败: %s", self.dictionary_type, e)
            return False

    def get_dictionary_stats(self) -> Dict[str, int]:
        """
        获取词典统计信息

        Returns:
            Dict[str, int]: 统计信息
        """
        return {
            "total_entries": len(self.dictionary),
            "dictionary_path": self.dictionary_path,
            "dictionary_exists": Path(self.dictionary_path).exists(),
        }

    def reload_dictionary(self) -> bool:
        """
        重新加载词典

        Returns:
            bool: 是否成功
        """
        try:
            self.dictionary.clear()
            self._load_dictionary()
            logger.info("%s词典重新加载完成", self.dictionary_type)
            return True
        except (OSError, IOError, yaml.YAMLError) as e:
            logger.error("重新加载%s词典失败: %s", self.dictionary_type, e)
            return False
