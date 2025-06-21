"""
用户交互服务模块

提供用户交互相关的服务，包括：
- 路径输入和验证
- 历史记录展示
- 用户选择处理

Author: Day汉化项目
Created: 2024-12-19
"""

from typing import Optional, List
import logging
from colorama import Fore, Style

from config.data_models import UnifiedConfig
from services.path_service import path_validation_service
from services.history_service import history_service

logger = logging.getLogger(__name__)


class UserInteractionService:
    """用户交互服务

    处理用户输入、路径验证、历史记录展示等交互逻辑
    """

    def get_path_with_validation(
        self,
        config: UnifiedConfig,
        path_type: str,
        prompt: str,
        validator_type: str,
        required: bool = True,
        default: Optional[str] = None,
        show_history: bool = True,
    ) -> Optional[str]:
        """获取并验证路径输入

        Args:
            config: 统一配置对象
            path_type: 路径类型标识
            prompt: 输入提示
            validator_type: 验证器类型
            required: 是否必需
            default: 默认值
            show_history: 是否显示历史记录

        Returns:
            验证通过的路径或None
        """
        try:
            # 显示历史记录
            if show_history:
                self._show_path_history(config, path_type)
            # 获取用户输入
            while True:
                user_input = input(f"{prompt}: ").strip()

                # 处理空输入
                if not user_input:
                    if default:
                        user_input = default
                    elif not required:
                        return None
                    else:
                        print(f"{Fore.RED}此项为必填项{Style.RESET_ALL}")
                        continue

                # 验证路径
                validation_result = path_validation_service.validate_path(
                    user_input, validator_type
                )

                if validation_result.is_valid:
                    validated_path = validation_result.normalized_path or user_input

                    # 记住路径（如果启用）
                    if config.user.general.remember_paths:
                        history_service.remember_path(path_type, validated_path, config)
                        history_service.add_to_history(path_type, validated_path, config)

                    return validated_path
                else:
                    print(f"{Fore.RED}❌ {validation_result.error_message}{Style.RESET_ALL}")

        except Exception as e:
            logger.error(f"获取路径输入失败: {path_type}, 错误: {e}")
            raise

    def _show_path_history(self, config: UnifiedConfig, path_type: str) -> None:
        """显示路径历史记录

        Args:
            config: 统一配置对象
            path_type: 路径类型
        """
        try:
            recent_paths = history_service.get_history(path_type, config)

            if recent_paths:
                print(f"\n{Fore.YELLOW}最近使用的路径：{Style.RESET_ALL}")
                # 显示最近5个路径
                for i, path in enumerate(recent_paths[:5], 1):
                    print(f"  {i}. {path}")

        except Exception as e:
            logger.warning(f"显示历史记录失败: {path_type}, 错误: {e}")

    def get_choice_from_list(
        self,
        prompt: str,
        choices: List[str],
        default_index: Optional[int] = None,
    ) -> Optional[str]:
        """从列表中获取用户选择

        Args:
            prompt: 输入提示
            choices: 选择列表
            default_index: 默认选择索引（0-based）

        Returns:
            用户选择的项，如果用户取消则返回None
        """
        try:
            if not choices:
                return None

            # 显示选择列表
            print(f"\n{prompt}")
            for i, choice in enumerate(choices, 1):
                marker = " (默认)" if default_index is not None and i - 1 == default_index else ""
                print(f"  {i}. {choice}{marker}")

            # 获取用户输入
            while True:
                user_input = input("请选择 [数字]: ").strip()

                # 处理空输入
                if not user_input:
                    if default_index is not None:
                        return choices[default_index]
                    else:
                        print(f"{Fore.RED}请输入选择{Style.RESET_ALL}")
                        continue

                # 验证数字输入
                try:
                    choice_num = int(user_input)
                    if 1 <= choice_num <= len(choices):
                        return choices[choice_num - 1]
                    else:
                        print(f"{Fore.RED}请输入 1-{len(choices)} 之间的数字{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}请输入有效的数字{Style.RESET_ALL}")

        except Exception as e:
            logger.error(f"获取用户选择失败: {e}")
            raise

    def get_yes_no_choice(
        self,
        prompt: str,
        default: Optional[bool] = None,
    ) -> bool:
        """获取是/否选择

        Args:
            prompt: 输入提示
            default: 默认值 (True=是, False=否, None=必须选择)

        Returns:
            用户选择 (True=是, False=否)
        """
        try:
            # 构建提示字符串
            if default is True:
                choice_hint = "[Y/n]"
            elif default is False:
                choice_hint = "[y/N]"
            else:
                choice_hint = "[y/n]"

            # 获取用户输入
            while True:
                user_input = input(f"{prompt} {choice_hint}: ").strip().lower()

                # 处理空输入
                if not user_input:
                    if default is not None:
                        return default
                    else:
                        print(f"{Fore.RED}请输入 y 或 n{Style.RESET_ALL}")
                        continue

                # 验证输入
                if user_input in ["y", "yes", "是"]:
                    return True
                elif user_input in ["n", "no", "否"]:
                    return False
                else:
                    print(f"{Fore.RED}请输入 y 或 n{Style.RESET_ALL}")

        except Exception as e:
            logger.error(f"获取是否选择失败: {e}")
            raise

    def show_path_history_summary(self, config: UnifiedConfig) -> None:
        """显示路径历史记录摘要

        Args:
            config: 统一配置对象
        """
        try:
            stats = history_service.get_history_stats(config)

            if not stats:
                print(f"{Fore.YELLOW}📝 没有路径历史记录{Style.RESET_ALL}")
                return

            print(f"\n{Fore.BLUE}📝 路径历史记录摘要{Style.RESET_ALL}")
            print("=" * 50)

            for path_type, stat in stats.items():
                count = stat.get("count", 0)
                max_length = stat.get("max_length", 10)
                has_last_used = stat.get("has_last_used", False)

                status = "✅" if has_last_used else "📝"
                print(f"{status} {path_type}: {count}/{max_length} 条记录")

                if has_last_used:
                    last_used = history_service.get_last_used_path(path_type, config)
                    if last_used:
                        print(f"   最后使用: {last_used}")

            print("=" * 50)

        except Exception as e:
            logger.error(f"显示历史记录摘要失败: {e}")
            print(f"{Fore.RED}❌ 无法显示历史记录摘要{Style.RESET_ALL}")


# 单例实例
user_interaction_service = UserInteractionService()
