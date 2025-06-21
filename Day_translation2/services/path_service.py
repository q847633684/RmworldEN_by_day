"""
Day Translation 2 - 路径验证服务

负责路径验证、文件检查等与文件系统相关的业务逻辑。
将路径相关业务逻辑从配置层分离出来。
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

from colorama import Fore, Style

from models.exceptions import ValidationError
from config.data_models import PathValidationResult, UnifiedConfig


class PathValidationService:
    """路径验证服务 - 专门处理路径验证相关的业务逻辑"""

    def __init__(self):
        """初始化路径验证服务"""
        self.logger = logging.getLogger(__name__)

    def validate_path(self, path: str, validator_type: str) -> PathValidationResult:
        """
        验证路径有效性

        Args:
            path: 要验证的路径
            validator_type: 验证器类型 (dir, file, csv, json, mod, etc.)

        Returns:
            路径验证结果
        """
        try:
            if not path or not path.strip():
                return PathValidationResult(
                    is_valid=False, error_message="路径不能为空", suggestion="请输入有效的路径"
                )

            path = path.strip()

            # 规范化路径
            normalized_path = os.path.normpath(path)

            # 根据验证器类型进行不同的验证
            if validator_type == "dir":
                return self._validate_directory(normalized_path)
            elif validator_type == "dir_create":
                return self._validate_directory_create(normalized_path)
            elif validator_type == "file":
                return self._validate_file(normalized_path)
            elif validator_type == "csv":
                return self._validate_csv_file(normalized_path)
            elif validator_type == "json":
                return self._validate_json_file(normalized_path)
            elif validator_type == "mod":
                return self._validate_mod_directory(normalized_path)
            else:
                return PathValidationResult(
                    is_valid=False,
                    error_message=f"未知的验证器类型: {validator_type}",
                    suggestion="请检查验证器类型配置",
                )

        except Exception as e:
            self.logger.error(f"路径验证过程出错: {e}")
            return PathValidationResult(
                is_valid=False,
                error_message=f"路径验证失败: {e}",
                suggestion="请检查路径格式和权限",
            )

    def _validate_directory(self, path: str) -> PathValidationResult:
        """验证目录"""
        if not os.path.exists(path):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="目录不存在",
                suggestion="请检查目录路径是否正确",
            )

        if not os.path.isdir(path):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="路径不是目录",
                suggestion="请选择一个有效的目录",
            )

        if not os.access(path, os.R_OK):
            return PathValidationResult(
                is_valid=False, path=path, error_message="目录无法访问", suggestion="请检查目录权限"
            )

        return PathValidationResult(is_valid=True, path=path)

    def _validate_directory_create(self, path: str) -> PathValidationResult:
        """验证目录（允许创建不存在的目录）"""
        if os.path.exists(path):
            return self._validate_directory(path)

        # 检查父目录是否存在且可写
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="父目录不存在",
                suggestion=f"请确保父目录存在: {parent_dir}",
            )

        if parent_dir and not os.access(parent_dir, os.W_OK):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="父目录无写入权限",
                suggestion="请检查父目录权限",
            )

        return PathValidationResult(is_valid=True, path=path)

    def _validate_file(self, path: str) -> PathValidationResult:
        """验证文件"""
        if not os.path.exists(path):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="文件不存在",
                suggestion="请检查文件路径是否正确",
            )

        if not os.path.isfile(path):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="路径不是文件",
                suggestion="请选择一个有效的文件",
            )

        if not os.access(path, os.R_OK):
            return PathValidationResult(
                is_valid=False, path=path, error_message="文件无法读取", suggestion="请检查文件权限"
            )

        return PathValidationResult(is_valid=True, path=path)

    def _validate_csv_file(self, path: str) -> PathValidationResult:
        """验证CSV文件"""  # 先进行基本文件验证
        basic_result = self._validate_file(path)
        if not basic_result.is_valid:
            # 如果文件不存在，但路径有效，可能是要创建新文件
            error_msg = basic_result.error_message or ""
            if "不存在" in error_msg:
                if path.lower().endswith(".csv"):
                    parent_dir = os.path.dirname(path)
                    if os.path.exists(parent_dir) and os.access(parent_dir, os.W_OK):
                        return PathValidationResult(is_valid=True, path=path)
            return basic_result

        # 检查文件扩展名
        if not path.lower().endswith(".csv"):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="文件不是CSV格式",
                suggestion="请选择CSV文件（.csv扩展名）",
            )

        return PathValidationResult(is_valid=True, path=path)

    def _validate_json_file(self, path: str) -> PathValidationResult:
        """验证JSON文件"""  # 先进行基本文件验证
        basic_result = self._validate_file(path)
        if not basic_result.is_valid:
            # 如果文件不存在，但路径有效，可能是要创建新文件
            error_msg = basic_result.error_message or ""
            if "不存在" in error_msg:
                if path.lower().endswith(".json"):
                    parent_dir = os.path.dirname(path)
                    if os.path.exists(parent_dir) and os.access(parent_dir, os.W_OK):
                        return PathValidationResult(is_valid=True, path=path)
            return basic_result

        # 检查文件扩展名
        if not path.lower().endswith(".json"):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="文件不是JSON格式",
                suggestion="请选择JSON文件（.json扩展名）",
            )

        return PathValidationResult(is_valid=True, path=path)

    def _validate_mod_directory(self, path: str) -> PathValidationResult:
        """验证模组目录"""
        # 先进行基本目录验证
        basic_result = self._validate_directory(path)
        if not basic_result.is_valid:
            return basic_result

        # 检查模组目录结构
        about_xml = os.path.join(path, "About", "About.xml")
        if not os.path.exists(about_xml):
            return PathValidationResult(
                is_valid=False,
                path=path,
                error_message="不是有效的模组目录",
                suggestion="模组目录应包含 About/About.xml 文件",
            )

        return PathValidationResult(is_valid=True, path=path)

    def get_path_with_validation(
        self,
        path_type: str,
        prompt: str,
        validator_type: str,
        config: UnifiedConfig,
        required: bool = True,
        default: Optional[str] = None,
        show_history: bool = True,
    ) -> Optional[str]:
        """
        获取并验证路径

        Args:
            path_type: 路径类型（用于历史记录）
            prompt: 用户提示信息
            validator_type: 验证器类型
            config: 配置实例
            required: 是否必须
            default: 默认值
            show_history: 是否显示历史记录

        Returns:
            验证通过的路径，或None
        """
        try:
            # 显示历史记录
            if show_history:
                self._show_path_history(path_type, config)

            # 构建提示信息
            full_prompt = prompt
            if default:
                full_prompt += f"（默认: {default}）"
            full_prompt += ": "

            while True:
                user_input = input(f"{Fore.CYAN}{full_prompt}{Style.RESET_ALL}").strip()

                # 处理空输入
                if not user_input:
                    if default:
                        user_input = default
                    elif not required:
                        return None
                    else:
                        print(f"{Fore.RED}❌ 路径不能为空{Style.RESET_ALL}")
                        continue

                # 验证路径
                result = self.validate_path(user_input, validator_type)

                if result.is_valid:
                    print(f"{Fore.GREEN}✅ 路径验证通过{Style.RESET_ALL}")
                    return result.path
                else:
                    print(f"{Fore.RED}❌ {result.error_message}{Style.RESET_ALL}")
                    if result.suggestion:
                        print(f"{Fore.YELLOW}💡 {result.suggestion}{Style.RESET_ALL}")

                    # 询问是否重新输入
                    retry = input(f"{Fore.CYAN}是否重新输入？[Y/n]: {Style.RESET_ALL}").lower()
                    if retry in ["n", "no"]:
                        return None

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}用户取消操作{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.logger.error(f"获取路径时出错: {e}")
            print(f"{Fore.RED}❌ 获取路径失败: {e}{Style.RESET_ALL}")
            return None

    def _show_path_history(self, path_type: str, config: UnifiedConfig) -> None:
        """显示路径历史记录"""
        try:
            history_data = config.user.path_history.get(path_type, {})

            if isinstance(history_data, dict) and "paths" in history_data:
                paths = history_data["paths"]
                if isinstance(paths, list) and paths:
                    print(f"\n{Fore.BLUE}📂 最近使用的路径：{Style.RESET_ALL}")
                    for i, path in enumerate(paths[-5:], 1):  # 显示最近5个
                        print(f"  {i}. {path}")
                    print()

        except Exception as e:
            self.logger.debug(f"显示路径历史记录时出错: {e}")

    def check_file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(path) and os.path.isfile(path)

    def check_directory_exists(self, path: str) -> bool:
        """检查目录是否存在"""
        return os.path.exists(path) and os.path.isdir(path)

    def get_file_size(self, path: str) -> Optional[int]:
        """获取文件大小"""
        try:
            if self.check_file_exists(path):
                return os.path.getsize(path)
        except Exception as e:
            self.logger.error(f"获取文件大小失败: {e}")
        return None

    def get_directory_file_count(self, path: str, extension: Optional[str] = None) -> int:
        """获取目录中文件数量"""
        try:
            if not self.check_directory_exists(path):
                return 0

            count = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    if extension is None or file.lower().endswith(extension.lower()):
                        count += 1
            return count
        except Exception as e:
            self.logger.error(f"获取目录文件数量失败: {e}")
            return 0


# 单例实例
path_validation_service = PathValidationService()
