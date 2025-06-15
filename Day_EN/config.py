from typing import List
# 日志相关常量（全项目统一引用）
LOG_FILE = "main.log"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
# 是否开启调试模式
DEBUG_MODE = False
PREVIEW_TRANSLATABLE_FIELDS: bool = False
# 默认翻译字段列表
DEFAULT_FIELDS: List[str] = [
    'label', 'RMBLabel', 'description', 'baseDesc', 'title', 'titleShort',
    'rulesStrings', 'labelNoun', 'gerund', 'reportString',
    'text', 'message', 'verb', 'skillLabel', 'pawnLabel'
]
# 忽略的字段列表（不需要翻译的字段）
IGNORE_FIELDS: List[str] = [
    'defName', 'ParentName', 'visible', 'baseMoodEffect', 'Class',
    'ignoreIllegalLabelCharacterConfigError', 'identifier', 'slot',
    'spawnCategories', 'skillGains', 'workDisables', 'requiredWorkTags',
    'bodyTypeGlobal', 'bodyTypeFemale', 'bodyTypeMale', 'forcedTraits',
    'initialSeverity', 'minSeverity', 'maxSeverity', 'isBad', 'tendable',
    'scenarioCanAdd', 'comps', 'defaultLabelColor', 'hediffDef',
    'becomeVisible', 'rulePack', 'retro' ,'Social'
]
# 非文本模式匹配列表（用于识别非文本内容）
NON_TEXT_PATTERNS: List[str] = [
    r'^\s*\(\s*\d+\s*,\s*[\d*\.]+\s*\)\s*$',
    r'^\s*[\d.]+\s*$',
    r'^\s*(true|false)\s*$',
]
