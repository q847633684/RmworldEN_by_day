from dataclasses import dataclass
import os
import logging
from typing import Set, List
from .filter_config import UnifiedFilterRules

@dataclass
class TranslationConfig:
    default_language: str = "ChineseSimplified"
    source_language: str = "English"
    def_injected_dir: str = "DefInjected"
    keyed_dir: str = "Keyed"
    output_csv: str = "extracted_translations.csv"
    log_file: str = os.path.join(os.path.dirname(__file__), "logs", "translation.log")
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    debug_mode: bool = os.getenv("DAY_TRANSLATION_DEBUG", "").lower() == "true"
    preview_transatable_fields: int = 0

    def __post_init__(self):
        self._rules = UnifiedFilterRules.get_rules()
        self.log_dir = os.path.dirname(self.log_file)
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)

    @property
    def default_fields(self) -> Set[str]:
        return self._rules.DEFAULT_FIELDS

    @property
    def ignore_fields(self) -> Set[str]:
        return self._rules.IGNORE_FIELDS

    @property
    def non_text_patterns(self) -> List[str]:
        return self._rules.NON_TEXT_PATTERNS

    def load_custom_config(self, config_file: str) -> None:
        """加载自定义配置文件"""
        import json
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._rules = UnifiedFilterRules.from_custom_config(config)
            logging.info(f"加载自定义配置: {config_file}")
        except Exception as e:
            logging.warning(f"加载自定义配置失败，使用默认规则: {e}")