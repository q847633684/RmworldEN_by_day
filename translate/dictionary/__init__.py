"""
词典翻译模块
包含成人内容和游戏内容的词典翻译功能
"""

from .dictionary_translator import (
    DictionaryTranslator,
    create_dictionary_translator,
    translate_content_in_csv,
    # 向后兼容的便捷函数
    create_adult_content_translator,
    create_game_content_translator,
    translate_adult_content_in_csv,
    translate_game_content_in_csv,
)

__all__ = [
    # 通用词典翻译
    "DictionaryTranslator",
    "create_dictionary_translator",
    "translate_content_in_csv",
    # 向后兼容的便捷函数
    "create_adult_content_translator",
    "create_game_content_translator",
    "translate_adult_content_in_csv",
    "translate_game_content_in_csv",
]
