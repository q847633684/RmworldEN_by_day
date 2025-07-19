"""
配置管理模块 - 负责翻译配置的加载、保存、验证和管理

支持的配置项及含义：
- CN_language: 中文语言目录名（如 ChineseSimplified）
- EN_language: 英文语言目录名（如 English）
- DefInjected_dir: DefInjected 子目录名（如 DefInjected）
- keyed_dir: Keyed 子目录名（如 Keyed）
- output_csv: 默认输出 CSV 文件名
- log_file: 日志文件路径（自动生成）
- log_format: 日志格式
- debug_mode: 是否开启调试模式（环境变量 DAY_TRANSLATION_DEBUG 控制）
- preview_transatable_fields: 预览可翻译字段数量

其它配置项可参考 TranslationConfig 数据类定义。
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from colorama import Fore, Style  # type: ignore

from .filter_config import UnifiedFilterRules

_config_instance: Optional["TranslationConfig"] = None
CONFIG_VERSION = "1.0.0"


class ConfigError(Exception):
    """配置相关错误"""


@dataclass
class TranslationConfig:
    """翻译配置类，负责管理所有配置项"""

    version: str = CONFIG_VERSION
    CN_language: str = "ChineseSimplified"
    EN_language: str = "English"
    DefInjected_dir: str = "DefInjected"
    keyed_dir: str = "Keyed"
    output_csv: str = "extracted_translations.csv"
    log_file: str = ""  # 将在 __post_init__ 中动态生成
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    debug_mode: bool = True  # os.getenv("DAY_TRANSLATION_DEBUG", "").lower() =="true"
    preview_transatable_fields: int = 0

    def __post_init__(self):
        """初始化后处理"""
        # 动态生成带时间戳的日志文件名
        if not self.log_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
            )
            self.log_file = os.path.join(log_dir, f"day_translation_{timestamp}.log")
        self._validate_config()
        self._rules = {
            "default_fields": UnifiedFilterRules.DEFAULT_FIELDS,
            "ignore_fields": UnifiedFilterRules.IGNORE_FIELDS,
            "non_text_patterns": UnifiedFilterRules.NON_TEXT_PATTERNS,
        }
        self._setup_logging()
        self._load_user_config()

    def _setup_logging(self) -> None:
        """设置日志系统"""
        # 检查是否已经初始化过日志系统
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return  # 已经初始化，直接返回
        # 确保日志目录存在
        try:
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            # 创建文件处理器和控制台处理器
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
            file_handler.setFormatter(logging.Formatter(self.log_format))

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误
            console_handler.setFormatter(logging.Formatter(self.log_format))

            # 配置根日志器
            root_logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            logging.info("日志系统初始化完成: %s", self.log_file)
        except Exception as e:
            print(f"{Fore.RED}日志系统初始化失败: {e}{Style.RESET_ALL}")
            raise ConfigError(f"日志系统初始化失败: {str(e)}") from e

    def _load_user_config(self) -> None:
        """加载用户配置"""
        try:
            user_config = get_user_config()  # 使用缓存版本
            if user_config:
                self._update_from_dict(user_config)
                logging.info("已加载用户配置")
        except (OSError, IOError, ValueError, KeyError) as e:
            logging.warning("加载用户配置失败: %s", e)

    def _validate_config(self) -> None:
        """验证配置项的有效性"""
        if not isinstance(self.CN_language, str) or not self.CN_language:
            raise ConfigError("CN_language 必须是有效的语言代码")
        if not isinstance(self.EN_language, str) or not self.EN_language:
            raise ConfigError("EN_language 必须是有效的语言代码")
        if not isinstance(self.DefInjected_dir, str) or not self.DefInjected_dir:
            raise ConfigError("DefInjected_dir 不能为空")
        if not isinstance(self.keyed_dir, str) or not self.keyed_dir:
            raise ConfigError("keyed_dir 不能为空")
        if not isinstance(self.output_csv, str) or not self.output_csv:
            raise ConfigError("output_csv 必须是有效的文件路径")
        if not isinstance(self.log_file, str) or not self.log_file:
            raise ConfigError("log_file 必须是有效的文件路径")
        if not isinstance(self.log_format, str) or not self.log_format:
            raise ConfigError("log_format 不能为空")
        if (
            not isinstance(self.preview_transatable_fields, int)
            or self.preview_transatable_fields < 0
        ):
            raise ConfigError("preview_transatable_fields 必须是非负整数")

    def _update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """从字典更新配置"""
        for key, value in config_dict.items():
            if hasattr(self, key) and not key.startswith("_"):
                setattr(self, key, value)
        self._validate_config()

    @property
    def default_fields(self) -> Set[str]:
        """获取默认字段集合"""
        if not hasattr(self, "_rules") or not self._rules:
            return set()
        default_fields = self._rules.get("default_fields", [])
        # 确保所有字段都是字符串类型
        if isinstance(default_fields, (list, set)):
            return set(f for f in default_fields if isinstance(f, str))
        return set()

    @property
    def ignore_fields(self) -> Set[str]:
        """获取忽略字段集合"""
        if not hasattr(self, "_rules") or not self._rules:
            return set()
        ignore_fields = self._rules.get("ignore_fields", [])
        return set(ignore_fields) if ignore_fields else set()

    @property
    def non_text_patterns(self) -> List[str]:
        """获取非文本模式列表"""
        if not hasattr(self, "_rules") or not self._rules:
            return []
        return self._rules.get("non_text_patterns", [])

    def update_config(self, key: str, value: Any) -> None:
        """
        更新配置项

        Args:
            key (str): 配置项名称
            value (Any): 配置项值

        Raises:
            ConfigError: 如果配置项无效
        """
        if not hasattr(self, key) or key.startswith("_"):
            raise ConfigError(f"无效的配置项: {key}")

        old_value = getattr(self, key)
        try:
            setattr(self, key, value)
            self._validate_config()
            logging.info("更新配置: %s = %s", key, value)
        except Exception as e:
            setattr(self, key, old_value)
            raise ConfigError(f"更新配置失败: {str(e)}") from e

    def show_config(self) -> None:
        """显示当前配置"""
        # 定义中文字段名映射
        field_names = {
            "version": "配置版本",
            "CN_language": "中文语言目录",
            "EN_language": "英文语言目录",
            "DefInjected_dir": "DefInjected目录",
            "keyed_dir": "Keyed目录",
            "output_csv": "默认CSV文件名",
            "log_file": "日志文件路径",
            "preserve_comments": "保留注释",
            "preserve_original_structure": "保留原始结构",
            "use_machine_translation": "使用机器翻译",
            "translation_api": "翻译API",
            "api_key": "API密钥",
            "api_endpoint": "API端点",
            "request_timeout": "请求超时",
            "request_delay": "请求延迟",
            "max_retries": "最大重试次数",
            "backup_enabled": "备份启用",
            "backup_dir": "备份目录",
            "backup_count": "备份数量",
            "languages_dir": "Languages目录",
            "defs_dir": "Defs目录",
        }

        print(f"\n{Fore.BLUE}=== 当前配置 ==={Style.RESET_ALL}")
        config_dict = asdict(self)
        for key, value in config_dict.items():
            if not key.startswith("_"):
                chinese_name = field_names.get(key, key)
                # 特殊处理敏感信息
                if "key" in key.lower() and value:
                    display_value = (
                        f"{'*' * (len(str(value)) - 4)}{str(value)[-4:]}"
                        if len(str(value)) > 4
                        else "****"
                    )
                else:
                    display_value = value
                print(f"  {chinese_name}: {Fore.CYAN}{display_value}{Style.RESET_ALL}")

    def export_config(self, config_file: str) -> None:
        """
        导出配置到文件

        Args:
            config_file (str): 配置文件路径

        Raises:
            ConfigError: 如果导出失败
        """
        try:
            config_dict = asdict(self)
            # 移除内部属性
            config_dict.pop("_rules", None)

            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            logging.info("配置已导出到: %s", config_file)
        except Exception as e:
            raise ConfigError(f"导出配置失败: {str(e)}") from e

    def import_config(self, config_file: str) -> None:
        """
        从文件导入配置

        Args:
            config_file (str): 配置文件路径

        Raises:
            ConfigError: 如果导入失败
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_dict = json.load(f)

            # 验证配置文件版本
            config_version = config_dict.get("version", "0.0.0")
            if config_version != self.version:
                logging.warning(
                    "配置文件版本不匹配: 当前版本 %s, 配置文件版本 %s",
                    self.version,
                    config_version,
                )
                if not self._is_compatible_version(config_version):
                    raise ConfigError(f"不兼容的配置文件版本: {config_version}")

            self._update_from_dict(config_dict)
            logging.info("配置已从 %s 导入", config_file)
        except Exception as e:
            raise ConfigError(f"导入配置失败: {str(e)}") from e

    def save_user_config(self) -> None:
        """保存用户配置"""
        try:
            user_config = asdict(self)
            # 移除内部属性
            user_config.pop("_rules", None)
            save_user_config_to_file(user_config)
            logging.info("用户配置已保存")
        except (OSError, IOError, ValueError, KeyError) as e:
            logging.error("保存用户配置失败: %s", e)

    def _is_compatible_version(self, version: str) -> bool:
        """检查版本兼容性"""
        try:
            current_major = int(self.version.split(".", maxsplit=1)[0])
            config_major = int(version.split(".", maxsplit=1)[0])
            return current_major == config_major
        except (ValueError, IndexError):
            return False

    def load_custom_rules(self, config_file: str) -> None:
        """
        加载自定义规则配置

        Args:
            config_file (str): 规则配置文件路径

        Raises:
            ConfigError: 如果加载失败
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 验证配置文件版本
            config_version = config.get("version", "0.0.0")
            if config_version != self.version:
                logging.warning(
                    "规则配置文件版本不匹配: 当前版本 %s, 配置文件版本 %s",
                    self.version,
                    config_version,
                )
                if not self._is_compatible_version(config_version):
                    raise ConfigError(f"不兼容的规则配置文件版本: {config_version}")

            # 验证规则配置
            self._validate_rules_config(config)

            self._rules = {
                "default_fields": UnifiedFilterRules.DEFAULT_FIELDS,
                "ignore_fields": UnifiedFilterRules.IGNORE_FIELDS,
                "non_text_patterns": UnifiedFilterRules.NON_TEXT_PATTERNS,
            }
            logging.info("加载自定义规则配置: %s", config_file)
        except Exception as e:
            logging.warning("加载自定义规则配置失败，使用默认规则: %s", e)
            raise ConfigError(f"加载自定义规则配置失败: {str(e)}") from e

    def _validate_rules_config(self, config: Dict[str, Any]) -> None:
        """验证规则配置项"""
        required_fields = {
            "version",
            "default_fields",
            "ignore_fields",
            "non_text_patterns",
        }
        missing_fields = required_fields - set(config.keys())
        if missing_fields:
            raise ConfigError(f"规则配置文件缺少必需字段: {missing_fields}")

        if not isinstance(config["default_fields"], list):
            raise ConfigError("default_fields 必须是列表")
        if not isinstance(config["ignore_fields"], list):
            raise ConfigError("ignore_fields 必须是列表")
        if not isinstance(config["non_text_patterns"], list):
            raise ConfigError("non_text_patterns 必须是列表")


# 全局配置实例管理
# =================


def get_config() -> "TranslationConfig":
    """
    获取全局唯一的配置实例（单例模式）。

    如果实例不存在，则创建一个新的 TranslationConfig 实例。
    这确保了整个应用程序共享同一个配置状态，避免了重复初始化。

    Returns:
        TranslationConfig: 全局配置实例。
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = TranslationConfig()
    return _config_instance


def reload_config() -> "TranslationConfig":
    """
    重新加载配置，强制创建一个新的配置实例。

    这在需要应用外部更改（例如，用户修改了配置文件）而无需重启整个应用时非常有用。

    Returns:
        TranslationConfig: 新的全局配置实例。
    """
    global _config_instance
    _config_instance = TranslationConfig()
    logging.info("配置已重新加载")
    return _config_instance


# 缓存的用户配置
_user_config_cache: Optional[Dict[str, Any]] = None


def get_config_path() -> str:
    """获取用户配置文件路径"""
    config_path = os.path.join(Path.home(), ".day_translation", "config.json")
    logging.debug("获取配置文件路径: %s", config_path)
    return config_path


def get_user_config() -> Dict[str, Any]:
    """获取缓存的用户配置"""
    global _user_config_cache
    if _user_config_cache is None:
        # 直接实现配置加载，避免循环依赖
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    _user_config_cache = json.load(f)
                    logging.debug("加载用户配置成功: %s", config_path)
            except (OSError, IOError, json.JSONDecodeError) as e:
                logging.error("加载用户配置文件失败: %s", e)
                _user_config_cache = {}
        else:
            _user_config_cache = {}
            logging.debug("用户配置文件不存在，使用空配置")
    return _user_config_cache


def clear_user_config_cache():
    """清除用户配置缓存（用于配置更新后）"""
    global _user_config_cache
    _user_config_cache = None


def save_user_config_to_file(config: Dict) -> None:
    """
    保存用户配置到文件

    Args:
        config (Dict): 配置字典
    """
    config_path = get_config_path()
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logging.debug("配置文件保存成功: %s", config_path)
        # 清除缓存，以便下次读取时获取最新配置
        clear_user_config_cache()
    except (OSError, IOError, ValueError) as e:
        print(f"保存配置文件失败: {e}")
        logging.error("保存配置文件失败: %s", e)


def get_language_dir(base_dir, language):
    """
    获取指定语言的 Languages 目录路径
    """
    return Path(base_dir) / "Languages" / language


def get_language_subdir(base_dir, language, subdir_type):
    """
    获取指定语言的子目录路径，例如 DefInjected 或 Keyed
    :param base_dir: 基础路径
    :param language: 语言名称（如 "ChineseSimplified"）
    :param subdir_type: 子目录类型，应为 'definjected' 或 'keyed'
    :return: 对应子目录的完整路径
    """
    subdir_type = subdir_type.lower()
    subdir_map = {
        "definjected": get_config().DefInjected_dir,
        "keyed": get_config().keyed_dir,
    }
    if subdir_type not in subdir_map:
        raise ValueError(f"Unsupported subdir_type: {subdir_type}")

    return get_language_dir(base_dir, language) / subdir_map[subdir_type]
