"""
批量处理器交互入口
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

def handle_batch():
    """批量处理主入口"""
    try:
        # 选择模组目录
        mod_dirs = select_mod_path_with_version_detection(multi=True)
        if not mod_dirs:
            return

        # 延迟导入，避免循环导入
        from day_translation.core.translation_facade import TranslationFacade
        
        # 创建翻译门面实例
        facade = TranslationFacade(mod_dirs[0])  # 示例，实际可批量

        # 这里可以扩展为批量处理逻辑
        show_info("=== 开始批量处理 ===")
        try:
            # 示例：批量处理
            result = facade.batch_process(mod_dirs)
            show_success(f"批量处理完成！共处理 {len(result)} 个模组")
        except Exception as e:
            show_error(f"批量处理失败: {str(e)}")
            logging.error("批量处理失败: %s", str(e), exc_info=True)
    except Exception as e:
        show_error(f"批量功能失败: {str(e)}")
        logging.error("批量功能失败: %s", str(e), exc_info=True) 