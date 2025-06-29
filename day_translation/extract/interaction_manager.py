"""
智能交互管理器 - 实现用户设计的四步智能流程
负责协调用户交互决策，复用现有功能完成实际工作
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from colorama import Fore, Style

from day_translation.utils.path_manager import PathManager
from day_translation.utils.config import get_config

CONFIG = get_config()

class InteractionManager:
    """
    智能交互管理器 - 实现用户设计的四步智能流程
    1. 检测英文目录状态（DefInjected/Keyed）
    2. 检测输出目录状态（DefInjected/Keyed）
    3. 选择数据来源（DefInjected提取 vs Defs扫描）
    4. 处理输出冲突（合并/覆盖/重建）
    """

    def __init__(self):
        """初始化交互管理器"""
        self.path_manager = PathManager()
        self.logger = logging.getLogger(__name__)

    def _print_separator(self, title: str = "", char: str = "=", length: int = 60):
        """
        打印分隔线
        
        Args:
            title (str): 分隔线标题
            char (str): 分隔线字符
            length (int): 分隔线长度
        """
        if title:
            padding = (length - len(title) - 2) // 2
            print(f"\n{Fore.CYAN}{char * padding} {title} {char * padding}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.CYAN}{char * length}{Style.RESET_ALL}")

    def _print_step_header(self, step_num: int, total_steps: int, title: str):
        """
        打印步骤标题
        
        Args:
            step_num (int): 当前步骤号
            total_steps (int): 总步骤数
            title (str): 步骤标题
        """
        print(f"\n{Fore.YELLOW}【步骤 {step_num}/{total_steps}】{title}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'─' * 50}{Style.RESET_ALL}")

    def handle_smart_extraction_workflow(self, mod_dir: str) -> Dict[str, Any]:
        """
        执行用户设计的四步智能流程

        Args:
            mod_dir (str): 模组目录路径（已经是最终目录）

        Returns:
            Dict[str, Any]: 智能流程决策结果
        """
        self._print_separator("智能提取翻译模板工作流", "=", 60)
        
        # 第一步：检测英文目录状态
        self._print_step_header(1, 5, "检测英文目录状态")
        english_status = self._detect_english_directories(mod_dir)
        
        # 第二步：检测输出目录状态
        self._print_step_header(2, 5, "检测输出目录状态")
        output_dir = self._get_output_directory(mod_dir)
        output_status = self._detect_output_directories(output_dir)
        
        # 第三步：选择数据来源
        self._print_step_header(3, 5, "选择数据来源")
        data_source_choice = self._choose_data_source(english_status)
        
        # 第四步：处理输出冲突
        self._print_step_header(4, 5, "处理输出冲突")
        conflict_resolution = self._handle_output_conflicts(output_status)
        
        # 第五步：自动选择模板结构
        self._print_step_header(5, 5, "选择模板结构")
        template_structure = self._choose_template_structure(data_source_choice, english_status)
        
        # 构建智能配置
        smart_config = {
            'data_sources': {
                'choice': data_source_choice,
                'english_status': english_status
            },
            'output_config': {
                'conflict_resolution': conflict_resolution,
                'output_dir': output_dir
            },
            'organization': 'group_by_type',  # 默认按类型分组
            'template_structure': template_structure
        }
        
        self._print_separator("✅ 智能流程决策完成", "=", 60)
        return smart_config

    def _detect_english_directories(self, mod_dir: str) -> Dict[str, bool]:
        """
        检测英文目录状态

        Args:
            mod_dir (str): 模组目录路径

        Returns:
            Dict[str, bool]: 英文目录状态
        """
        print(f"{Fore.BLUE}🔍 正在检测英文目录状态...{Style.RESET_ALL}")
        
        # 检测英文 DefInjected 目录
        en_definjected_dir = Path(mod_dir) / "Languages" / "English" / "DefInjected"
        has_english_definjected = en_definjected_dir.exists() and any(en_definjected_dir.iterdir())
        
        # 检测英文 Keyed 目录
        en_keyed_dir = Path(mod_dir) / "Languages" / "English" / "Keyed"
        has_english_keyed = en_keyed_dir.exists() and any(en_keyed_dir.iterdir())
        
        print(f"   {Fore.CYAN}检测英文的DefInjected目录: {Fore.GREEN if has_english_definjected else Fore.RED}{'✅ 有' if has_english_definjected else '❌ 否'}{Style.RESET_ALL}")
        print(f"   {Fore.CYAN}检测英文的Keyed目录: {Fore.GREEN if has_english_keyed else Fore.RED}{'✅ 有' if has_english_keyed else '❌ 否'}{Style.RESET_ALL}")
        
        return {
            'has_definjected': has_english_definjected,
            'has_keyed': has_english_keyed,
            'definjected_path': str(en_definjected_dir) if has_english_definjected else None,
            'keyed_path': str(en_keyed_dir) if has_english_keyed else None
        }

    def _get_output_directory(self, mod_dir: str) -> str:
        """
        获取用户指定的输出目录

        Args:
            mod_dir (str): 模组目录路径（已经是最终目录）
        Returns:
            str: 输出目录路径
        """
        path_manager = PathManager()
        default_dir = str(Path(mod_dir) / 'Languages' / 'ChineseSimplified')
        history = path_manager.get_history_list("output_dir")
        
        print(f"{Fore.BLUE}📁 请选择输出目录：{Style.RESET_ALL}")
        print(f"{Fore.GREEN}1. 使用默认目录：{default_dir}{Style.RESET_ALL}")
        
        # 展示所有历史记录
        if history:
            print(f"{Fore.YELLOW}历史记录：{Style.RESET_ALL}")
            for i, hist_path in enumerate(history, 2):
                print(f"   {i}. {hist_path}")
        else:
            print(f"{Fore.YELLOW}暂无历史记录{Style.RESET_ALL}")
        
        max_choice = len(history) + 1
        
        while True:
            choice = input(f"\n{Fore.CYAN}请选择 (1-{max_choice}) 或直接输入路径: {Style.RESET_ALL}").strip()
            
            if choice == '1':
                print(f"   {Fore.GREEN}✅ 选择：{default_dir}{Style.RESET_ALL}")
                path_manager.remember_path("output_dir", default_dir)
                return default_dir
            elif choice.isdigit() and 2 <= int(choice) <= max_choice:
                selected_path = history[int(choice) - 2]
                print(f"   {Fore.GREEN}✅ 选择：{selected_path}{Style.RESET_ALL}")
                path_manager.remember_path("output_dir", selected_path)
                return selected_path
            elif choice:  # 非空输入，当作路径使用
                # 验证路径
                if os.path.isdir(choice) or not os.path.exists(choice):
                    print(f"   {Fore.GREEN}✅ 选择：{choice}{Style.RESET_ALL}")
                    path_manager.remember_path("output_dir", choice)
                    return choice
                else:
                    print(f"   {Fore.RED}❌ 路径无效：{choice}{Style.RESET_ALL}")
                    continue
            else:
                print(f"   {Fore.RED}❌ 请输入选择或路径{Style.RESET_ALL}")

    def _detect_output_directories(self, output_dir: str) -> Dict[str, bool]:
        """
        检测输出目录状态

        Args:
            output_dir (str): 输出目录路径

        Returns:
            Dict[str, bool]: 输出目录状态
        """
        output_path = Path(output_dir)
        print(f"{Fore.BLUE}🔍 正在检测输出目录：{output_dir}{Style.RESET_ALL}")
        #   检测输出 DefInjected 目录
        output_definjected_dir = output_path / "DefInjected"
        output_keyed_dir = output_path / "Keyed"      
        has_output_definjected = output_definjected_dir.exists() and any(output_definjected_dir.iterdir())
        has_output_keyed = output_keyed_dir.exists() and any(output_keyed_dir.iterdir())
        
        print(f"   {Fore.CYAN}检测DefInjected目录：{Fore.GREEN if has_output_definjected else Fore.RED}{'✅ 有' if has_output_definjected else '❌ 否'}{Style.RESET_ALL}")
        print(f"   {Fore.CYAN}检测Keyed目录：{Fore.GREEN if has_output_keyed else Fore.RED}{'✅ 有' if has_output_keyed else '❌ 否'}{Style.RESET_ALL}")
        
        return {
            'has_definjected': has_output_definjected,
            'has_keyed': has_output_keyed,
            'definjected_path': str(output_definjected_dir) if has_output_definjected else None,
            'keyed_path': str(output_keyed_dir) if has_output_keyed else None
        }

    def _choose_data_source(self, english_status: Dict[str, bool]) -> str:
        """
        选择数据来源

        Args:
            english_status (Dict[str, bool]): 英文目录状态

        Returns:
            str: 数据来源选择
        """
        has_definjected = english_status['has_definjected']
        
        if has_definjected:
            print(f"{Fore.BLUE}检测DefInjected目录：{Fore.GREEN}✅ 有{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}请选择数据来源：{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}1. 使用DefInjected目录提取翻译（推荐，更快）{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}2. 扫描Defs文件重新提取（完整扫描）{Style.RESET_ALL}")
            
            while True:
                choice = input(f"\n{Fore.CYAN}请选择 (1/2): {Style.RESET_ALL}").strip()
                if choice == '1':
                    print(f"   {Fore.GREEN}✅ 选择：使用DefInjected目录提取翻译{Style.RESET_ALL}")
                    return 'definjected_only'
                elif choice == '2':
                    print(f"   {Fore.GREEN}✅ 选择：扫描Defs文件重新提取{Style.RESET_ALL}")
                    return 'defs_only'
                else:
                    print(f"   {Fore.RED}❌ 请输入 1 或 2{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}检测DefInjected目录：{Fore.RED}❌ 没有{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✅ 自动选择：扫描Defs文件重新提取{Style.RESET_ALL}")
            return 'defs_only'

    def _handle_output_conflicts(self, output_status: Dict[str, bool]) -> str:
        """
        处理输出冲突

        Args:
            output_status (Dict[str, bool]): 输出目录状态

        Returns:
            str: 冲突处理方式
        """
        has_output_files = output_status['has_definjected'] or output_status['has_keyed']
        
        if has_output_files:
            print(f"{Fore.YELLOW}⚠️  检测到输出目录中已有翻译文件，请选择处理方式：{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}1. 合并 - 保留现有翻译文件，仅添加新内容{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}2. 覆盖 - 删除并重新生成本次要导出的翻译文件{Style.RESET_ALL}")
            print(f"   {Fore.RED}3. 重建 - 清空整个输出目录，所有内容全部重建{Style.RESET_ALL}")
            
            while True:
                choice = input(f"\n{Fore.CYAN}请选择 (1/2/3): {Style.RESET_ALL}").strip()
                if choice == '1':
                    print(f"   {Fore.GREEN}✅ 选择：合并{Style.RESET_ALL}")
                    return 'merge'
                elif choice == '2':
                    print(f"   {Fore.YELLOW}✅ 选择：覆盖{Style.RESET_ALL}")
                    return 'overwrite'
                elif choice == '3':
                    print(f"   {Fore.RED}✅ 选择：重建{Style.RESET_ALL}")
                    return 'rebuild'
                else:
                    print(f"   {Fore.RED}❌ 请输入 1、2 或 3{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}输出目录中没有现有翻译文件{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✅ 自动选择：新建{Style.RESET_ALL}")
            return 'new'

    def get_english_keyed_directory(self, mod_dir: str) -> Optional[str]:
        """
        获取英文 Keyed 目录路径

        Args:
            mod_dir (str): 模组目录路径

        Returns:
            Optional[str]: Keyed 目录路径，如果不存在则返回 None
        """
        en_keyed_dir = Path(mod_dir) / "Languages" / "English" / "Keyed"
        if en_keyed_dir.exists() and any(en_keyed_dir.iterdir()):
            return str(en_keyed_dir)
        return None

    def _choose_template_structure(self, data_source_choice: str, english_status: Dict[str, bool]) -> str:
        """
        根据数据来源自动选择模板结构
        
        Args:
            data_source_choice (str): 数据来源选择
            english_status (Dict[str, bool]): 英文目录状态
            
        Returns:
            str: 模板结构选择
        """
        if data_source_choice == 'definjected_only':
            # 使用DefInjected目录提取 → 保持原结构
            print(f"{Fore.BLUE}检测到使用DefInjected目录提取翻译{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✅ 自动选择：保持原英文DefInjected结构{Style.RESET_ALL}")
            return 'original_structure'
        else:
            # 扫描Defs文件 → 按Defs结构
            print(f"{Fore.BLUE}检测到使用Defs文件扫描提取翻译{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}✅ 自动选择：按原Defs目录结构生成{Style.RESET_ALL}")
            return 'defs_structure' 