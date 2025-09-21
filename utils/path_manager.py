"""
路径管理模块 - 提供统一的路径管理功能，包括路径验证、记忆、历史记录等
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Callable, List, Set, Union, Any
from utils.logging_config import get_logger, log_error_with_context
from utils.ui_style import ui
from dataclasses import dataclass, field

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
        self.logger = get_logger(f"{__name__}.PathManager")
        self.user_config = get_user_config()
        self._history_file = os.path.join(
            os.path.dirname(__file__), ".day_translation_history.json"
        )
        self._path_pattern = re.compile(
            r"^[a-zA-Z]:[\\/]|^[\\/]{2}|^[a-zA-Z0-9_\-\.]+[\\/]"
        )
        self._history_cache: Dict[str, PathHistory] = {}
        self._load_history()
        # 注册路径验证器
        self._validators: Dict[str, Callable[[str], PathValidationResult]] = {
            "dir": self._validate_directory,
            "file": self._validate_file,
            "csv": self._validate_csv_file,
            "xml": self._validate_xml_file,
            "json": self._validate_json_file,
            "mod": self._validate_mod_directory,
            "language": self._validate_language_directory,
            "output_dir": self._validate_output_directory,
        }

    def _load_history(self) -> None:
        """加载历史记录"""
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, paths in data.items():
                        self._history_cache[key] = PathHistory(
                            paths=self._sanitize_history(paths),
                            last_used=paths[0] if paths else None,
                        )
        except Exception as e:
            self.logger.error("加载历史记录失败: %s", e)
            self._history_cache = {}

    def _save_history(self) -> None:
        """保存历史记录"""
        try:
            data = {
                key: history.paths
                for key, history in self._history_cache.items()
                if history.paths
            }
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error("保存历史记录失败: %s", e)

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
                    is_valid=False, error_message="无效的路径格式"
                )
            return PathValidationResult(is_valid=True, normalized_path=normalized)
        except Exception as e:
            return PathValidationResult(
                is_valid=False, error_message=f"路径规范化失败: {str(e)}"
            )

    def get_path(
        self,
        path_type: str,
        prompt: str,
        validator_type: str = "file",
        required: bool = True,
        default: Optional[str] = None,
    ) -> Optional[str]:
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
                    use_default = (
                        input(
                            f"{ui.Colors.WARNING}使用默认路径: {result.normalized_path} [y/n]: {ui.Colors.RESET}"
                        )
                        .strip()
                        .lower()
                    )
                    if use_default == "y":
                        return result.normalized_path

            # 获取历史记录
            history = self._history_cache.get(path_type, PathHistory())

            # 显示历史记录
            if history.paths:
                ui.print_info("\n历史记录：")
                for i, path in enumerate(history.paths, 1):
                    print(f"{i}. {path}")

            # 获取用户输入
            while True:
                choice = input(f"\n{ui.Colors.INFO}{prompt}{ui.Colors.RESET}").strip()

                if choice.lower() == "q":
                    return None

                if choice.isdigit() and 1 <= int(choice) <= len(history.paths):
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
                    history.paths = history.paths[: history.max_length]
                    history.last_used = result.normalized_path
                    self._save_history()

                    return result.normalized_path
                else:
                    ui.print_error(result.error_message)

        except Exception as e:
            self.logger.error("获取路径失败: %s", e)
            ui.print_error(f"获取路径时发生错误: {e}")
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
            history.paths = history.paths[: history.max_length]
            history.last_used = result.normalized_path
            self._save_history()

            return True
        except Exception as e:
            self.logger.error("记住路径失败: %s", e)
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
            self.logger.error("获取记忆路径失败: %s", e)
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
                    normalized_path=result.normalized_path,
                )
            if not os.access(result.normalized_path, os.R_OK | os.W_OK):
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"目录无法访问: {path}",
                    normalized_path=result.normalized_path,
                )
            return PathValidationResult(
                is_valid=True, normalized_path=result.normalized_path, path_type="dir"
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录验证失败: {str(e)}",
                normalized_path=result.normalized_path,
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
                        normalized_path=result.normalized_path,
                    )
            else:
                parent_dir = path_obj.parent or Path(".")
                if not parent_dir.is_dir() or not os.access(str(parent_dir), os.W_OK):
                    return PathValidationResult(
                        is_valid=False,
                        error_message=f"父目录不存在或无法写入: {path}",
                        normalized_path=result.normalized_path,
                    )
            return PathValidationResult(
                is_valid=True, normalized_path=result.normalized_path, path_type="file"
            )
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件验证失败: {str(e)}",
                normalized_path=result.normalized_path,
            )

    def _validate_csv_file(self, path: str) -> PathValidationResult:
        """验证CSV文件"""
        result = self._validate_file(path)
        if not result.is_valid:
            return result

        if not Path(result.normalized_path).suffix.lower() == ".csv":
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件必须是CSV格式: {path}",
                normalized_path=result.normalized_path,
            )
        return PathValidationResult(
            is_valid=True, normalized_path=result.normalized_path, path_type="csv"
        )

    def _validate_xml_file(self, path: str) -> PathValidationResult:
        """验证XML文件"""
        result = self._validate_file(path)
        if not result.is_valid:
            return result

        if not Path(result.normalized_path).suffix.lower() == ".xml":
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件必须是XML格式: {path}",
                normalized_path=result.normalized_path,
            )
        return PathValidationResult(
            is_valid=True, normalized_path=result.normalized_path, path_type="xml"
        )

    def _validate_json_file(self, path: str) -> PathValidationResult:
        """验证JSON文件"""
        result = self._validate_file(path)
        if not result.is_valid:
            return result

        if not Path(result.normalized_path).suffix.lower() == ".json":
            return PathValidationResult(
                is_valid=False,
                error_message=f"文件必须是JSON格式: {path}",
                normalized_path=result.normalized_path,
            )
        return PathValidationResult(
            is_valid=True, normalized_path=result.normalized_path, path_type="json"
        )

    def _validate_mod_directory(self, path: str) -> PathValidationResult:
        """只判断 About 文件夹是否存在，有则为有效模组目录，否则报错。"""
        result = self._validate_directory(path)
        if not result.is_valid:
            return result

        about_dir = os.path.join(result.normalized_path, "About")
        if os.path.isdir(about_dir):
            return PathValidationResult(
                is_valid=True, normalized_path=result.normalized_path, path_type="mod"
            )
        else:
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录不是有效的模组目录（缺少 About 文件夹）: {path}",
                normalized_path=result.normalized_path,
            )

    def detect_version_and_choose(self, mod_path: str) -> Optional[str]:
        """
        对已确定的模组路径进行版本检测和选择
        不显示历史记录，直接处理路径
        """
        # 验证路径
        result = self._validate_mod_directory(mod_path)

        if result.is_valid:
            # 检查是否为版本号结构
            structure_type, mod_dir, content_dir = self._detect_mod_structure_type(
                result.normalized_path
            )
            ui.print_info(f"🔍 检测模组结构: {structure_type} - {mod_dir}")
            if structure_type == "versioned":
                # 让用户选择版本号，直接返回最终目录
                final_dir = self._choose_versioned_content_dir(mod_dir)
                if final_dir:
                    return final_dir
                else:
                    return None
            else:
                return result.normalized_path
        else:
            ui.print_error(result.error_message)
            return None

    def _choose_versioned_content_dir(self, mod_dir: str) -> Optional[str]:
        """
        让用户选择版本号内容目录，直接返回最终目录
        """
        version_dirs = []
        try:
            for item in os.listdir(mod_dir):
                item_path = os.path.join(mod_dir, item)
                if os.path.isdir(item_path):
                    if self._is_version_number(item):
                        content_dirs = {"Defs", "Languages", "Textures", "Sounds"}
                        found_content_dirs = {
                            d
                            for d in os.listdir(item_path)
                            if os.path.isdir(os.path.join(item_path, d))
                        }
                        if content_dirs.intersection(found_content_dirs):
                            version_dirs.append(
                                {
                                    "name": item,
                                    "path": item_path,
                                    "version": self._parse_version_number(item),
                                }
                            )
        except Exception as e:
            self.logger.error("检测版本目录失败: %s", e)

        if version_dirs:
            version_dirs.sort(key=lambda x: x["version"], reverse=True)

            # 美化版本选择界面
            ui.print_section_header("📦 检测到版本号结构模组", ui.Icons.INFO)
            ui.print_info(f"📁 模组目录: {mod_dir}")
            ui.print_info(f"🔍 发现以下可用版本：")

            # 准备版本名称列表用于多行显示
            version_names = [
                f"{version_info['name']} (推荐)" if i == 0 else version_info["name"]
                for i, version_info in enumerate(version_dirs)
            ]

            # 计算自适应布局
            versions_per_line, item_width = self._calculate_version_layout(
                version_names
            )

            # 多行显示版本
            for i in range(0, len(version_dirs), versions_per_line):
                row_versions = version_dirs[i : i + versions_per_line]
                row_items = []
                for j, version_info in enumerate(row_versions):
                    global_index = i + j + 1
                    status_icon = "✅" if global_index == 1 else "📋"
                    status_text = " (推荐)" if global_index == 1 else ""
                    item_text = f"{global_index}. {status_icon} {version_info['name']}{status_text}"
                    row_items.append(item_text.ljust(item_width))
                print("   " + "".join(row_items))

            ui.print_info(f"\n💡 快速选择：")
            ui.print_info(f"   0 - 使用默认选择（{version_dirs[0]['name']}）")
            ui.print_info(f"   q - 退出版本选择")
            while True:
                choice = input(
                    f"\n{ui.Colors.INFO}🎯 请选择版本 (1-{len(version_dirs)}，回车默认0，q退出): {ui.Colors.RESET}"
                ).strip()
                if not choice:
                    choice = "0"
                if choice.lower() == "q":
                    ui.print_warning("👋 已退出版本选择")
                    return None
                elif choice == "0":
                    selected_version = version_dirs[0]
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(version_dirs):
                    selected_version = version_dirs[int(choice) - 1]
                    break
                else:
                    ui.print_error(f"❌ 无效选择，请输入 1-{len(version_dirs)}、0 或 q")
                    ui.print_warning("💡 提示：直接回车选择推荐版本，输入 q 退出")
            ui.print_success("✅ 版本选择成功")
            ui.print_info(f"📦 选择版本: {selected_version['name']}")
            ui.print_info(f"📁 内容目录: {selected_version['path']}")
            return selected_version["path"]
        else:
            ui.print_warning("⚠️ 未检测到版本号结构")
            ui.print_info("💡 该模组可能使用标准结构，将使用根目录内容")
            return None

    def _validate_language_directory(self, path: str) -> PathValidationResult:
        """验证语言目录"""
        result = self._validate_directory(path)
        if not result.is_valid:
            return result

        # 检查语言目录结构
        required_dirs = {CONFIG.def_injected_dir, CONFIG.keyed_dir}
        found_dirs = {
            d.name for d in Path(result.normalized_path).iterdir() if d.is_dir()
        }

        if not required_dirs.intersection(found_dirs):
            return PathValidationResult(
                is_valid=False,
                error_message=f"目录不是有效的语言目录: {path}",
                normalized_path=result.normalized_path,
            )
        return PathValidationResult(
            is_valid=True, normalized_path=result.normalized_path, path_type="language"
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
                    normalized_path=str(path_obj.resolve()),
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
                    normalized_path=str(path_obj.resolve()),
                )

            return PathValidationResult(
                is_valid=True,
                normalized_path=str(path_obj.resolve()),
                path_type="output_dir",
            )

        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                error_message=f"验证输出目录失败: {str(e)}",
                normalized_path=str(Path(path).resolve()) if path else "",
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
            self.logger.error("创建目录失败: %s", e)
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

            return os.path.relpath(
                path_result.normalized_path, base_result.normalized_path
            )
        except Exception as e:
            self.logger.error("获取相对路径失败: %s", e)
            return None

    def get_path_with_smart_recommendations(
        self,
        path_type: str,
        prompt: str,
        validator_type: str = "file",
        required: bool = True,
        default: Optional[str] = None,
        smart_recommendations: Optional[List[str]] = None,
        recommendation_reasons: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        获取路径输入，支持智能推荐（基于现有 get_path 的增强版本）

        Args:
            path_type (str): 路径类型
            prompt (str): 提示文本
            validator_type (str): 验证器类型
            required (bool): 是否必需
            default (Optional[str]): 默认路径
            smart_recommendations (Optional[List[str]]): 智能推荐路径列表
            recommendation_reasons (Optional[Dict[str, str]]): 推荐原因说明

        Returns:
            Optional[str]: 验证后的路径
        """
        try:
            # 如果有智能推荐，优先显示
            if smart_recommendations:
                ui.print_info(f"\n💡 智能推荐：")
                for i, rec_path in enumerate(smart_recommendations, 1):
                    reason = (
                        recommendation_reasons.get(rec_path, "")
                        if recommendation_reasons
                        else ""
                    )
                    reason_text = f" ({reason})" if reason else ""
                    print(f"{i}. {rec_path}{reason_text}")

                ui.print_info(f"0. 手动输入其他路径")

                choice = input(
                    f"\n{ui.Colors.INFO}选择推荐项 (1-{len(smart_recommendations)}) 或 0 手动输入：{ui.Colors.RESET}"
                ).strip()

                if choice.isdigit() and 1 <= int(choice) <= len(smart_recommendations):
                    selected_path = smart_recommendations[int(choice) - 1]
                    # 验证选择的推荐路径
                    validator = self._validators.get(
                        validator_type, self._validate_file
                    )
                    result = validator(selected_path)
                    if result.is_valid:
                        # 更新历史记录（复用现有逻辑）
                        if path_type not in self._history_cache:
                            self._history_cache[path_type] = PathHistory()
                        history = self._history_cache[path_type]
                        if result.normalized_path in history.paths:
                            history.paths.remove(result.normalized_path)
                        history.paths.insert(0, result.normalized_path)
                        history.paths = history.paths[: history.max_length]
                        history.last_used = result.normalized_path
                        self._save_history()

                        return result.normalized_path
                    else:
                        ui.print_error(f"❌ 推荐路径无效: {result.error_message}")
                        # 继续到常规输入流程
                elif choice == "0":
                    # 用户选择手动输入，继续到常规流程
                    pass
                else:
                    ui.print_error("❌ 无效选择，使用常规输入方式")

            # 调用现有的 get_path 方法处理常规流程
            return self.get_path(path_type, prompt, validator_type, required, default)

        except Exception as e:
            self.logger.error("智能推荐路径输入失败: %s", e)
            # 降级到常规方法
            return self.get_path(path_type, prompt, validator_type, required, default)

    def _detect_mod_structure_type(self, mod_dir: str) -> tuple[str, str, str]:
        """
        检测模组目录结构类型

        Args:
            mod_dir (str): 模组目录路径

        Returns:
            tuple[str, str, str]: (结构类型, 模组目录, 内容目录)
                结构类型: 'standard' | 'versioned' | 'unknown'
                模组目录: 包含About的目录
                内容目录: 包含Defs/Languages的目录
        """
        # 检查根目录是否有About
        about_dir = os.path.join(mod_dir, "About")
        if os.path.isdir(about_dir):
            # 首先检查是否有版本号子目录
            version_result = self._find_version_content_dir(mod_dir)
            if version_result[0] == "versioned":
                # 如果找到版本号结构，优先使用版本号结构
                return version_result

            # 检查根目录是否有模组内容
            content_dirs = {"Defs", "Languages", "Textures", "Sounds"}
            found_content_dirs = {
                d
                for d in os.listdir(mod_dir)
                if os.path.isdir(os.path.join(mod_dir, d))
            }

            if content_dirs.intersection(found_content_dirs):
                # 标准结构：根目录既有About又有内容
                return "standard", mod_dir, mod_dir
            else:
                # 根目录有About但没有内容
                return "unknown", mod_dir, mod_dir

        return "unknown", mod_dir, mod_dir

    def _find_version_content_dir(self, mod_dir: str) -> tuple[str, str, str]:
        """
        在版本号子目录中查找内容目录

        Args:
            mod_dir (str): 模组根目录路径

        Returns:
            tuple[str, str, str]: (结构类型, 模组目录, 内容目录)
        """
        version_dirs = []
        try:
            for item in os.listdir(mod_dir):
                item_path = os.path.join(mod_dir, item)
                if os.path.isdir(item_path):
                    # 检查是否为版本号格式（如 1.5, 1.4, 1.3 等）
                    if self._is_version_number(item):
                        # 检查该版本目录下是否有模组内容
                        content_dirs = {"Defs", "Languages", "Textures", "Sounds"}
                        found_content_dirs = {
                            d
                            for d in os.listdir(item_path)
                            if os.path.isdir(os.path.join(item_path, d))
                        }

                        if content_dirs.intersection(found_content_dirs):
                            version_dirs.append(
                                {
                                    "name": item,
                                    "path": item_path,
                                    "version": self._parse_version_number(item),
                                }
                            )
        except Exception as e:
            self.logger.error("检测版本目录失败: %s", e)

        if version_dirs:
            # 按版本号排序，选择最新版本
            version_dirs.sort(key=lambda x: x["version"], reverse=True)
            latest_version = version_dirs[0]
            return "versioned", mod_dir, latest_version["path"]

        # 没有找到版本号内容目录
        return "unknown", mod_dir, mod_dir

    def _calculate_version_layout(self, version_names: List[str]) -> tuple:
        """计算版本选择的自适应布局参数"""
        try:
            import shutil

            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80  # 默认宽度

        # 预留边框和边距空间
        available_width = terminal_width - 10  # 边框 + 边距

        # 计算每个版本名需要的最大宽度
        max_name_length = (
            max(len(name) for name in version_names) if version_names else 10
        )
        # 编号宽度 (如 "6.") + 图标 + 版本名 + 间距
        item_width = (
            len(str(len(version_names))) + 1 + 2 + max_name_length + 3
        )  # 2 for emoji

        # 计算每行能放多少个版本
        versions_per_line = max(1, available_width // item_width)

        # 限制最大列数，避免过于拥挤
        versions_per_line = min(versions_per_line, 4)

        return versions_per_line, item_width

    def _is_version_number(self, name: str) -> bool:
        """
        判断字符串是否为版本号格式

        Args:
            name (str): 目录名

        Returns:
            bool: 是否为版本号格式
        """
        # 匹配版本号格式：1.5, 1.4, 1.3, 1.5.0, v1.5 等
        import re

        pattern = r"^v?(\d+\.)+\d+$"
        return bool(re.match(pattern, name))

    def _parse_version_number(self, version_str: str) -> tuple:
        """
        解析版本号字符串为可比较的元组

        Args:
            version_str (str): 版本号字符串

        Returns:
            tuple: 版本号元组
        """
        try:
            # 去掉可能的 'v' 前缀
            clean_version = version_str.strip().lower()
            if clean_version.startswith("v"):
                clean_version = clean_version[1:]

            # 分割版本号并转换为整数
            parts = []
            for part in clean_version.split("."):
                parts.append(int(part))

            return tuple(parts)
        except Exception:
            # 如果解析失败，返回 (0,) 表示最低版本
            return (0,)

    def get_history_list(self, path_type: str) -> List[str]:
        """
        获取指定类型的历史记录列表

        Args:
            path_type (str): 路径类型

        Returns:
            List[str]: 历史记录列表
        """
        try:
            if path_type not in self._history_cache:
                return []
            history = self._history_cache[path_type]
            return history.paths[:]  # 返回副本
        except Exception as e:
            self.logger.error("获取历史记录失败: %s", e)
            return []
