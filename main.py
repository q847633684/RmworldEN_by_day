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
from config_manage.handler import handle_config_manage
from corpus.handler import handle_corpus
from extract import handle_extract
from full_pipeline.handler import handle_full_pipeline
from import_template.handler import handle_import_template
from translate.handler import handle_unified_translate
from utils.interaction import show_main_menu

# 初始化 colorama 以支持 Windows 终端颜色
init()


def main():
    """主程序入口"""
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        mode = show_main_menu()
        if mode == "1":
            handle_full_pipeline()
            input("\n按回车返回主菜单...")
        elif mode == "2":
            handle_extract()
            input("\n按回车返回主菜单...")
        elif mode == "3":
            handle_unified_translate()
            input("\n按回车返回主菜单...")
        elif mode == "4":
            handle_import_template()
            input("\n按回车返回主菜单...")
        elif mode == "5":
            handle_batch()
            input("\n按回车返回主菜单...")
        elif mode == "6":
            handle_config_manage()
            input("\n按回车返回主菜单...")
        elif mode == "7":
            handle_corpus()
            input("\n按回车返回主菜单...")
        elif mode == "q":
            print("👋 感谢使用 Day Translation！")
            break
        else:
            print("❌ 无效选项，请重新输入。")
            input("\n按回车返回主菜单...")


if __name__ == "__main__":
    main()
