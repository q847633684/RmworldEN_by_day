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
from ...utils.logging_config import get_logger
from ...utils.ui_style import ui

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
        return str(
            Path(__file__).parent.parent.parent / "user_config" / "config" / filename
        )

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
            for category, category_data in data.items():
                if isinstance(category_data, dict) and "entries" in category_data:
                    for entry in category_data["entries"]:
                        english = entry.get("english", "").lower().strip()
                        chinese = entry.get("chinese", "").strip()
                        if english and chinese:
                            self.dictionary[english] = chinese
                            total_entries += 1

            if total_entries > 0:
                logger.info(
                    "已加载 %d 个%s内容翻译条目", total_entries, self.dictionary_type
                )
            else:
                logger.warning("词典文件中未找到%s内容翻译条目", self.dictionary_type)

        except Exception as e:
            logger.error("加载自定义词典失败: %s", e)

    def translate_text(self, text: str) -> Tuple[str, bool]:
        """
        翻译文本，优先使用自定义词典

        Args:
            text: 要翻译的文本

        Returns:
            Tuple[str, bool]: (翻译后的文本, 是否使用了自定义词典)
        """
        if not text or not isinstance(text, str):
            return text, False

        # 检查是否包含成人内容词汇
        text_lower = text.lower()
        used_custom_dict = False
        translated_text = text

        # 按优先级排序的词汇（长词汇优先，避免部分匹配问题）
        sorted_entries = sorted(
            self.dictionary.items(), key=lambda x: len(x[0]), reverse=True
        )

        for english_word, chinese_word in sorted_entries:
            if english_word in text_lower:
                # 使用正则表达式进行精确匹配
                import re

                pattern = r"\b" + re.escape(english_word) + r"\b"
                if re.search(pattern, text_lower):
                    translated_text = re.sub(
                        pattern, chinese_word, translated_text, flags=re.IGNORECASE
                    )
                    used_custom_dict = True
                    logger.debug(
                        "使用自定义词典翻译: %s -> %s", english_word, chinese_word
                    )

        return translated_text, used_custom_dict

    def translate_csv_file(self, input_csv: str, output_csv: str) -> bool:
        """
        翻译CSV文件中的内容

        Args:
            input_csv: 输入CSV文件路径
            output_csv: 输出CSV文件路径

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
                    modified = False

                    # 翻译text列
                    if "text" in row and row["text"]:
                        original_text = row["text"]
                        translated_text, used_dict = self.translate_text(original_text)
                        if used_dict:
                            row["text"] = translated_text
                            modified = True
                            translated_count += 1

                    # 翻译translated列（如果存在）
                    if "translated" in row and row["translated"]:
                        original_translated = row["translated"]
                        translated_translated, used_dict = self.translate_text(
                            original_translated
                        )
                        if used_dict:
                            row["translated"] = translated_translated
                            modified = True

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

        except Exception as e:
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

            self.dictionary[english_lower] = chinese_stripped
            logger.info(
                "添加%s自定义翻译: %s -> %s",
                self.dictionary_type,
                english_lower,
                chinese_stripped,
            )
            return True

        except Exception as e:
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
        except Exception as e:
            logger.error("重新加载%s词典失败: %s", self.dictionary_type, e)
            return False


def create_dictionary_translator(
    dictionary_type: str = "adult",
) -> DictionaryTranslator:
    """创建词典翻译器实例"""
    return DictionaryTranslator(dictionary_type)


def translate_content_in_csv(
    input_csv: str, output_csv: str, dictionary_type: str = "adult"
) -> bool:
    """
    翻译CSV文件中的内容（便捷函数）

    Args:
        input_csv: 输入CSV文件路径
        output_csv: 输出CSV文件路径
        dictionary_type: 词典类型 ("adult" 或 "game")

    Returns:
        bool: 是否成功
    """
    translator = create_dictionary_translator(dictionary_type)
    return translator.translate_csv_file(input_csv, output_csv)


# 向后兼容的便捷函数
def create_adult_content_translator() -> DictionaryTranslator:
    """创建成人内容翻译器实例（向后兼容）"""
    return DictionaryTranslator("adult")


def create_game_content_translator() -> DictionaryTranslator:
    """创建游戏内容翻译器实例（向后兼容）"""
    return DictionaryTranslator("game")


def translate_adult_content_in_csv(input_csv: str, output_csv: str) -> bool:
    """翻译CSV文件中的成人内容（向后兼容）"""
    return translate_content_in_csv(input_csv, output_csv, "adult")


def translate_game_content_in_csv(input_csv: str, output_csv: str) -> bool:
    """翻译CSV文件中的游戏内容（向后兼容）"""
    return translate_content_in_csv(input_csv, output_csv, "game")
