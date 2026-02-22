"""
Day Translation - RimWorld 模组汉化工具
主程序入口

这是 Day Translation 项目的主要入口点，提供以下核心功能：
- 模组翻译文本提取和模板生成
- 阿里云机器翻译服务集成
- 翻译结果导入和模板管理
- 英中平行语料生成
- 批量处理多个模组
- 配置管理和用户交互

主要类：
- TranslationFacade: 翻译操作的核心接口
- TranslationError: 翻译相关异常的基类
- TranslationImportError: 导入操作异常
- ExportError: 导出操作异常

主要函数：
- main(): 程序主入口，提供交互式菜单
- validate_dir(): 验证目录路径
- validate_file(): 验证文件路径
- show_welcome(): 显示欢迎界面

使用方法:
    python main.py

作者: Day Translation Team
版本: 0.1.0
"""

import os
import sys
from pathlib import Path
from colorama import init  # type: ignore

# 确保项目根目录在 sys.path 中，以支持直接运行脚本时的包导入
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 统一导入项目内部模块（避免分散导入导致的分组问题）
from batch.handler import handle_batch

# 配置管理功能直接集成
from corpus.handler import handle_corpus
from extract import handle_extract
from full_pipeline.handler import handle_full_pipeline
from import_template.handler import handle_import_template, handle_migrate_translations
from repair_translation.handler import handle_repair_translation
from translate.handler import handle_unified_translate
from extract.cleanup_outdated_keys import handle_cleanup_outdated_keys
from utils.interaction import show_main_menu, wait_for_user_input
from utils.ui_style import ui
from utils.interaction import confirm_action

# 初始化 colorama 以支持 Windows 终端颜色
init()


def handle_config_manage():
    """处理配置管理功能"""
    from utils.logging_config import get_logger
    from utils.ui_style import ui
    from user_config import UserConfigManager
    from user_config.ui import MainConfigUI

    logger = get_logger(__name__)

    try:
        # 直接启动新的配置系统
        config_manager = UserConfigManager.get_instance()
        config_ui = MainConfigUI(config_manager)
        config_ui.show_main_menu()

    except Exception as e:
        ui.print_error(f"启动配置系统失败: {str(e)}")
        logger.error("启动配置系统失败: %s", str(e), exc_info=True)


def main():
    """主程序入口"""

    # 根据配置决定是否在启动时清理日志
    try:
        from user_config import UserConfigManager

        config_manager = UserConfigManager.get_instance()
        log_config = config_manager.log_config

        if log_config.get_value("auto_cleanup_logs", True):
            from utils.logging_config import LoggingConfig

            # 根据配置决定清理模式
            if log_config.get_value("cleanup_all_logs_on_startup", False):
                # 清理所有日志
                LoggingConfig.cleanup_all_logs()
            else:
                # 清理指定天数的日志
                retention_days = log_config.get_value("log_retention_days", 7)
                LoggingConfig._cleanup_old_logs(retention_days)
    except Exception:
        # 忽略日志清理错误，不影响主程序运行
        pass

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        mode = show_main_menu()

        try:
            if mode == "1":
                handle_full_pipeline()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "2":
                handle_extract()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "3":
                handle_unified_translate()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "4":
                handle_import_template()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "5":
                handle_batch()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "6":
                handle_config_manage()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "7":
                handle_corpus()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "8":
                handle_cleanup_outdated_keys()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "9":
                handle_migrate_translations()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "10":
                handle_repair_translation()
                wait_for_user_input("按回车返回主菜单...")
            elif mode == "q":
                ui.print_success("👋 感谢使用 Day Translation！")
                break
            else:
                ui.print_error("❌ 无效选项，请重新输入（1-10 或 q）。")
                wait_for_user_input("按回车返回主菜单...")
        except KeyboardInterrupt:
            ui.print_warning("\n⚠️ 用户中断操作")

            if confirm_action("是否退出程序？"):
                ui.print_success("👋 感谢使用 Day Translation！")
                break
            continue
        except (ValueError, RuntimeError, ImportError) as e:
            ui.print_error(f"❌ 程序执行出错: {str(e)}")
            wait_for_user_input("按回车返回主菜单...")
        except Exception as e:
            ui.print_error(f"❌ 发生未预期的错误: {str(e)}")
            try:
                from user_config import UserConfigManager
                if UserConfigManager.get_instance().system_config.get_value("debug_mode", False):
                    import traceback
                    traceback.print_exc()
            except Exception:
                pass
            wait_for_user_input("按回车返回主菜单...")


if __name__ == "__main__":
    main()
