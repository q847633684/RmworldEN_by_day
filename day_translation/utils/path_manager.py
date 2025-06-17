"""
路径管理模块 - 提供统一的路径管理功能，包括路径验证、记忆、历史记录等
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Callable, List, Set, Union
from dataclasses import dataclass, field
from colorama import Fore, Style

from .config import get_user_config, save_user_config_to_file
from .config import get_config, get_user_config

CONFIG = get_config()

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

class PathManager:
    """统一的路径管理器，提供路径验证、记忆、历史记录等功能"""
    
    def __init__(self):
        """初始化路径管理器"""
        self.user_config = get_user_config()
        self._history_file = os.path.join(os.path.dirname(__file__), ".day_translation_history.json")
        self._path_pattern = re.compile(r'^[a-zA-Z]:[\\/]|^[\\/]{2}|^[a-zA-Z0-9_\-\.]+[\\/]')
        self._history_cache: Dict[str, PathHistory] = {}
        self._load_history()
          # 注册路径验证器
        self._validators: Dict[str, Callable[[str], PathValidationResult]] = {
            'dir': self._validate_directory,
            'file': self._validate_file,
            'csv': self._validate_csv_file,
            'xml': self._validate_xml_file,
            'json': self._validate_json_file,
            'mod': self._validate_mod_directory,
            'language': self._validate_language_directory,
            'output_dir': self._validate_output_directory
        }
        
    def _load_history(self) -> None:
        """加载历史记录"""
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, paths in data.items():
                        self._history_cache[key] = PathHistory(
                            paths=self._sanitize_history(paths),
                            last_used=paths[0] if paths else None
                        )
        except Exception as e:
            logging.error(f"加载历史记录失败: {e}")
            self._history_cache = {}
            
    def _save_history(self) -> None:
        """保存历史记录"""
        try:
            data = {
                key: history.paths
                for key, history in self._history_cache.items()
                if history.paths
            }
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存历史记录失败: {e}")
            
    def _sanitize_history(self, paths: List[str]) -> List[str]:
        """清理历史记录"""
        sanitized = []
        for path in paths:
            try:
                result = self._normalize_path(path)
                if result.is_valid and os.path.exists(result.normalized_path):
                    sanitized.append(result.normalized_path)
            except Exception:
                continue
        return sanitized[:10]  # 限制历史记录长度
        
    def _normalize_path(self, path: str) -> PathValidationResult:
        """
        规范化路径
        
        Args:
            path (str): 输入路径
            
        Returns:
            PathValidationResult: 验证结果
        """
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
            
    def get_path(self,
                path_type: str,
                prompt: str,
                validator_type: str = 'file',
                required: bool = True,
                default: Optional[str] = None) -> Optional[str]:
        """
        获取路径输入，支持记忆和历史记录
        
        Args:
            path_type (str): 路径类型
            prompt (str): 提示文本
            validator_type (str): 验证器类型
            required (bool): 是否必需
            default (Optional[str]): 默认路径
            
        Returns:
            Optional[str]: 验证后的路径
        """
        try:
            # 检查默认路径
            if default:
                result = self._normalize_path(default)
                if result.is_valid and os.path.exists(result.normalized_path):
                    use_default = input(f"{Fore.YELLOW}使用默认路径: {result.normalized_path} [y/n]: {Style.RESET_ALL}").strip().lower()
                    if use_default == 'y':
                        return result.normalized_path
                        
            # 获取历史记录
            history = self._history_cache.get(path_type, PathHistory())
            
            # 显示历史记录
            if history.paths:
                print(f"\n{Fore.BLUE}历史记录：{Style.RESET_ALL}")
                for i, path in enumerate(history.paths, 1):
                    print(f"{i}. {path}")
                print(f"0. {Fore.YELLOW}输入新路径{Style.RESET_ALL}")
                
            # 获取用户输入
            while True:
                choice = input(f"\n{Fore.CYAN}{prompt}{Style.RESET_ALL}").strip()
                
                if choice.lower() == 'q':
                    return None
                    
                if choice.isdigit() and 0 <= int(choice) <= len(history.paths):
                    if int(choice) == 0:
                        path = input(f"{Fore.CYAN}请输入新路径：{Style.RESET_ALL}").strip()
                    else:
                        path = history.paths[int(choice) - 1]
                else:
                    path = choice
                    
                if not path and not required:
                    return None
                    
                # 验证路径
                validator = self._validators.get(validator_type, self._validate_file)
                result = validator(path)
                
                if result.is_valid:
                    # 更新历史记录
                    if path_type not in self._history_cache:
                        self._history_cache[path_type] = PathHistory()
                    history = self._history_cache[path_type]
                    if result.normalized_path in history.paths:
                        history.paths.remove(result.normalized_path)
                    history.paths.insert(0, result.normalized_path)
                    history.paths = history.paths[:history.max_length]
                    history.last_used = result.normalized_path
                    self._save_history()
                    
                    return result.normalized_path
                else:
                    print(f"{Fore.RED}{result.error_message}{Style.RESET_ALL}")
                    
        except Exception as e:
            logging.error(f"获取路径失败: {e}")
            print(f"{Fore.RED}获取路径时发生错误: {e}{Style.RESET_ALL}")
            return None
            
    def remember_path(self, path_type: str, path: str) -> bool:
        """
        记住路径
        
        Args:
            path_type (str): 路径类型
            path (str): 路径
            
        Returns:
            bool: 是否成功
        """
        try:
            result = self._normalize_path(path)
            if not result.is_valid:
                return False
                
            # 更新用户配置
            self.user_config[f"default_{path_type}"] = result.normalized_path
            save_user_config_to_file(self.user_config)
            
            # 更新历史记录
            if path_type not in self._history_cache:
                self._history_cache[path_type] = PathHistory()
            history = self._history_cache[path_type]
            if result.normalized_path in history.paths:
                history.paths.remove(result.normalized_path)
            history.paths.insert(0, result.normalized_path)
            history.paths = history.paths[:history.max_length]
            history.last_used = result.normalized_path
            self._save_history()
            
            return True
        except Exception as e:
            logging.error(f"记住路径失败: {e}")
            return False
            
    def get_remembered_path(self, path_type: str) -> Optional[str]:
        """
        获取记忆的路径
        
        Args:
            path_type (str): 路径类型
            
        Returns:
            Optional[str]: 记忆的路径
        """
        try:
            path = self.user_config.get(f"default_{path_type}")
            if path:
                result = self._normalize_path(path)
                if result.is_valid and os.path.exists(result.normalized_path):
                    return result.normalized_path
        except Exception as e:
            logging.error(f"获取记忆路径失败: {e}")
        return None
        
    def _validate_directory(self, path: str) -> PathValidationResult:
        """验证目录"""
        result = self._normalize_path(path)
        if not result.is_valid:
            return result
            
        try:
            path_obj = Path(result.normalized_path)
            if not path_obj.is_dir():
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"目录不存在: {path}",
                    normalized_path=result.normalized_path
                )
            if not os.access(result.normalized_path, os.R_OK | os.W_OK):
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"目录无法访问: {path}",
                    normalized_path=result.normalized_path
                )
            return PathValidationResult(
                is_valid=True,
                normalized_path=result.normalized_path,
                path_type='dir'
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录验证失败: {str(e)}",
                normalized_path=result.normalized_path
            )
            
    def _validate_file(self, path: str) -> PathValidationResult:
        """验证文件"""
        result = self._normalize_path(path)
        if not result.is_valid:
            return result
            
        try:
            path_obj = Path(result.normalized_path)
            if path_obj.is_file():
                if not os.access(result.normalized_path, os.R_OK):
                    return PathValidationResult(
                        is_valid=False,
                        error_message=f"文件无法访问: {path}",
                        normalized_path=result.normalized_path
                    )
            else:
                parent_dir = path_obj.parent or Path('.')
                if not parent_dir.is_dir() or not os.access(str(parent_dir), os.W_OK):
                    return PathValidationResult(
                        is_valid=False,
                        error_message=f"父目录不存在或无法写入: {path}",
                        normalized_path=result.normalized_path
                    )
            return PathValidationResult(
                is_valid=True,
                normalized_path=result.normalized_path,
                path_type='file'
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件验证失败: {str(e)}",
                normalized_path=result.normalized_path
            )
            
    def _validate_csv_file(self, path: str) -> PathValidationResult:
        """验证CSV文件"""
        result = self._validate_file(path)
        if not result.is_valid:
            return result
            
        if not Path(result.normalized_path).suffix.lower() == '.csv':
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件必须是CSV格式: {path}",
                normalized_path=result.normalized_path
            )
        return PathValidationResult(
            is_valid=True,
            normalized_path=result.normalized_path,
            path_type='csv'
        )
        
    def _validate_xml_file(self, path: str) -> PathValidationResult:
        """验证XML文件"""
        result = self._validate_file(path)
        if not result.is_valid:
            return result
            
        if not Path(result.normalized_path).suffix.lower() == '.xml':
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件必须是XML格式: {path}",
                normalized_path=result.normalized_path
            )
        return PathValidationResult(
            is_valid=True,
            normalized_path=result.normalized_path,
            path_type='xml'
        )
        
    def _validate_json_file(self, path: str) -> PathValidationResult:
        """验证JSON文件"""
        result = self._validate_file(path)
        if not result.is_valid:
            return result
            
        if not Path(result.normalized_path).suffix.lower() == '.json':
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件必须是JSON格式: {path}",
                normalized_path=result.normalized_path
            )
        return PathValidationResult(
            is_valid=True,
            normalized_path=result.normalized_path,
            path_type='json'
        )
        
    def _validate_mod_directory(self, path: str) -> PathValidationResult:
        """验证模组目录"""
        result = self._validate_directory(path)
        if not result.is_valid:
            return result
            
        # 检查模组目录结构
        required_dirs = {'Languages', 'Defs', 'Textures', 'Sounds'}
        found_dirs = {d.name for d in Path(result.normalized_path).iterdir() if d.is_dir()}
        
        if not required_dirs.intersection(found_dirs):
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录不是有效的模组目录: {path}",
                normalized_path=result.normalized_path
            )
        return PathValidationResult(
            is_valid=True,
            normalized_path=result.normalized_path,
            path_type='mod'
        )
        
    def _validate_language_directory(self, path: str) -> PathValidationResult:
        """验证语言目录"""
        result = self._validate_directory(path)
        if not result.is_valid:
            return result
            
        # 检查语言目录结构
        required_dirs = {CONFIG.def_injected_dir, CONFIG.keyed_dir}
        found_dirs = {d.name for d in Path(result.normalized_path).iterdir() if d.is_dir()}
        
        if not required_dirs.intersection(found_dirs):
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录不是有效的语言目录: {path}",
                normalized_path=result.normalized_path
            )
        return PathValidationResult(
            is_valid=True,
            normalized_path=result.normalized_path,
            path_type='language'
        )
        
    def _validate_output_directory(self, path: str) -> PathValidationResult:
        """验证输出目录，如果不存在则创建"""
        try:
            path_obj = Path(path)
            
            # 如果路径不存在，尝试创建
            if not path_obj.exists():
                path_obj.mkdir(parents=True, exist_ok=True)
                
            # 验证是否为目录
            if not path_obj.is_dir():
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"路径不是目录: {path}",
                    normalized_path=str(path_obj.resolve())
                )
                
            # 检查写入权限
            test_file = path_obj / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"目录没有写入权限: {path}",
                    normalized_path=str(path_obj.resolve())
                )
                
            return PathValidationResult(
                is_valid=True,
                normalized_path=str(path_obj.resolve()),
                path_type='output_dir'
            )
            
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"验证输出目录失败: {str(e)}",
                normalized_path=str(Path(path).resolve()) if path else ""
            )
        
    def get_language_folder_path(self, mod_dir: str, language: str) -> str:
        """
        获取语言文件夹路径
        
        Args:
            mod_dir (str): 模组目录
            language (str): 语言代码
            
        Returns:
            str: 语言文件夹路径
        """
        return os.path.join(mod_dir, "Languages", language)
        
    def ensure_directory(self, path: str) -> bool:
        """
        确保目录存在
        
        Args:
            path (str): 目录路径
            
        Returns:
            bool: 是否成功
        """
        try:
            result = self._normalize_path(path)
            if not result.is_valid:
                return False
                
            os.makedirs(result.normalized_path, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"创建目录失败: {e}")
            return False
            
    def get_relative_path(self, path: str, base: str) -> Optional[str]:
        """
        获取相对路径
        
        Args:
            path (str): 目标路径
            base (str): 基准路径
            
        Returns:
            Optional[str]: 相对路径
        """
        try:
            path_result = self._normalize_path(path)
            base_result = self._normalize_path(base)
            
            if not path_result.is_valid or not base_result.is_valid:
                return None
                
            return os.path.relpath(path_result.normalized_path, base_result.normalized_path)
        except Exception as e:
            logging.error(f"获取相对路径失败: {e}")
            return None