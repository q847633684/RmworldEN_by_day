"""
Java翻译处理器
处理Java翻译工具的交互流程
"""

import os
import subprocess
from colorama import Fore, Style

from utils.interaction import (
    select_csv_path_with_history,
    auto_generate_output_path,
    show_success,
    show_error,
    show_info,
    show_warning,
    confirm_action,
)
from utils.logging_config import get_logger
from .java_translator_simple import JavaTranslator
from utils.path_manager import PathManager
from utils.config import get_user_config


def handle_java_translate():
    """处理Java机翻功能"""
    logger = get_logger(f"{__name__}.handle_java_translate")
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
                # 自动构建逻辑
                current_dir = os.path.dirname(os.path.abspath(__file__))
                java_proj_dir = os.path.join(current_dir, "RimWorldBatchTranslate")
                show_info("正在自动构建Java工具...")
                result = subprocess.run(
                    "mvn package",
                    shell=True,
                    cwd=java_proj_dir,
                    capture_output=True,
                    text=True,
                )
                print("--- Maven 构建输出 ---")
                print(result.stdout)
                print(result.stderr)
                if result.returncode == 0:
                    # 构建成功后，列出 target 目录下所有 JAR 文件
                    target_dir = os.path.join(java_proj_dir, "target")
                    if os.path.exists(target_dir):
                        jar_files = [
                            f for f in os.listdir(target_dir) if f.endswith(".jar")
                        ]
                        if jar_files:
                            show_info(f"target 目录下JAR文件: {jar_files}")
                        else:
                            show_warning("target 目录下未发现JAR文件！")
                    else:
                        show_warning("未找到target目录！")
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

        # 检查是否可以恢复暂停的翻译
        output_csv = translator.can_resume_translation(csv_path)
        if output_csv:
            print(f"\n🔄 检测到可恢复的翻译文件，自动恢复翻译...")
            success = translator.resume_translation(csv_path, output_csv)
            if success:
                show_success("恢复翻译完成！")
            else:
                # 用户中断翻译是正常操作，不显示为失败
                print("💡 翻译已暂停，可以随时恢复")
            return

        # 自动生成输出CSV文件路径
        output_csv = auto_generate_output_path(csv_path)
        # 将输出CSV加入"导入翻译"的历史，便于后续直接选择
        try:
            PathManager().remember_path("import_csv", output_csv)
        except Exception:
            pass

        # 确认开始翻译
        show_info("=== Java翻译工具配置 ===")
        print(f"输入文件: {csv_path}")
        print(f"输出文件: {output_csv}")
        print(f"JAR路径: {status['jar_path']}")
        print("\n💡 新功能:")
        print("  - 支持中断翻译 (Ctrl+C)")
        print("  - 支持恢复翻译")
        print("  - 自动保存翻译进度")

        if confirm_action("确认开始翻译？"):
            print()  # 添加空行，让进度条显示更清晰
            show_info("=== 开始Java翻译 ===")
            try:
                # 优先使用已保存的配置中的密钥，缺失时退回交互输入
                cfg = get_user_config() or {}
                ak = (cfg.get("aliyun_access_key_id") or "").strip()
                sk = (cfg.get("aliyun_access_key_secret") or "").strip()
                if ak and sk:
                    success = translator.translate_csv(csv_path, output_csv, ak, sk)
                else:
                    # 如果没有配置密钥，提示用户配置
                    show_error("未找到阿里云翻译密钥配置")
                    show_info("请先配置翻译密钥：")
                    show_info(
                        "1. 在配置文件中设置 aliyun_access_key_id 和 aliyun_access_key_secret"
                    )
                    show_info("2. 或使用其他功能进行配置")
                    return

                if success is True:
                    show_success("Java翻译完成！")
                    print(f"翻译结果已保存到: {output_csv}")
                elif success is None:
                    # 用户中断，不是失败
                    print("💡 翻译已暂停，可以随时恢复")
                else:
                    show_error("Java翻译失败")
            except KeyboardInterrupt:
                show_warning("翻译被用户中断")
                print("💡 提示: 可以使用恢复功能继续翻译")
            except Exception as e:
                show_error(f"Java翻译执行异常: {str(e)}")
                logger.error("Java翻译执行异常: %s", str(e), exc_info=True)
        else:
            show_warning("用户取消翻译")

    except ImportError as e:
        show_error(f"Java翻译模块导入失败: {str(e)}")
        show_warning("请确保 java_translate.java_translator 模块存在")
    except Exception as e:
        show_error(f"Java翻译失败: {str(e)}")
        logger.error("Java翻译失败: %s", str(e), exc_info=True)
