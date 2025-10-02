"""
翻译字典管理器

管理翻译词典，提供翻译建议和一致性检查
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from utils.logging_config import get_logger


class DictionaryManager:
    """翻译字典管理器"""

    def __init__(self):
        self.logger = get_logger(f"{__name__}.DictionaryManager")
        self.dictionary_data = {}
        self.load_dictionary()

    def load_dictionary(self) -> bool:
        """加载翻译字典"""
        try:
            # 从新位置加载字典文件
            dict_path = Path(__file__).parent / "config" / "translation_dictionary.yaml"

            if not dict_path.exists():
                self.logger.warning("翻译字典文件不存在，使用空字典")
                return False

            with open(dict_path, "r", encoding="utf-8") as f:
                self.dictionary_data = yaml.safe_load(f) or {}

            self.logger.info(
                f"翻译字典加载成功，包含 {len(self.dictionary_data)} 个条目"
            )
            return True

        except Exception as e:
            self.logger.error(f"加载翻译字典失败: {e}")
            self.dictionary_data = {}
            return False

    def get_translation(self, english_text: str) -> Optional[str]:
        """获取英文文本的翻译"""
        return self.dictionary_data.get(english_text.strip())

    def add_translation(self, english_text: str, chinese_text: str) -> bool:
        """添加翻译条目"""
        try:
            self.dictionary_data[english_text.strip()] = chinese_text.strip()
            self.logger.debug(f"添加翻译条目: {english_text} -> {chinese_text}")
            return True
        except Exception as e:
            self.logger.error(f"添加翻译条目失败: {e}")
            return False

    def remove_translation(self, english_text: str) -> bool:
        """移除翻译条目"""
        try:
            if english_text.strip() in self.dictionary_data:
                del self.dictionary_data[english_text.strip()]
                self.logger.debug(f"移除翻译条目: {english_text}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除翻译条目失败: {e}")
            return False

    def save_dictionary(self) -> bool:
        """保存翻译字典"""
        try:
            dict_path = Path(__file__).parent / "config" / "translation_dictionary.yaml"

            with open(dict_path, "w", encoding="utf-8") as f:
                yaml.dump(self.dictionary_data, f, ensure_ascii=False, indent=2)

            self.logger.info("翻译字典保存成功")
            return True

        except Exception as e:
            self.logger.error(f"保存翻译字典失败: {e}")
            return False

    def search_translations(self, keyword: str) -> Dict[str, str]:
        """搜索包含关键词的翻译条目"""
        results = {}
        keyword_lower = keyword.lower()

        for english, chinese in self.dictionary_data.items():
            if keyword_lower in english.lower() or keyword_lower in chinese.lower():
                results[english] = chinese

        return results

    def get_suggestions(
        self, english_text: str, max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """获取翻译建议"""
        suggestions = []
        english_lower = english_text.lower()

        # 精确匹配
        exact_match = self.get_translation(english_text)
        if exact_match:
            suggestions.append(
                {
                    "type": "exact",
                    "english": english_text,
                    "chinese": exact_match,
                    "confidence": 1.0,
                }
            )
            return suggestions

        # 部分匹配
        for english, chinese in self.dictionary_data.items():
            if english_lower in english.lower() or english.lower() in english_lower:
                suggestions.append(
                    {
                        "type": "partial",
                        "english": english,
                        "chinese": chinese,
                        "confidence": 0.7,
                    }
                )

                if len(suggestions) >= max_suggestions:
                    break

        return suggestions

    def get_statistics(self) -> Dict[str, Any]:
        """获取字典统计信息"""
        return {
            "total_entries": len(self.dictionary_data),
            "average_english_length": sum(len(k) for k in self.dictionary_data.keys())
            / max(len(self.dictionary_data), 1),
            "average_chinese_length": sum(len(v) for v in self.dictionary_data.values())
            / max(len(self.dictionary_data), 1),
        }


# 全局字典管理器实例
_dictionary_manager = None


def get_dictionary_manager() -> DictionaryManager:
    """获取全局字典管理器实例"""
    global _dictionary_manager
    if _dictionary_manager is None:
        _dictionary_manager = DictionaryManager()
    return _dictionary_manager
