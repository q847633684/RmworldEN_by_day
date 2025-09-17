"""
Java翻译处理器
处理Java翻译工具的交互流程
"""

import logging
import subprocess
import os
from pathlib import Path
from colorama import Fore, Style

from utils.interaction import (
    select_csv_path_with_history,
    confirm_action,
    auto_generate_output_path,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from .java_translator import JavaTranslator
from utils.path_manager import PathManager
from utils.config import get_user_config


def handle_java_translate():
    """处理Java机翻功能"""
    try:
        # 尝试创建Java翻译器实例
        try:
            translator = JavaTranslator()
            status = translator.get_status()
        except FileNotFoundError as e:
            show_error(str(e))
            # 自动构建逻辑
            user_input = (
                input(f"{Fore.YELLOW}是否自动构建Java工具？[y/n]: {Style.RESET_ALL}")
                .strip()
                .lower()
            )
            if user_input == "y":
                # 构建脚本现在在当前目录下的RimWorldBatchTranslate子目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                build_script = os.path.join(
                    current_dir, "RimWorldBatchTranslate", "build.bat"
                )
                if os.path.exists(build_script):
                    show_info("正在自动构建Java工具...")
                    result = subprocess.run([build_script], shell=True)
                    if result.returncode == 0:
                        show_success("Java工具构建完成，正在重新检测...")
                        # 构建后重新尝试创建翻译器
                        try:
                            translator = JavaTranslator()
                            status = translator.get_status()
                            show_success("Java翻译工具已就绪！")
                        except FileNotFoundError:
                            show_error("构建后仍未检测到JAR文件，请手动检查构建日志。")
                            return
                    else:
                        show_error("Java工具构建失败，请手动检查构建日志。")
                        return
                else:
                    show_error(
                        "未找到build.bat脚本，请手动进入RimWorldBatchTranslate目录构建。"
                    )
                    show_info(f"脚本路径: {build_script}")
                    return
            else:
                show_warning("用户取消构建，返回主菜单")
                return

        # 检查Java工具是否可用
        if not status["java_available"]:
            show_error("Java未安装或不在PATH中")
            show_warning("请先安装Java 8或更高版本")
            return

        if not status["jar_exists"]:
            show_error("Java翻译工具JAR文件不存在")
            show_warning("请先构建Java工具：")
            show_info("cd RimWorldBatchTranslate && mvn package")
            return

        show_success("Java翻译工具已就绪")

        # 获取输入CSV文件
        csv_path = select_csv_path_with_history()
        if not csv_path:
            return

        # 自动生成输出CSV文件路径
        output_csv = auto_generate_output_path(csv_path)
        # 将输出CSV加入“导入翻译”的历史，便于后续直接选择
        try:
            PathManager().remember_path("import_csv", output_csv)
        except Exception:
            pass

        # 确认开始翻译
        show_info("=== Java翻译工具配置 ===")
        print(f"输入文件: {csv_path}")
        print(f"输出文件: {output_csv}")
        print(f"JAR路径: {status['jar_path']}")

        if confirm_action("确认开始翻译？"):
            show_info("=== 开始Java翻译 ===")
            try:
                # 优先使用已保存的配置中的密钥，缺失时退回交互输入
                cfg = get_user_config() or {}
                ak = (cfg.get("aliyun_access_key_id") or "").strip()
                sk = (cfg.get("aliyun_access_key_secret") or "").strip()
                if ak and sk:
                    success = translator.translate_csv(csv_path, output_csv, ak, sk)
                else:
                    success = translator.translate_csv_interactive(csv_path, output_csv)

                if success:
                    show_success("Java翻译完成！")
                    print(f"翻译结果已保存到: {output_csv}")
                else:
                    show_error("Java翻译失败")
            except Exception as e:
                show_error(f"Java翻译执行异常: {str(e)}")
                logging.error("Java翻译执行异常: %s", str(e), exc_info=True)
        else:
            show_warning("用户取消翻译")

    except ImportError as e:
        show_error(f"Java翻译模块导入失败: {str(e)}")
        show_warning("请确保 java_translate.java_translator 模块存在")
    except Exception as e:
        show_error(f"Java翻译失败: {str(e)}")
        logging.error("Java翻译失败: %s", str(e), exc_info=True)
