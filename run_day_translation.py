import logging
import sys
import os
from day_translation.core.main import main

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

if __name__ == "__main__":
    try:
        setup_logging()
        logging.info("启动 Day Translation...")
        main()
    except ImportError as e:
        logging.error(f"导入错误: {e}")
        print(f"导入错误: {e}")
        print("请确保所有依赖模块都已正确安装")
        input("按回车键退出...")
    except Exception as e:
        logging.error(f"运行错误: {e}", exc_info=True)
        print(f"运行错误: {e}")
        input("按回车键退出...")