"""
翻译辅助工具

功能：
- 集成翻译字典
- 提供翻译建议
- 翻译质量检查
- 批量翻译辅助
"""

from typing import List, Dict, Any, Optional, Tuple
from user_config.dictionary_manager import get_dictionary_manager
from user_config import UserConfigManager
from utils.logging_config import get_logger


class TranslationHelper:
    """翻译辅助工具"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.dictionary_manager = get_dictionary_manager()
        self.config_manager = UserConfigManager()

    def translate_text(self, english_text: str, context: str = None) -> Dict[str, Any]:
        """
        翻译文本

        Args:
            english_text: 英文文本
            context: 上下文

        Returns:
            翻译结果字典
        """
        result = {
            "original": english_text,
            "translation": None,
            "confidence": 0.0,
            "suggestions": [],
            "warnings": [],
            "is_translatable": True,
        }

        # 检查是否需要翻译
        if not self._should_translate(english_text):
            result["is_translatable"] = False
            result["warnings"].append("文本不需要翻译")
            return result

        # 尝试从字典获取翻译
        translation = self.dictionary_manager.get_translation(english_text, context)
        if translation:
            result["translation"] = translation
            result["confidence"] = 1.0
        else:
            # 获取翻译建议
            suggestions = self.dictionary_manager.get_suggestions(english_text)
            result["suggestions"] = suggestions
            result["confidence"] = 0.0

        return result

    def batch_translate(
        self, texts: List[Tuple[str, str]], context: str = None
    ) -> List[Dict[str, Any]]:
        """
        批量翻译文本

        Args:
            texts: 文本列表，每个元素为 (field_name, english_text)
            context: 上下文

        Returns:
            翻译结果列表
        """
        results = []

        for field_name, english_text in texts:
            # 检查字段是否需要翻译
            if not self.config.is_translation_field(field_name):
                results.append(
                    {
                        "field": field_name,
                        "original": english_text,
                        "translation": english_text,
                        "confidence": 1.0,
                        "skipped": True,
                        "reason": "字段不需要翻译",
                    }
                )
                continue

            # 翻译文本
            translation_result = self.translate_text(english_text, context)
            results.append(
                {
                    "field": field_name,
                    "original": english_text,
                    "translation": translation_result["translation"],
                    "confidence": translation_result["confidence"],
                    "suggestions": translation_result["suggestions"],
                    "warnings": translation_result["warnings"],
                    "skipped": False,
                }
            )

        return results

    def _should_translate(self, text: str) -> bool:
        """
        判断文本是否需要翻译

        Args:
            text: 文本内容

        Returns:
            是否需要翻译
        """
        if not text or not text.strip():
            return False

        # 检查是否包含中文字符
        if any("\u4e00" <= char <= "\u9fff" for char in text):
            return False

        # 检查是否为纯数字
        if text.strip().isdigit():
            return False

        # 检查是否为纯标点符号
        if all(not char.isalnum() for char in text.strip()):
            return False

        return True


# 全局翻译辅助工具实例
_translation_helper: Optional[TranslationHelper] = None


def get_translation_helper() -> TranslationHelper:
    """获取全局翻译辅助工具实例"""
    global _translation_helper
    if _translation_helper is None:
        _translation_helper = TranslationHelper()
    return _translation_helper
