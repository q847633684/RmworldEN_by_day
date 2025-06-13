from typing import List

PREVIEW_TRANSLATABLE_FIELDS: bool = False
DEBUG_MODE: bool = False
LOG_FILE: str = "extract_translate.log"

DEFAULT_FIELDS: List[str] = [
    'label', 'RMBLabel', 'description', 'baseDesc', 'title', 'titleShort',
    'rulesStrings', 'labelNoun', 'gerund', 'reportString',
    'text', 'message', 'verb', 'skillLabel', 'pawnLabel'
]
IGNORE_FIELDS: List[str] = [
    'defName', 'ParentName', 'visible', 'baseMoodEffect', 'Class',
    'ignoreIllegalLabelCharacterConfigError', 'identifier', 'slot',
    'spawnCategories', 'skillGains', 'workDisables', 'requiredWorkTags',
    'bodyTypeGlobal', 'bodyTypeFemale', 'bodyTypeMale', 'forcedTraits',
    'initialSeverity', 'minSeverity', 'maxSeverity', 'isBad', 'tendable',
    'scenarioCanAdd', 'comps', 'defaultLabelColor', 'hediffDef',
    'becomeVisible', 'rulePack', 'retro' ,'Social'
]
NON_TEXT_PATTERNS: List[str] = [
    r'^\s*\(\s*\d+\s*,\s*[\d*\.]+\s*\)\s*$',
    r'^\s*[\d.]+\s*$',
    r'^\s*(true|false)\s*$',
]
