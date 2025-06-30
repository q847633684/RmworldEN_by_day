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
from colorama import init

# 添加当前模块的父目录到sys.path，以支持day_translation模块导入
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 初始化 colorama 以支持 Windows 终端颜色
init()

# 导入功能模块
from day_translation.extract.handler import handle_extract
from day_translation.python_translate.handler import handle_python_translate
from day_translation.java_translate.handler import handle_java_translate
from day_translation.import_template.handler import handle_import_template
from day_translation.batch.handler import handle_batch
from day_translation.corpus.handler import handle_corpus
from day_translation.full_pipeline.handler import handle_full_pipeline
from day_translation.config_manage.handler import handle_config_manage
from day_translation.utils.interaction import show_main_menu


def main():
    """主程序入口"""
    while True:
        mode = show_main_menu()
        if mode == "1":
            handle_extract()
            input("\n按回车返回主菜单...")
        elif mode == "2":
            handle_python_translate()
            input("\n按回车返回主菜单...")
        elif mode == "3":
            handle_import_template()
            input("\n按回车返回主菜单...")
        elif mode == "4":
            handle_corpus()
            input("\n按回车返回主菜单...")
        elif mode == "5":
            handle_full_pipeline()
            input("\n按回车返回主菜单...")
        elif mode == "6":
            handle_batch()
            input("\n按回车返回主菜单...")
        elif mode == "7":
            handle_config_manage()
            input("\n按回车返回主菜单...")
        elif mode == "8":
            handle_java_translate()
            input("\n按回车返回主菜单...")
        elif mode == "q":
            print("👋 感谢使用 Day Translation！")
            break
        else:
            print("❌ 无效选项，请重新输入。")
            input("\n按回车返回主菜单...")
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    main()
