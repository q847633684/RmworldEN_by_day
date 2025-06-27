"""
环境检测模块 - 检测模组翻译资源和输出目录状态
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from colorama import Fore, Style

from .config import get_config

CONFIG = get_config()

@dataclass
class ResourceStatus:
    """资源状态数据类"""
    exists: bool
    path: Optional[str] = None
    file_count: int = 0
    size_mb: float = 0.0
    last_modified: Optional[str] = None

@dataclass
class EnvironmentStatus:
    """环境状态数据类"""
    english_definjected: ResourceStatus
    english_keyed: ResourceStatus
    output_definjected: ResourceStatus
    output_keyed: ResourceStatus
    mod_dir: str
    output_dir: Optional[str] = None

class EnvironmentDetector:
    """环境状态检测器"""
    
    def __init__(self):
        """初始化检测器"""
        self.logger = logging.getLogger(__name__)
    
    def detect_full_environment(self, mod_dir: str, output_dir: Optional[str] = None) -> EnvironmentStatus:
        """
        全面检测提取环境状态
        
        Args:
            mod_dir (str): 模组目录路径
            output_dir (Optional[str]): 输出目录路径
            
        Returns:
            EnvironmentStatus: 完整的环境状态信息
        """
        self.logger.info(f"开始检测环境状态: mod_dir={mod_dir}, output_dir={output_dir}")
        
        # 检测模组翻译资源
        english_definjected = self._detect_english_definjected(mod_dir)
        english_keyed = self._detect_english_keyed(mod_dir)
        
        # 检测输出目录状态
        if output_dir:
            output_definjected = self._detect_output_definjected(output_dir)
            output_keyed = self._detect_output_keyed(output_dir)
        else:
            # 如果没有指定输出目录，检测模组内部目录
            output_definjected = self._detect_output_definjected(mod_dir, is_internal=True)
            output_keyed = self._detect_output_keyed(mod_dir, is_internal=True)
        
        return EnvironmentStatus(
            english_definjected=english_definjected,
            english_keyed=english_keyed,
            output_definjected=output_definjected,
            output_keyed=output_keyed,
            mod_dir=mod_dir,
            output_dir=output_dir
        )
    
    def _detect_english_definjected(self, mod_dir: str) -> ResourceStatus:
        """检测英文 DefInjected 目录"""
        definjected_path = Path(mod_dir) / "Languages" / CONFIG.source_language / CONFIG.def_injected_dir
        return self._analyze_directory(definjected_path, "*.xml")
    
    def _detect_english_keyed(self, mod_dir: str) -> ResourceStatus:
        """检测英文 Keyed 目录"""
        keyed_path = Path(mod_dir) / "Languages" / CONFIG.source_language / CONFIG.keyed_dir
        return self._analyze_directory(keyed_path, "*.xml")
    
    def _detect_output_definjected(self, output_dir: str, is_internal: bool = False) -> ResourceStatus:
        """检测输出 DefInjected 目录"""
        if is_internal:
            definjected_path = Path(output_dir) / "Languages" / CONFIG.default_language / CONFIG.def_injected_dir
        else:
            definjected_path = Path(output_dir) / "Languages" / CONFIG.default_language / CONFIG.def_injected_dir
        return self._analyze_directory(definjected_path, "*.xml")
    
    def _detect_output_keyed(self, output_dir: str, is_internal: bool = False) -> ResourceStatus:
        """检测输出 Keyed 目录"""
        if is_internal:
            keyed_path = Path(output_dir) / "Languages" / CONFIG.default_language / CONFIG.keyed_dir
        else:
            keyed_path = Path(output_dir) / "Languages" / CONFIG.default_language / CONFIG.keyed_dir
        return self._analyze_directory(keyed_path, "*.xml")
    
    def _analyze_directory(self, dir_path: Path, pattern: str = "*") -> ResourceStatus:
        """
        分析目录状态
        
        Args:
            dir_path (Path): 目录路径
            pattern (str): 文件匹配模式
            
        Returns:
            ResourceStatus: 目录状态信息
        """
        if not dir_path.exists():
            return ResourceStatus(exists=False)
        
        try:
            # 统计文件
            files = list(dir_path.rglob(pattern))
            file_count = len(files)
            
            # 计算总大小
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            # 获取最后修改时间
            if files:
                latest_file = max(files, key=lambda f: f.stat().st_mtime if f.is_file() else 0)
                import datetime
                last_modified = datetime.datetime.fromtimestamp(
                    latest_file.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M")
            else:
                last_modified = None
            
            return ResourceStatus(
                exists=True,
                path=str(dir_path),
                file_count=file_count,
                size_mb=size_mb,
                last_modified=last_modified
            )
            
        except Exception as e:
            self.logger.warning(f"分析目录失败 {dir_path}: {e}")
            return ResourceStatus(
                exists=True,
                path=str(dir_path),
                file_count=0,
                size_mb=0.0
            )

class EnvironmentDisplayer:
    """环境状态显示器"""
    
    @staticmethod
    def show_detection_progress():
        """显示检测进度"""
        print(f"\n{Fore.CYAN}🔍 正在检测模组和输出目录状态...{Style.RESET_ALL}")
        # 这里可以添加进度条，暂时用简单的文本提示
        print(f"{Fore.YELLOW}[████████████████████████████████] 100%{Style.RESET_ALL}")
    
    @staticmethod
    def display_environment_status(env_status: EnvironmentStatus) -> None:
        """
        显示环境状态摘要
        
        Args:
            env_status (EnvironmentStatus): 环境状态信息
        """
        print(f"\n{Fore.CYAN}📊 检测结果摘要：{Style.RESET_ALL}")
        print("┌─────────────────────────────────────────┐")
        print("│ 📂 模组翻译资源检测：                    │")
        
        # 显示英文 DefInjected 状态
        status_icon = "✅" if env_status.english_definjected.exists else "❌"
        status_text = "已找到" if env_status.english_definjected.exists else "未找到"
        print(f"│    英文 DefInjected 目录: {status_icon} {status_text}      │")
        
        if env_status.english_definjected.exists:
            path = env_status.english_definjected.path or ""
            # 截断过长的路径
            if len(path) > 35:
                path = "..." + path[-32:]
            print(f"│    └── 路径: {path:<25} │")
            print(f"│    └── 包含文件: {env_status.english_definjected.file_count:>3} 个翻译文件           │")
        
        # 显示英文 Keyed 状态
        status_icon = "✅" if env_status.english_keyed.exists else "❌"
        status_text = "已找到" if env_status.english_keyed.exists else "未找到"
        print(f"│                                         │")
        print(f"│    英文 Keyed 目录: {status_icon} {status_text}           │")
        
        if env_status.english_keyed.exists:
            path = env_status.english_keyed.path or ""
            if len(path) > 35:
                path = "..." + path[-32:]
            print(f"│    └── 路径: {path:<25} │")
            print(f"│    └── 包含文件: {env_status.english_keyed.file_count:>3} 个翻译文件            │")
        
        print("│                                         │")
        print("│ 📁 输出目录状态检测：                    │")
        
        # 显示输出 DefInjected 状态
        status_icon = "✅" if env_status.output_definjected.exists else "❌"
        status_text = "已存在" if env_status.output_definjected.exists else "不存在"
        print(f"│    输出 DefInjected 目录: {status_icon} {status_text}      │")
        
        if env_status.output_definjected.exists:
            print(f"│    └── 包含文件: {env_status.output_definjected.file_count:>3} 个翻译文件           │")
            if env_status.output_definjected.last_modified:
                print(f"│    └── 上次修改: {env_status.output_definjected.last_modified}         │")
        
        # 显示输出 Keyed 状态
        status_icon = "✅" if env_status.output_keyed.exists else "❌"
        status_text = "已存在" if env_status.output_keyed.exists else "不存在"
        print(f"│    输出 Keyed 目录: {status_icon} {status_text}           │")
        
        if env_status.output_keyed.exists:
            print(f"│    └── 包含文件: {env_status.output_keyed.file_count:>3} 个翻译文件            │")
            if env_status.output_keyed.last_modified:
                print(f"│    └── 上次修改: {env_status.output_keyed.last_modified}          │")
        
        print("└─────────────────────────────────────────┘")
        print()
