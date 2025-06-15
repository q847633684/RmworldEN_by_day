from typing import List
from dataclasses import dataclass, field

@dataclass
class TranslationConfig:
    """翻译项目配置"""
    log_file: str = "main.log"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    debug_mode: bool = True  # 开发时设为 True
    preview_translatable_fields: bool = False  # 测试时可设为 False 跳过预览
    default_language: str = "ChineseSimplified"
    source_language: str = "English"
    def_injected_dir: str = "DefInjected"
    keyed_dir: str = "Keyed"
    ignore_prefixes: List[str] = field(default_factory=lambda: ["#", "@", "$", "%", "&"])
    output_csv: str = "extracted_translations.csv"
    default_fields: List[str] = field(default_factory=lambda: [
        "label", "RMBLabel", "description", "baseDesc", "title", "titleShort",
        "rulesStrings", "labelNoun", "gerund", "reportString",
        "text", "message", "verb", "skillLabel", "pawnLabel"
    ])
    ignore_fields: List[str] = field(default_factory=lambda: [
        "defName", "ParentName", "visible", "baseMoodEffect", "Class",
        "ignoreIllegalLabelCharacterConfigError", "identifier", "slot",
        "spawnCategories", "skillGains", "workDisables", "requiredWorkTags",
        "bodyTypeGlobal", "bodyTypeFemale", "bodyTypeMale", "forcedTraits",
        "initialSeverity", "minSeverity", "maxSeverity", "isBad", "tendable",
        "scenarioCanAdd", "comps", "defaultLabelColor", "hediffDef",
        "becomeVisible", "rulePack", "retro", "Social"
    ])
    non_text_patterns: List[str] = field(default_factory=lambda: [
        r"^\s*\(\s*\d+\s*,\s*[\d*\.]+\s*\)\s*$",
        r"^\s*[\d.]+\s*$",
        r"^\s*(true|false)\s*$",
        r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*$",  # 变量名
        r"^\s*#[0-9A-Fa-f]{6}\s*$",  # 颜色代码
    ])
    
    # 新增：批量处理配置
    batch_mode_enabled: bool = True
    max_concurrent_files: int = 10
    
    # 新增：用户体验配置
    show_progress_bar: bool = True
    auto_backup: bool = True
    backup_suffix: str = ".backup"