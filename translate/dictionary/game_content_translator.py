"""
游戏内容翻译处理器
处理游戏相关词汇的翻译，使用游戏词典进行翻译
"""

try:
    import yaml
except ImportError:
    yaml = None
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from ...utils.logging_config import get_logger
from ...utils.ui_style import ui

logger = get_logger(__name__)


class GameContentTranslator:
    """游戏内容翻译器"""

    def __init__(self, dictionary_path: Optional[str] = None):
        """
        初始化游戏内容翻译器

        Args:
            dictionary_path: 自定义词典文件路径
        """
        self.dictionary = {}
        self.dictionary_path = dictionary_path or self._get_default_dictionary_path()
        self._load_dictionary()

    def _get_default_dictionary_path(self) -> str:
        """获取默认词典路径"""
        return str(
            Path(__file__).parent.parent.parent
            / "user_config"
            / "config"
            / "game_dictionary.yaml"
        )

    def _load_dictionary(self) -> None:
        """加载自定义词典"""
        try:
            if not Path(self.dictionary_path).exists():
                logger.warning("游戏词典文件不存在: %s", self.dictionary_path)
                return

            if yaml is None:
                logger.error("yaml库未安装，无法加载游戏词典")
                return

            with open(self.dictionary_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 加载游戏内容词典（新格式）
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
                logger.info("已加载 %d 个游戏内容翻译条目", total_entries)
            else:
                logger.warning("词典文件中未找到游戏内容翻译条目")

        except Exception as e:
            logger.error("加载游戏词典失败: %s", e)

    def translate_text(self, text: str) -> Tuple[str, bool]:
        """
        翻译文本，优先使用游戏词典

        Args:
            text: 要翻译的文本

        Returns:
            Tuple[str, bool]: (翻译后的文本, 是否使用了游戏词典)
        """
        if not text or not isinstance(text, str):
            return text, False

        # 检查是否包含游戏内容词汇
        text_lower = text.lower()
        used_game_dict = False
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
                    used_game_dict = True
                    logger.debug(
                        "使用游戏词典翻译: %s -> %s", english_word, chinese_word
                    )

        return translated_text, used_game_dict

    def translate_csv_file(self, input_csv: str, output_csv: str) -> bool:
        """
        翻译CSV文件中的游戏内容

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
                "游戏内容翻译完成: %d/%d 条记录使用了游戏词典",
                translated_count,
                total_count,
            )
            ui.print_success(
                f"✅ 游戏内容翻译完成: {translated_count}/{total_count} 条记录"
            )
            return True

        except Exception as e:
            logger.error("翻译CSV文件失败: %s", e)
            ui.print_error(f"❌ 游戏内容翻译失败: {e}")
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
            logger.info("添加游戏自定义翻译: %s -> %s", english_lower, chinese_stripped)
            return True

        except Exception as e:
            logger.error("添加游戏自定义翻译失败: %s", e)
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
            logger.info("游戏词典重新加载完成")
            return True
        except Exception as e:
            logger.error("重新加载游戏词典失败: %s", e)
            return False


def create_game_content_translator() -> GameContentTranslator:
    """创建游戏内容翻译器实例"""
    return GameContentTranslator()


def translate_game_content_in_csv(input_csv: str, output_csv: str) -> bool:
    """
    翻译CSV文件中的游戏内容（便捷函数）

    Args:
        input_csv: 输入CSV文件路径
        output_csv: 输出CSV文件路径

    Returns:
        bool: 是否成功
    """
    translator = create_game_content_translator()
    return translator.translate_csv_file(input_csv, output_csv)
