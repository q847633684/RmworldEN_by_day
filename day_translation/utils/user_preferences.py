"""
用户偏好和交互管理模块
负责管理用户选择、配置记忆、交互界面等功能，包含路径管理功能
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict, field
from colorama import Fore, Style

@dataclass
class PathValidationResult:
    """路径验证结果"""
    is_valid: bool
    error_message: Optional[str] = None
    normalized_path: Optional[str] = None
    path_type: Optional[str] = None

@dataclass
class PathHistory:
    """路径历史记录"""
    paths: List[str] = field(default_factory=list)
    max_length: int = 10
    last_used: Optional[str] = None

@dataclass
class ExtractionPreferences:
    """提取操作的用户偏好"""
    output_location: str = "external"  # "internal" 或 "external"
    output_dir: Optional[str] = None
    en_keyed_dir: Optional[str] = None
    auto_detect_en_keyed: bool = True
    auto_choose_definjected: bool = False
    structure_choice: str = "original"  # "original", "defs", "structured"
    merge_mode: str = "smart-merge"  # "merge", "replace", "backup", "skip", "smart-merge"
    
@dataclass 
class ImportPreferences:
    """导入操作的用户偏好"""
    merge_existing: bool = True
    backup_before_import: bool = True
    
@dataclass
class TranslationPreferences:
    """翻译操作的用户偏好"""
    auto_translate: bool = False
    save_api_keys: bool = True
    
@dataclass
class GeneralPreferences:
    """通用偏好设置"""
    remember_paths: bool = True
    auto_mode: bool = False  # 是否启用自动模式（使用上次配置）
    confirm_operations: bool = True
    
@dataclass
class UserPreferences:
    """用户偏好的完整配置"""
    extraction: ExtractionPreferences
    import_prefs: ImportPreferences
    translation: TranslationPreferences
    general: GeneralPreferences
    
    def __post_init__(self):
        # 确保子对象都是正确的类型
        if isinstance(self.extraction, dict):
            self.extraction = ExtractionPreferences(**self.extraction)
        if isinstance(self.import_prefs, dict):
            self.import_prefs = ImportPreferences(**self.import_prefs)
        if isinstance(self.translation, dict):
            self.translation = TranslationPreferences(**self.translation)
        if isinstance(self.general, dict):
            self.general = GeneralPreferences(**self.general)

class UserPreferencesManager:
    """用户偏好管理器，集成路径管理功能"""
    
    def __init__(self, config_dir: str = None):
        """初始化偏好管理器"""
        if config_dir is None:
            config_dir = os.path.join(Path.home(), ".day_translation")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.preferences_file = self.config_dir / "user_preferences.json"
        self.paths_file = self.config_dir / "remembered_paths.json"
        self.history_file = self.config_dir / "path_history.json"
        
        self._preferences: Optional[UserPreferences] = None
        self._remembered_paths: Dict[str, str] = {}
        self._path_history: Dict[str, PathHistory] = {}
        
        # 路径验证相关
        self._path_pattern = re.compile(r'^[a-zA-Z]:[\\/]|^[\\/]{2}|^[a-zA-Z0-9_\-\.]+[\\/]')
        self._validators: Dict[str, Callable[[str], PathValidationResult]] = {
            'dir': self._validate_directory,
            'file': self._validate_file,
            'csv': self._validate_csv_file,
            'xml': self._validate_xml_file,
            'json': self._validate_json_file,
            'mod': self._validate_mod_directory,
        }
        
        self.load_preferences()
        self.load_remembered_paths()
        self.load_path_history()
        
    # === 路径验证功能 ===
    def _validate_directory(self, path: str) -> PathValidationResult:
        """验证目录路径"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"目录不存在: {path}"
                )
            if not path_obj.is_dir():
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"路径不是目录: {path}"
                )
            return PathValidationResult(
                is_valid=True,
                normalized_path=str(path_obj.resolve()),
                path_type="directory"
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录验证失败: {str(e)}"
            )
    
    def _validate_file(self, path: str) -> PathValidationResult:
        """验证文件路径"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"文件不存在: {path}"
                )
            if not path_obj.is_file():
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"路径不是文件: {path}"
                )
            return PathValidationResult(
                is_valid=True,
                normalized_path=str(path_obj.resolve()),
                path_type="file"
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件验证失败: {str(e)}"
            )
    
    def _validate_csv_file(self, path: str) -> PathValidationResult:
        """验证CSV文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith('.csv'):
            return PathValidationResult(
                is_valid=False,
                error_message="文件必须是CSV格式"
            )
        return result
    
    def _validate_xml_file(self, path: str) -> PathValidationResult:
        """验证XML文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith('.xml'):
            return PathValidationResult(
                is_valid=False,
                error_message="文件必须是XML格式"
            )
        return result
    
    def _validate_json_file(self, path: str) -> PathValidationResult:
        """验证JSON文件路径"""
        result = self._validate_file(path)
        if result.is_valid and not path.lower().endswith('.json'):
            return PathValidationResult(
                is_valid=False,
                error_message="文件必须是JSON格式"
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
                    error_message="目录中未找到Languages文件夹，可能不是有效的模组目录"
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
                    error_message="无效的路径格式"
                )
            return PathValidationResult(
                is_valid=True,
                normalized_path=normalized
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"路径规范化失败: {str(e)}"
            )
    
    def validate_path(self, path: str, validator_type: str = 'file') -> PathValidationResult:
        """验证路径"""
        if validator_type in self._validators:
            return self._validators[validator_type](path)
        else:
            return self.normalize_path(path)
    
    # === 路径历史记录功能 ===
    def add_to_history(self, path_type: str, path: str):
        """添加路径到历史记录"""
        if path_type not in self._path_history:
            self._path_history[path_type] = PathHistory()
        
        history = self._path_history[path_type]
        
        # 如果路径已存在，先移除
        if path in history.paths:
            history.paths.remove(path)
        
        # 添加到开头
        history.paths.insert(0, path)
        
        # 限制历史记录长度
        if len(history.paths) > history.max_length:
            history.paths = history.paths[:history.max_length]
        
        history.last_used = path
        self.save_path_history()
    
    def get_path_history(self, path_type: str) -> List[str]:
        """获取路径历史记录"""
        return self._path_history.get(path_type, PathHistory()).paths
    
    def get_last_used_path(self, path_type: str) -> Optional[str]:
        """获取最后使用的路径"""
        return self._path_history.get(path_type, PathHistory()).last_used
    
    def save_path_history(self):
        """保存路径历史记录到文件"""
        try:
            # 转换为可序列化的格式
            history_data = {}
            for path_type, history in self._path_history.items():
                history_data[path_type] = asdict(history)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            logging.debug(f"路径历史记录已保存到: {self.history_file}")
        except Exception as e:
            logging.error(f"保存路径历史记录失败: {e}")
    
    def load_path_history(self):
        """从文件加载路径历史记录"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # 转换为PathHistory对象
                for path_type, data in history_data.items():
                    self._path_history[path_type] = PathHistory(**data)
                
                logging.debug(f"路径历史记录已加载: {self.history_file}")
        except Exception as e:
            logging.error(f"加载路径历史记录失败: {e}")
            self._path_history = {}
    
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
                    self.remember_path(path_type, result.normalized_path)
                    self.add_to_history(path_type, result.normalized_path)
                    return result.normalized_path
                else:
                    print(f"{Fore.RED}❌ {result.error_message}{Style.RESET_ALL}")
                    
                    # 如果是目录不存在，询问是否创建
                    if validator_type == 'dir' and "不存在" in result.error_message:
                        if input(f"{Fore.YELLOW}目录不存在，是否创建？[y/n]: {Style.RESET_ALL}").lower() in ['y', 'yes']:
                            try:
                                Path(user_input).mkdir(parents=True, exist_ok=True)
                                print(f"{Fore.GREEN}✅ 目录已创建{Style.RESET_ALL}")
                                normalized_path = str(Path(user_input).resolve())
                                self.remember_path(path_type, normalized_path)
                                self.add_to_history(path_type, normalized_path)
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

    # === 原有偏好管理功能 ===
    def get_preferences(self) -> UserPreferences:
        """获取用户偏好设置"""
        if self._preferences is None:
            self._preferences = UserPreferences(
                extraction=ExtractionPreferences(),
                import_prefs=ImportPreferences(),
                translation=TranslationPreferences(),
                general=GeneralPreferences()
            )
        return self._preferences
    
    def save_preferences(self):
        """保存用户偏好到文件"""
        try:
            preferences_dict = asdict(self.get_preferences())
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences_dict, f, indent=2, ensure_ascii=False)
            logging.debug(f"用户偏好已保存到: {self.preferences_file}")
        except Exception as e:
            logging.error(f"保存用户偏好失败: {e}")
    
    def load_preferences(self):
        """从文件加载用户偏好"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._preferences = UserPreferences(**data)
                logging.debug(f"用户偏好已加载: {self.preferences_file}")
            else:
                self._preferences = None
                logging.debug("用户偏好文件不存在，将使用默认设置")
        except Exception as e:
            logging.error(f"加载用户偏好失败: {e}")
            self._preferences = None
    
    def remember_path(self, path_type: str, path: str):
        """记住用户选择的路径"""
        if self.get_preferences().general.remember_paths:
            self._remembered_paths[path_type] = path
            self.save_remembered_paths()
    
    def get_remembered_path(self, path_type: str) -> Optional[str]:
        """获取记住的路径"""
        return self._remembered_paths.get(path_type)
    
    def save_remembered_paths(self):
        """保存记住的路径到文件"""
        try:
            with open(self.paths_file, 'w', encoding='utf-8') as f:
                json.dump(self._remembered_paths, f, indent=2, ensure_ascii=False)
            logging.debug(f"记住的路径已保存到: {self.paths_file}")
        except Exception as e:
            logging.error(f"保存记住的路径失败: {e}")
    
    def load_remembered_paths(self):
        """从文件加载记住的路径"""
        try:
            if self.paths_file.exists():
                with open(self.paths_file, 'r', encoding='utf-8') as f:
                    self._remembered_paths = json.load(f)
                logging.debug(f"记住的路径已加载: {self.paths_file}")
        except Exception as e:
            logging.error(f"加载记住的路径失败: {e}")
            self._remembered_paths = {}
    
    def reset_preferences(self):
        """重置用户偏好为默认值"""
        self._preferences = UserPreferences(
            extraction=ExtractionPreferences(),
            import_prefs=ImportPreferences(),
            translation=TranslationPreferences(),
            general=GeneralPreferences()
        )
        self.save_preferences()
        logging.info("用户偏好已重置为默认值")
    
    def clear_remembered_paths(self):
        """清空记住的路径"""
        self._remembered_paths = {}
        self.save_remembered_paths()
        logging.info("记住的路径已清空")

class UserInteraction:
    """用户交互界面管理器"""
    
    def __init__(self, preferences_manager: UserPreferencesManager):
        self.preferences_manager = preferences_manager
    
    def ask_use_previous_config(self, operation_name: str) -> bool:
        """询问用户是否使用上次的配置"""
        prefs = self.preferences_manager.get_preferences()
        
        if prefs.general.auto_mode:
            print(f"{Fore.GREEN}🔄 自动模式：使用上次配置进行{operation_name}{Style.RESET_ALL}")
            return True
        
        print(f"\n{Fore.CYAN}=== {operation_name} 配置选择 ==={Style.RESET_ALL}")
        print(f"1. {Fore.GREEN}使用上次配置{Style.RESET_ALL}（快速开始）")
        print(f"2. {Fore.YELLOW}重新配置{Style.RESET_ALL}（自定义设置）")
        print(f"3. {Fore.BLUE}查看上次配置{Style.RESET_ALL}（查看后再决定）")
        
        while True:
            choice = input(f"{Fore.CYAN}请选择 (1-3): {Style.RESET_ALL}").strip()
            
            if choice == "1":
                return True
            elif choice == "2":
                return False
            elif choice == "3":
                self.show_current_extraction_config()
                continue
            else:
                print(f"{Fore.RED}❌ 请输入 1-3{Style.RESET_ALL}")
    
    def show_current_extraction_config(self):
        """显示当前的提取配置"""
        prefs = self.preferences_manager.get_preferences()
        extraction = prefs.extraction
        
        print(f"\n{Fore.BLUE}=== 当前提取配置 ==={Style.RESET_ALL}")
        print(f"输出位置: {Fore.GREEN}{extraction.output_location}{Style.RESET_ALL}")
        if extraction.output_dir:
            print(f"输出目录: {Fore.GREEN}{extraction.output_dir}{Style.RESET_ALL}")
        if extraction.en_keyed_dir:
            print(f"英文Keyed目录: {Fore.GREEN}{extraction.en_keyed_dir}{Style.RESET_ALL}")
        print(f"结构选择: {Fore.GREEN}{extraction.structure_choice}{Style.RESET_ALL}")
        print(f"合并模式: {Fore.GREEN}{extraction.merge_mode}{Style.RESET_ALL}")
        print(f"自动检测英文Keyed: {Fore.GREEN}{'是' if extraction.auto_detect_en_keyed else '否'}{Style.RESET_ALL}")
        print(f"自动选择DefInjected: {Fore.GREEN}{'是' if extraction.auto_choose_definjected else '否'}{Style.RESET_ALL}")
    
    def configure_extraction_preferences(self, mod_dir: str) -> Tuple[bool, ExtractionPreferences]:
        """配置提取偏好设置
        
        Returns:
            Tuple[bool, ExtractionPreferences]: (是否取消, 配置对象)
        """
        prefs = self.preferences_manager.get_preferences()
        extraction = ExtractionPreferences()
        
        # 1. 选择输出位置
        print(f"\n{Fore.CYAN}1. 请选择模板输出位置：{Style.RESET_ALL}")
        print(f"   1. {Fore.GREEN}模组内部{Style.RESET_ALL}（直接集成到模组Languages目录）")
        print(f"   2. {Fore.GREEN}外部目录{Style.RESET_ALL}（独立管理，推荐）")
        
        default_choice = "2" if prefs.extraction.output_location == "external" else "1"
        choice = input(f"{Fore.CYAN}请选择 (1/2, 默认{default_choice}): {Style.RESET_ALL}").strip() or default_choice
        
        if choice == "1":
            extraction.output_location = "internal"
            extraction.output_dir = None
        else:
            extraction.output_location = "external"
            # 获取输出目录
            default_dir = self.preferences_manager.get_remembered_path("output_dir") or "提取的翻译"
            extraction.output_dir = self._get_directory_path("输出目录", default_dir)
            if not extraction.output_dir:
                return True, extraction  # 用户取消
        
        # 2. 英文Keyed目录配置
        auto_en_keyed_dir = os.path.join(mod_dir, "Languages", "English", "Keyed")
        
        if os.path.exists(auto_en_keyed_dir):
            print(f"\n{Fore.GREEN}✅ 检测到英文Keyed目录: {auto_en_keyed_dir}{Style.RESET_ALL}")
            if input(f"{Fore.CYAN}是否使用检测到的目录？[Y/n]: {Style.RESET_ALL}").lower() not in ['n', 'no']:
                extraction.en_keyed_dir = auto_en_keyed_dir
                extraction.auto_detect_en_keyed = True
            else:
                extraction.en_keyed_dir = self._get_directory_path("英文Keyed目录", 
                    self.preferences_manager.get_remembered_path("en_keyed_dir"), required=False)
                extraction.auto_detect_en_keyed = False
        else:
            print(f"\n{Fore.YELLOW}⚠️ 未检测到标准英文Keyed目录{Style.RESET_ALL}")
            if input(f"{Fore.CYAN}是否手动指定英文Keyed目录？[y/N]: {Style.RESET_ALL}").lower() in ['y', 'yes']:
                extraction.en_keyed_dir = self._get_directory_path("英文Keyed目录", 
                    self.preferences_manager.get_remembered_path("en_keyed_dir"), required=False)
                extraction.auto_detect_en_keyed = False
        
        # 3. 结构选择
        print(f"\n{Fore.CYAN}3. 选择输出结构：{Style.RESET_ALL}")
        print(f"   1. {Fore.GREEN}原始结构{Style.RESET_ALL}（保持原有目录结构，推荐）")
        print(f"   2. {Fore.GREEN}Defs结构{Style.RESET_ALL}（按Defs分类）")
        print(f"   3. {Fore.GREEN}结构化{Style.RESET_ALL}（高度组织化）")
        
        structure_map = {"1": "original", "2": "defs", "3": "structured"}
        reverse_map = {v: k for k, v in structure_map.items()}
        default_structure = reverse_map.get(prefs.extraction.structure_choice, "1")
        
        choice = input(f"{Fore.CYAN}请选择 (1-3, 默认{default_structure}): {Style.RESET_ALL}").strip() or default_structure
        extraction.structure_choice = structure_map.get(choice, "original")
        
        # 4. 合并模式选择
        print(f"\n{Fore.CYAN}4. 选择合并模式（处理已有翻译文件的方式）：{Style.RESET_ALL}")
        print(f"   1. {Fore.GREEN}智能合并{Style.RESET_ALL}（推荐：保留手动编辑，添加新条目）")
        print(f"   2. {Fore.YELLOW}传统合并{Style.RESET_ALL}（只更新现有条目）")
        print(f"   3. {Fore.BLUE}备份替换{Style.RESET_ALL}（备份后完全替换）")
        print(f"   4. {Fore.RED}直接替换{Style.RESET_ALL}（完全替换，不备份）")
        print(f"   5. {Fore.MAGENTA}跳过处理{Style.RESET_ALL}（跳过已有文件）")
        
        merge_map = {"1": "smart-merge", "2": "merge", "3": "backup", "4": "replace", "5": "skip"}
        reverse_merge_map = {v: k for k, v in merge_map.items()}
        default_merge = reverse_merge_map.get(prefs.extraction.merge_mode, "1")
        
        choice = input(f"{Fore.CYAN}请选择 (1-5, 默认{default_merge}): {Style.RESET_ALL}").strip() or default_merge
        extraction.merge_mode = merge_map.get(choice, "smart-merge")
        
        # 5. 其他选项
        print(f"\n{Fore.CYAN}5. 其他选项：{Style.RESET_ALL}")
        
        default_auto_def = "y" if prefs.extraction.auto_choose_definjected else "n"
        auto_def = input(f"{Fore.CYAN}自动选择DefInjected提取方式？[y/N, 默认{default_auto_def}]: {Style.RESET_ALL}").lower() or default_auto_def
        extraction.auto_choose_definjected = auto_def in ['y', 'yes']
        
        return False, extraction
    
    def _get_directory_path(self, name: str, default: str = None, required: bool = True) -> Optional[str]:
        """获取目录路径输入"""
        while True:
            prompt = f"{Fore.CYAN}请输入{name}"
            if default:
                prompt += f"（默认: {default}）"
            prompt += f": {Style.RESET_ALL}"
            
            path = input(prompt).strip() or default
            
            if not path:
                if not required:
                    return None
                print(f"{Fore.RED}❌ {name}不能为空{Style.RESET_ALL}")
                continue
            
            path = Path(path).resolve()
            
            if not path.exists():
                if input(f"{Fore.YELLOW}目录不存在，是否创建？[Y/n]: {Style.RESET_ALL}").lower() not in ['n', 'no']:
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        print(f"{Fore.GREEN}✅ 目录已创建: {path}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}❌ 创建目录失败: {e}{Style.RESET_ALL}")
                        continue
                else:
                    continue
            
            if not path.is_dir():
                print(f"{Fore.RED}❌ 路径不是有效目录{Style.RESET_ALL}")
                continue
            
            # 记住用户选择
            path_type = name.replace(" ", "_").lower()
            self.preferences_manager.remember_path(path_type, str(path))
            
            return str(path)
    
    def ask_save_current_config(self) -> bool:
        """询问是否保存当前配置"""
        prefs = self.preferences_manager.get_preferences()
        if prefs.general.auto_mode:
            return True  # 自动模式下总是保存
        
        return input(f"{Fore.CYAN}保存当前配置供下次使用？[Y/n]: {Style.RESET_ALL}").lower() not in ['n', 'no']
    
    def configure_general_preferences(self):
        """配置通用偏好设置"""
        prefs = self.preferences_manager.get_preferences()
        
        print(f"\n{Fore.BLUE}=== 通用设置配置 ==={Style.RESET_ALL}")
        
        # 自动模式
        current_auto = "是" if prefs.general.auto_mode else "否"
        auto_mode = input(f"{Fore.CYAN}启用自动模式（使用上次配置）？当前: {current_auto} [y/n/Enter保持]: {Style.RESET_ALL}").lower()
        if auto_mode in ['y', 'yes']:
            prefs.general.auto_mode = True
        elif auto_mode in ['n', 'no']:
            prefs.general.auto_mode = False
        
        # 记住路径
        current_remember = "是" if prefs.general.remember_paths else "否"
        remember = input(f"{Fore.CYAN}记住用户选择的路径？当前: {current_remember} [y/n/Enter保持]: {Style.RESET_ALL}").lower()
        if remember in ['y', 'yes']:
            prefs.general.remember_paths = True
        elif remember in ['n', 'no']:
            prefs.general.remember_paths = False
        
        # 操作确认
        current_confirm = "是" if prefs.general.confirm_operations else "否"
        confirm = input(f"{Fore.CYAN}重要操作前需要确认？当前: {current_confirm} [y/n/Enter保持]: {Style.RESET_ALL}").lower()
        if confirm in ['y', 'yes']:
            prefs.general.confirm_operations = True
        elif confirm in ['n', 'no']:
            prefs.general.confirm_operations = False
        
        self.preferences_manager.save_preferences()
        print(f"{Fore.GREEN}✅ 通用设置已保存{Style.RESET_ALL}")

@dataclass
class PathValidationResult:
    """路径验证结果"""
    is_valid: bool
    error_message: Optional[str] = None
    normalized_path: Optional[str] = None
    path_type: Optional[str] = None

@dataclass
class PathHistory:
    """路径历史记录"""
    paths: List[str] = field(default_factory=list)
    max_length: int = 10
    last_used: Optional[str] = None

