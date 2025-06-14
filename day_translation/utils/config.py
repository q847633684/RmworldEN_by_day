from typing import List
from dataclasses import dataclass

@dataclass
class TranslationConfig:
    """翻译项目配置"""
    log_file: str = "main.log"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    debug_mode: bool = False
    preview_translatable_fields: bool = False
    default_language: str = "ChineseSimplified"
    source_language: str = "English"
    def_injected_dir: str = "DefInjected"
    keyed_dir: str = "Keyed"
    output_csv: str = "extracted_translations.csv"
    default_fields: List[str] = [
        "label", "RMBLabel", "description", "baseDesc", "title", "titleShort",
        "rulesStrings", "labelNoun", "gerund", "reportString",
        "text", "message", "verb", "skillLabel", "pawnLabel"
    ]
    ignore_fields: List[str] = [
        "defName", "ParentName", "visible", "baseMoodEffect", "Class",
        "ignoreIllegalLabelCharacterConfigError", "identifier", "slot",
        "spawnCategories", "skillGains", "workDisables", "requiredWorkTags",
        "bodyTypeGlobal", "bodyTypeFemale", "bodyTypeMale", "forcedTraits",
        "initialSeverity", "minSeverity", "maxSeverity", "isBad", "tendable",
        "scenarioCanAdd", "comps", "defaultLabelColor", "hediffDef",
        "becomeVisible", "rulePack", "retro", "Social"
    ]
    non_text_patterns: List[str] = [
        r"^\s*\(\s*\d+\s*,\s*[\d*\.]+\s*\)\s*$",
        r"^\s*[\d.]+\s*$",
        r"^\s*(true|false)\s*$",
    ]