import logging
import sys
import os
import argparse
from pathlib import Path
from day_translation.core.main import main
from day_translation.utils.user_config import load_user_config

def setup_logging():
    """设置日志"""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "run_day_translation.log"), encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

def show_welcome():
    """显示欢迎界面"""
    print("\n=== 欢迎使用 Day Translation v0.1.0 ===")
    print("功能：模组文本提取、阿里云机器翻译、翻译导入、批量处理")
    user_config = load_user_config()
    print(f"阿里云密钥：{'已配置' if user_config.get('ALIYUN_ACCESS_KEY_ID') else '未配置'}")
    print("输入 'q' 随时退出，'b' 返回主菜单")
    print("=====================================\n")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Day Translation 模组翻译工具")
    parser.add_argument('--mod-dir', help="模组目录路径")
    parser.add_argument('--mode', choices=['1', '2', '3', '4', '5', '6'], help="运行模式 (1-6)")
    return parser.parse_args()

if __name__ == "__main__":
    try:
        setup_logging()
        show_welcome()
        args = parse_args()
        logging.info("启动 Day Translation...")
        # 动态添加项目根目录到 sys.path
        project_root = str(Path(__file__).parent.resolve())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        main()
    except ImportError as e:
        logging.error(f"导入错误: {e}")
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖模块都已正确安装")
        input("按回车键退出...")
    except Exception as e:
        logging.error(f"运行错误: {e}", exc_info=True)
        print(f"❌ 运行错误: {e}")
        input("按回车键退出...")