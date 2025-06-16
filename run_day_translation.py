import logging
import sys
import os
import argparse
from pathlib import Path
from colorama import init, Fore, Style
from day_translation.core.main import main
from day_translation.utils.user_config import load_user_config

# 初始化 colorama
init()

def setup_logging():
    """配置日志记录，输出到文件和控制台"""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "run_day_translation.log"), encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.debug("日志配置完成")

def show_welcome():
    """显示程序欢迎界面，包含版本和配置状态"""
    user_config = load_user_config()
    has_api_key = bool(user_config.get('ALIYUN_ACCESS_KEY_ID') or os.getenv('ALIYUN_ACCESS_KEY_ID'))
    print(f"\n{Fore.MAGENTA}=== 欢迎使用 Day Translation v0.1.0 ==={Style.RESET_ALL}")
    print(f"功能：模组文本提取、阿里云机器翻译、翻译导入、批量处理")
    print(f"阿里云密钥：{Fore.GREEN if has_api_key else Fore.RED}{'已配置' if has_api_key else '未配置'}{Style.RESET_ALL}")
    print(f"输入 '{Fore.RED}q{Style.RESET_ALL}' 随时退出，'{Fore.YELLOW}b{Style.RESET_ALL}' 返回主菜单")
    print(f"{Fore.MAGENTA}====================================={Style.RESET_ALL}\n")
    logging.debug("显示欢迎界面")

def parse_args():
    """
    解析命令行参数

    Returns:
        argparse.Namespace: 包含 mod_dir 和 mode 的参数对象
    """
    parser = argparse.ArgumentParser(description="Day Translation 模组翻译工具")
    parser.add_argument('--mod-dir', help="模组目录路径")
    parser.add_argument('--mode', choices=['1', '2', '3', '4', '5', '6'], help="运行模式 (1-6)")
    args = parser.parse_args()
    logging.debug(f"命令行参数: mod_dir={args.mod_dir}, mode={args.mode}")
    return args

if __name__ == "__main__":
    """程序入口，初始化并运行主工作流"""
    try:
        setup_logging()
        show_welcome()
        args = parse_args()
        logging.info("启动 Day Translation...")
        # 动态添加项目根目录到 sys.path
        project_root = str(Path(__file__).parent.resolve())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logging.debug(f"添加 sys.path: {project_root}")
        main()
    except ImportError as e:
        logging.error(f"导入错误: {e}", exc_info=True)
        print(f"{Fore.RED}❌ 导入错误: {e}{Style.RESET_ALL}")
        print("请确保所有依赖模块都已正确安装")
        input(f"{Fore.YELLOW}按回车键退出...{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"运行错误: {e}", exc_info=True)
        print(f"{Fore.RED}❌ 运行错误: {e}{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}按回车键退出...{Style.RESET_ALL}")