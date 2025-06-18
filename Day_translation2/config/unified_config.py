"""
Day Translation 2 - 统一配置管理模块

整合所有配置到分层结构中，负责管理程序核心配置和用户偏好设置。
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict, field
from colorama import Fore, Style
from datetime import datetime

try:
    # 尝试相对导入 (包内使用)
    from ..models.config_models import CoreConfig, UserConfig, PathValidationResult, FilterConfig, ProcessingConfig
    from ..models.exceptions import ConfigError
except ImportError:
    # 回退到绝对导入 (直接运行时)
    from models.config_models import CoreConfig, UserConfig, PathValidationResult, FilterConfig, ProcessingConfig
    from models.exceptions import ConfigError

CONFIG_VERSION = "2.0.0"

@dataclass
class PathHistory:
    """路径历史记录"""
    paths: List[str] = field(default_factory=list)
    max_length: int = 10
    last_used: Optional[str] = None

# === 扩展配置类 ===
@dataclass
class ExtractionPreferences:
    """提取操作的用户偏好"""
    # 输出位置选择
    output_location: str = "external"  # "internal" 或 "external"
    output_dir: Optional[str] = None  # 输出目录
    en_keyed_dir: Optional[str] = None  # 英文 Keyed 目录
    auto_detect_en_keyed: bool = True  # 自动检测英文 Keyed 目录
    auto_choose_definjected: bool = False  # 自动选择 DefInjected
    structure_choice: str = "original"  # "original", "defs", "structured"
    merge_mode: str = "smart-merge"  # "merge", "replace", "backup", "skip", "smart-merge"

@dataclass 
class ImportPreferences:
    """导入操作的用户偏好"""
    merge_existing: bool = True # 是否合并现有翻译
    backup_before_import: bool = True # 是否在导入之前备份文件

@dataclass
class ApiPreferences:
    """API配置偏好"""
    aliyun_access_key_id: str = "" # 阿里云访问密钥ID
    aliyun_access_key_secret: str = "" #阿里云访问密钥Secret
    save_api_keys: bool = True # 是否保存API密钥

@dataclass
class GeneralPreferences:
    """通用偏好设置"""
    remember_paths: bool = True # 是否记住用户选择的路径
    auto_mode: bool = False  # 是否启用自动模式（使用上次配置）
    confirm_operations: bool = True # 是否在执行操作前确认

@dataclass
class ExtendedUserConfig(UserConfig):
    """扩展的用户配置"""
    extraction: ExtractionPreferences = field(default_factory=ExtractionPreferences)
    import_prefs: ImportPreferences = field(default_factory=ImportPreferences)
    api: ApiPreferences = field(default_factory=ApiPreferences)
    general: GeneralPreferences = field(default_factory=GeneralPreferences)
    remembered_paths: Dict[str, str] = field(default_factory=dict)
    path_history: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 继承的配置
    filter_config: FilterConfig = field(default_factory=FilterConfig)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)

    def __post_init__(self):
        super().__post_init__()
        # 确保子对象都是正确的类型
        if isinstance(self.extraction, dict):
            self.extraction = ExtractionPreferences(**self.extraction)
        if isinstance(self.import_prefs, dict):
            self.import_prefs = ImportPreferences(**self.import_prefs)
        if isinstance(self.api, dict):
            self.api = ApiPreferences(**self.api)
        if isinstance(self.general, dict):
            self.general = GeneralPreferences(**self.general)

@dataclass
class ExtendedCoreConfig(CoreConfig):
    """扩展的核心配置"""
    # 继承基础配置，添加扩展配置
    default_language: str = "ChineseSimplified"
    source_language: str = "English"
    def_injected_dir: str = "DefInjected"
    keyed_dir: str = "Keyed"
    output_csv: str = "extracted_translations.csv"
    log_file: str = ""
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    debug_mode: bool = False
    preview_transatable_fields: int = 0
    
    # 默认字段集合
    default_fields: set = field(default_factory=lambda: {
        'label', 'description', 'labelShort', 'descriptionShort',
        'title', 'text', 'message', 'tooltip', 'baseDesc',
        'skillDescription', 'backstoryDesc', 'jobString',
        'gerundLabel', 'verb', 'deathMessage', 'summary',
        'note', 'flavor', 'quote', 'caption',
        'RMBLabel', 'rulesStrings', 'labelNoun', 'gerund', 
        'reportString', 'skillLabel', 'pawnLabel', 'titleShort',
        'reportStringOverride', 'overrideReportString',
        'overrideTooltip', 'overrideLabel', 'overrideDescription',
        'overrideLabelShort', 'overrideDescriptionShort',
        'overrideTitle', 'overrideText', 'overrideMessage',
        'overrideTooltip', 'overrideBaseDesc', 'overrideSkillDescription',
        'overrideBackstoryDesc', 'overrideJobString', 'overrideGerundLabel',
        'overrideVerb', 'overrideDeathMessage', 'overrideSummary',
        'overrideNote', 'overrideFlavor', 'overrideQuote', 'overrideCaption'
    })

# === 统一配置类 ===
@dataclass
class UnifiedConfig:
    """统一配置类 - 包含核心配置和用户配置"""
    version: str = CONFIG_VERSION
    core: ExtendedCoreConfig = field(default_factory=ExtendedCoreConfig)
    user: ExtendedUserConfig = field(default_factory=ExtendedUserConfig)

    def __post_init__(self):
        # 确保子对象都是正确的类型
        if isinstance(self.core, dict):
            self.core = ExtendedCoreConfig(**self.core)
        if isinstance(self.user, dict):
            self.user = ExtendedUserConfig(**self.user)
        
        # 动态生成日志文件名
        if not self.core.log_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            self.core.log_file = os.path.join(log_dir, f"day_translation_{timestamp}.log")
        
        self._setup_logging()
        self._setup_path_validators()

    def _setup_logging(self) -> None:
        """设置日志系统"""
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return  # 已经初始化，直接返回
                      
        try:
            log_dir = os.path.dirname(self.core.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # 创建文件处理器和控制台处理器
            file_handler = logging.FileHandler(self.core.log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG if self.core.debug_mode else logging.INFO)
            file_handler.setFormatter(logging.Formatter(self.core.log_format))
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误
            console_handler.setFormatter(logging.Formatter(self.core.log_format))
            
            # 配置根日志器
            root_logger.setLevel(logging.DEBUG if self.core.debug_mode else logging.INFO)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            logging.info(f"日志系统初始化完成: {self.core.log_file}")
        except Exception as e:
            print(f"{Fore.RED}日志系统初始化失败: {e}{Style.RESET_ALL}")
            raise ConfigError(f"日志系统初始化失败: {str(e)}")

    def _setup_path_validators(self):
        """设置路径验证器"""
        self._path_pattern = re.compile(r'^[a-zA-Z]:[\\/]|^[\\/]{2}|^[a-zA-Z0-9_\-\.]+[\\/]')
        self._validators: Dict[str, Callable[[str], PathValidationResult]] = {
            'dir': self._validate_directory,
            'dir_create': self._validate_directory_create,
            'file': self._validate_file,
            'csv': self._validate_csv_file,
            'xml': self._validate_xml_file,
            'json': self._validate_json_file,
            'mod': self._validate_mod_directory,
        }

    # === 路径验证功能 ===
    def _validate_directory(self, path: str) -> PathValidationResult:
        """验证目录路径"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return PathValidationResult(
                    is_valid=False,
                    message=f"目录不存在: {path}"
                )
            if not path_obj.is_dir():
                return PathValidationResult(
                    is_valid=False,
                    message=f"路径不是目录: {path}"
                )
            return PathValidationResult(
                is_valid=True,
                message="目录验证通过",
                path=path_obj.resolve()
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                message=f"目录验证失败: {str(e)}"
            )

    def _validate_directory_create(self, path: str) -> PathValidationResult:
        """验证目录路径，如果不存在则允许创建"""
        try:
            path_obj = Path(path)
            
            # 如果目录已存在，验证是否为目录
            if path_obj.exists():
                if not path_obj.is_dir():
                    return PathValidationResult(
                        is_valid=False,
                        message=f"路径不是目录: {path}"
                    )
                return PathValidationResult(
                    is_valid=True,
                    message="目录验证通过",
                    path=path_obj.resolve()
                )
            
            # 目录不存在，检查父目录是否存在且可写
            parent = path_obj.parent
            if not parent.exists():
                return PathValidationResult(
                    is_valid=False,
                    message=f"父目录不存在: {parent}"
                )
            
            if not parent.is_dir():
                return PathValidationResult(
                    is_valid=False,
                    message=f"父路径不是目录: {parent}"
                )
            
            # 父目录存在且是目录，允许创建
            return PathValidationResult(
                is_valid=True,
                message="可以创建目录",
                path=path_obj.resolve()
            )
            
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                message=f"目录验证失败: {str(e)}"
            )

    def _validate_file(self, path: str) -> PathValidationResult:
        """验证文件路径"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return PathValidationResult(
                    is_valid=False,
                    message=f"文件不存在: {path}"
                )
            if not path_obj.is_file():
                return PathValidationResult(
                    is_valid=False,
                    message=f"路径不是文件: {path}"
                )
            return PathValidationResult(
                is_valid=True,
                message="文件验证通过",
                path=path_obj.resolve()
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                message=f"文件验证失败: {str(e)}"
            )

    def _validate_csv_file(self, path: str) -> PathValidationResult:
        """验证CSV文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith('.csv'):
            return PathValidationResult(
                is_valid=False,
                message="文件必须是CSV格式"
            )
        return result

    def _validate_xml_file(self, path: str) -> PathValidationResult:
        """验证XML文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith('.xml'):
            return PathValidationResult(
                is_valid=False,
                message="文件必须是XML格式"
            )
        return result

    def _validate_json_file(self, path: str) -> PathValidationResult:
        """验证JSON文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith('.json'):
            return PathValidationResult(
                is_valid=False,
                message="文件必须是JSON格式"
            )
        return result

    def _validate_mod_directory(self, path: str) -> PathValidationResult:
        """验证模组目录路径"""
        result = self._validate_directory(path)
        if result.is_valid:
            # 检查是否包含Languages目录
            languages_dir = Path(path) / "Languages"
            if not languages_dir.exists():
                return PathValidationResult(
                    is_valid=False,
                    message="目录中未找到Languages文件夹，可能不是有效的模组目录"
                )
        return result

    def normalize_path(self, path: str) -> PathValidationResult:
        """规范化路径"""
        try:
            # 转换为绝对路径
            abs_path = os.path.abspath(path)
            # 统一路径分隔符
            normalized = os.path.normpath(abs_path)
            # 验证路径格式
            if not self._path_pattern.match(normalized):
                return PathValidationResult(
                    is_valid=False,
                    message="无效的路径格式"
                )
            return PathValidationResult(
                is_valid=True,
                message="路径规范化完成",
                path=Path(normalized)
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                message=f"路径规范化失败: {str(e)}"
            )

    def validate_path(self, path: str, validator_type: str = 'file') -> PathValidationResult:
        """验证路径"""
        if validator_type in self._validators:
            return self._validators[validator_type](path)
        else:
            return self.normalize_path(path)

    # === 路径记忆和历史记录功能 ===
    def remember_path(self, path_type: str, path: str):
        """记住用户选择的路径"""
        if self.user.general.remember_paths:
            self.user.remembered_paths[path_type] = path
            self.add_to_history(path_type, path)

    def get_remembered_path(self, path_type: str) -> Optional[str]:
        """获取记住的路径"""
        return self.user.remembered_paths.get(path_type)

    def add_to_history(self, path_type: str, path: str):
        """添加路径到历史记录"""
        if path_type not in self.user.path_history:
            self.user.path_history[path_type] = {
                "paths": [],
                "max_length": 10,
                "last_used": None
            }
        
        history = self.user.path_history[path_type]
        
        # 如果路径已存在，先移除
        if path in history["paths"]:
            history["paths"].remove(path)
        
        # 添加到开头
        history["paths"].insert(0, path)
        
        # 限制历史记录长度
        if len(history["paths"]) > history["max_length"]:
            history["paths"] = history["paths"][:history["max_length"]]
        
        history["last_used"] = path

    def get_path_history(self, path_type: str) -> List[str]:
        """获取路径历史记录"""
        return self.user.path_history.get(path_type, {}).get("paths", [])

    def get_last_used_path(self, path_type: str) -> Optional[str]:
        """获取最后使用的路径"""
        return self.user.path_history.get(path_type, {}).get("last_used")

    # === 智能路径获取功能 ===
    def get_path_with_validation(self,
                                path_type: str,
                                prompt: str,
                                validator_type: str = 'file',
                                required: bool = True,
                                default: Optional[str] = None,
                                show_history: bool = True) -> Optional[str]:
        """
        获取路径输入，支持验证、记忆和历史记录
        
        Args:
            path_type: 路径类型标识
            prompt: 提示文本
            validator_type: 验证器类型
            required: 是否必需
            default: 默认路径
            show_history: 是否显示历史记录
            
        Returns:
            验证后的路径或None
        """
        try:
            # 检查记忆的路径
            remembered = self.get_remembered_path(path_type)
            if remembered and os.path.exists(remembered):
                use_remembered = input(f"{Fore.YELLOW}使用记忆的路径: {remembered} [y/n]: {Style.RESET_ALL}").strip().lower()
                if use_remembered in ['y', 'yes', '']:
                    return remembered
            
            # 显示历史记录
            if show_history:
                history = self.get_path_history(path_type)
                if history:
                    print(f"{Fore.CYAN}最近使用的路径：{Style.RESET_ALL}")
                    for i, path in enumerate(history[:5], 1):
                        if os.path.exists(path):
                            print(f"  {i}. {path}")
                    
                    choice = input(f"{Fore.CYAN}选择历史路径 (1-{min(5, len(history))}) 或按Enter继续: {Style.RESET_ALL}").strip()
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(history) and os.path.exists(history[idx]):
                            selected_path = history[idx]
                            self.remember_path(path_type, selected_path)
                            return selected_path
            
            # 用户输入路径
            while True:
                full_prompt = f"{Fore.CYAN}{prompt}"
                if default:
                    full_prompt += f" (默认: {default})"
                full_prompt += f": {Style.RESET_ALL}"
                
                user_input = input(full_prompt).strip() or default
                
                if not user_input:
                    if required:
                        print(f"{Fore.RED}❌ 路径不能为空{Style.RESET_ALL}")
                        continue
                    return None
                
                # 验证路径
                result = self.validate_path(user_input, validator_type)
                
                if result.is_valid:
                    # 记忆并保存到历史
                    final_path = str(result.path) if result.path else user_input
                    self.remember_path(path_type, final_path)
                    return final_path
                else:
                    print(f"{Fore.RED}❌ {result.message}{Style.RESET_ALL}")
                    
                    # 如果是目录不存在，询问是否创建
                    if validator_type == 'dir' and "不存在" in result.message:
                        if input(f"{Fore.YELLOW}目录不存在，是否创建？[y/n]: {Style.RESET_ALL}").lower() in ['y', 'yes']:
                            try:
                                Path(user_input).mkdir(parents=True, exist_ok=True)
                                print(f"{Fore.GREEN}✅ 目录已创建{Style.RESET_ALL}")
                                normalized_path = str(Path(user_input).resolve())
                                self.remember_path(path_type, normalized_path)
                                return normalized_path
                            except Exception as e:
                                print(f"{Fore.RED}❌ 创建目录失败: {e}{Style.RESET_ALL}")
                                continue
                    
                    continue
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}操作已取消{Style.RESET_ALL}")
            return None
        except Exception as e:
            logging.error(f"获取路径时发生错误: {e}")
            print(f"{Fore.RED}❌ 获取路径失败: {e}{Style.RESET_ALL}")
            return None

    # === 配置管理功能 ===
    def save_config(self, config_path: str = None):
        """保存配置到文件"""
        if not config_path:
            config_path = get_config_path()
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            config_dict = asdict(self)
            # 处理 set 类型字段
            if 'core' in config_dict and 'default_fields' in config_dict['core']:
                config_dict['core']['default_fields'] = list(config_dict['core']['default_fields'])
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logging.debug(f"配置已保存到: {config_path}")
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
            raise ConfigError(f"保存配置失败: {str(e)}")

    def show_config(self):
        """显示当前配置"""
        print(f"\n{Fore.BLUE}=== 当前配置 ==={Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}核心配置:{Style.RESET_ALL}")
        core_dict = asdict(self.core)
        for key, value in core_dict.items():
            if isinstance(value, set):
                value = f"[{len(value)}个字段]"
            print(f"  {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}用户偏好:{Style.RESET_ALL}")
        print(f"  提取偏好:")
        for key, value in asdict(self.user.extraction).items():
            print(f"    {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")
        
        print(f"  通用设置:")
        for key, value in asdict(self.user.general).items():
            print(f"    {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")
        
        print(f"  API配置:")
        api_dict = asdict(self.user.api)
        for key, value in api_dict.items():
            if 'key' in key.lower() and value:
                # 隐藏API密钥的具体值
                print(f"    {key}: {Fore.GREEN}{'*' * 8}...{Style.RESET_ALL}")
            else:
                print(f"    {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")

    def reset_config(self):
        """重置配置为默认值"""
        self.core = ExtendedCoreConfig()
        self.user = ExtendedUserConfig()
        logging.info("配置已重置为默认值")

    def export_config(self, export_path: str):
        """导出配置到指定文件"""
        try:
            config_dict = asdict(self)
            # 处理 set 类型字段
            if 'core' in config_dict and 'default_fields' in config_dict['core']:
                config_dict['core']['default_fields'] = list(config_dict['core']['default_fields'])
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"{Fore.GREEN}✅ 配置已导出到: {export_path}{Style.RESET_ALL}")
            logging.info(f"配置已导出到: {export_path}")
        except Exception as e:
            print(f"{Fore.RED}❌ 导出失败: {e}{Style.RESET_ALL}")
            raise ConfigError(f"导出配置失败: {str(e)}")

    def import_config(self, import_path: str):
        """从指定文件导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # 验证版本兼容性
            imported_version = config_dict.get('version', '1.0.0')
            if not self._is_compatible_version(imported_version):
                print(f"{Fore.YELLOW}⚠️ 配置文件版本不同: {imported_version} vs {self.version}{Style.RESET_ALL}")
                if input(f"{Fore.CYAN}是否继续导入？[y/N]: {Style.RESET_ALL}").lower() != 'y':
                    return
            
            # 处理 set 类型字段
            if 'core' in config_dict and 'default_fields' in config_dict['core']:
                if isinstance(config_dict['core']['default_fields'], list):
                    config_dict['core']['default_fields'] = set(config_dict['core']['default_fields'])
            
            # 更新配置
            if 'core' in config_dict:
                self.core = ExtendedCoreConfig(**config_dict['core'])
            if 'user' in config_dict:
                self.user = ExtendedUserConfig(**config_dict['user'])
            
            print(f"{Fore.GREEN}✅ 配置已导入{Style.RESET_ALL}")
            logging.info(f"配置已从 {import_path} 导入")
        except Exception as e:
            print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")
            raise ConfigError(f"导入配置失败: {str(e)}")

    def _is_compatible_version(self, version: str) -> bool:
        """检查版本兼容性"""
        try:
            current_major = int(self.version.split('.')[0])
            imported_major = int(version.split('.')[0])
            return current_major == imported_major
        except (ValueError, IndexError):
            return False

    def get_api_key(self, key_name: str) -> Optional[str]:
        """获取API密钥"""
        if key_name == "ALIYUN_ACCESS_KEY_ID":
            return self.user.api.aliyun_access_key_id
        elif key_name == "ALIYUN_ACCESS_KEY_SECRET":
            return self.user.api.aliyun_access_key_secret
        else:
            # 从环境变量获取
            return os.getenv(key_name)
    
    def set_api_key(self, key_name: str, key_value: str) -> None:
        """设置API密钥"""
        if key_name == "ALIYUN_ACCESS_KEY_ID":
            self.user.api.aliyun_access_key_id = key_value
        elif key_name == "ALIYUN_ACCESS_KEY_SECRET":
            self.user.api.aliyun_access_key_secret = key_value
        else:
            # 对于其他密钥，暂时不支持持久化存储
            # 可以在未来扩展
            logging.warning(f"不支持持久化存储的API密钥: {key_name}")

    @property
    def default_fields(self) -> set:
        """获取默认字段集合 - 兼容旧代码"""
        return self.core.default_fields

# === 全局配置管理 ===
_global_config_instance = None

def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(Path.home(), ".day_translation", "config.json")

def get_config() -> UnifiedConfig:
    """获取全局配置实例（单例模式）"""
    global _global_config_instance
    if _global_config_instance is None:
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                    
                # 处理 set 类型字段
                if 'core' in config_dict and 'default_fields' in config_dict['core']:
                    if isinstance(config_dict['core']['default_fields'], list):
                        config_dict['core']['default_fields'] = set(config_dict['core']['default_fields'])
                    
                _global_config_instance = UnifiedConfig(**config_dict)
                logging.debug(f"配置已加载: {config_path}")
            except Exception as e:
                logging.warning(f"加载配置文件失败，使用默认配置: {e}")
                _global_config_instance = UnifiedConfig()
        else:
            _global_config_instance = UnifiedConfig()
            # 首次运行时保存默认配置
            _global_config_instance.save_config()
            logging.info("已创建默认配置文件")
    
    return _global_config_instance

def save_config():
    """保存当前配置"""
    config = get_config()
    config.save_config()

def reset_config():
    """重置并重新加载配置"""
    global _global_config_instance
    _global_config_instance = None
    config = get_config()
    config.reset_config()
    config.save_config()
    return config
