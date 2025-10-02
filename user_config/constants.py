"""
常量定义模块
定义项目中使用的各种常量，避免硬编码
"""

# 语言相关常量
class LanguageConstants:
    """语言相关常量"""
    CHINESE_SIMPLIFIED = "ChineseSimplified"
    ENGLISH = "English"
    DEFAULT_LANGUAGE = CHINESE_SIMPLIFIED

# 目录相关常量
class DirectoryConstants:
    """目录相关常量"""
    DEFINJECTED_DIR = "DefInjected"
    KEYED_DIR = "Keyed"
    DEFS_DIR = "Defs"
    LANGUAGES_DIR = "Languages"

# 文件相关常量
class FileConstants:
    """文件相关常量"""
    DEFAULT_OUTPUT_CSV = "extracted_translations.csv"
    TRANSLATED_CSV_SUFFIX = "_zh.csv"
    XML_FILE_EXTENSION = ".xml"
    CSV_FILE_EXTENSION = ".csv"

# 翻译器相关常量
class TranslatorConstants:
    """翻译器相关常量"""
    AUTO_TRANSLATOR = "auto"
    JAVA_TRANSLATOR = "java"
    PYTHON_TRANSLATOR = "python"

# 数据结构相关常量
class DataStructureConstants:
    """数据结构相关常量"""
    ORIGINAL_STRUCTURE = "original_structure"
    DEFS_BY_TYPE = "defs_by_type"
    DEFS_BY_FILE_STRUCTURE = "defs_by_file_structure"

# 数据源选择常量
class DataSourceConstants:
    """数据源选择常量"""
    DEFINJECTED_ONLY = "definjected_only"
    DEFS_ONLY = "defs_only"
    BOTH = "both"

# UI相关常量
class UIConstants:
    """UI相关常量"""
    PROGRESS_BAR_WIDTH = 40
    MAX_DESCRIPTION_LENGTH = 50
    
    # 进度条前缀
    SCAN_PREFIX = "扫描"
    GENERATE_PREFIX = "生成"
    EXPORT_PREFIX = "导出"
    
    # 进度条描述模板
    SCAN_DESCRIPTION_TEMPLATE = "正在扫描 {name} 目录中的 {count} 个文件"
    GENERATE_DESCRIPTION_TEMPLATE = "正在生成 {name} 模板中的 {count} 个文件"
    EXPORT_DESCRIPTION_TEMPLATE = "正在导出 {count} 条翻译到CSV"

# 配置相关常量
class ConfigConstants:
    """配置相关常量"""
    CONFIG_VERSION = "1.0.0"
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_DEBUG_MODE = False

# 错误消息常量
class ErrorMessages:
    """错误消息常量"""
    INVALID_MOD_DIR = "无效的模组目录"
    CSV_FILE_NOT_EXISTS = "CSV文件不存在"
    TRANSLATION_FAILED = "翻译失败"
    IMPORT_FAILED = "导入失败"
    EXPORT_FAILED = "导出失败"
    CONFIG_ERROR = "配置错误"
    VALIDATION_FAILED = "验证失败"

# 成功消息常量
class SuccessMessages:
    """成功消息常量"""
    TRANSLATION_COMPLETED = "翻译完成"
    IMPORT_COMPLETED = "导入完成"
    EXPORT_COMPLETED = "导出完成"
    TEMPLATE_GENERATED = "模板已生成"
    CSV_GENERATED = "CSV文件已生成"

# 警告消息常量
class WarningMessages:
    """警告消息常量"""
    NO_LANGUAGES_FOLDER = "模组目录中未找到 Languages 文件夹"
    NO_PARALLEL_CORPUS = "未找到任何平行语料"
    TRANSLATION_INCOMPLETE = "翻译部分完成"
    LOW_TRANSLATION_RATIO = "翻译率过低"
