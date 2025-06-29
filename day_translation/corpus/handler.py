"""
语料处理器
处理生成英-中平行语料的交互流程
"""

import logging
from colorama import Fore, Style

from day_translation.utils.interaction import (
    select_mod_path_with_version_detection,
    show_success,
    show_error,
    show_info,
    show_warning
)
from day_translation.utils.path_manager import PathManager

path_manager = PathManager()

def handle_corpus():
    """处理生成语料功能"""
    try:
        # 选择模组目录
        mod_dir = select_mod_path_with_version_detection()
        if not mod_dir:
            return

        # 延迟导入，避免循环导入
        from day_translation.core.translation_facade import TranslationFacade
        
        # 创建翻译门面实例
        facade = TranslationFacade(mod_dir)

        # 生成语料
        show_info("=== 开始生成语料 ===")
        try:
            facade.generate_corpus()
            show_success("语料生成完成！")
        except Exception as e:
            show_error(f"语料生成失败: {str(e)}")
            logging.error("语料生成失败: %s", str(e), exc_info=True)
    except Exception as e:
        show_error(f"语料功能失败: {str(e)}")
        logging.error("语料功能失败: %s", str(e), exc_info=True) 