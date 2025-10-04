"""
词典翻译模块
包含成人内容和游戏内容的词典翻译功能
"""

from .adult_content_translator import (
    AdultContentTranslator,
    create_adult_content_translator,
    translate_adult_content_in_csv,
)
from .game_content_translator import (
    GameContentTranslator,
    create_game_content_translator,
    translate_game_content_in_csv,
)

__all__ = [
    # 成人内容翻译
    "AdultContentTranslator",
    "create_adult_content_translator",
    "translate_adult_content_in_csv",
    # 游戏内容翻译
    "GameContentTranslator",
    "create_game_content_translator",
    "translate_game_content_in_csv",
]
