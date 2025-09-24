"""
语料处理器
处理生成英-中平行语料的交互流程
"""

from utils.logging_config import get_logger

from utils.interaction import (
    select_mod_path_with_version_detection,
    show_success,
    show_error,
    show_info,
)
from utils.path_manager import PathManager
from utils.ui_style import ui
from core.translation_facade import TranslationFacade
from utils.config import get_config

path_manager = PathManager()


def select_corpus_mode(project_type: str = None):
    """选择语料生成模式"""

    ui.print_section_header("选择语料生成模式", ui.Icons.SETTINGS)

    # 根据项目类型显示不同的选项
    if project_type == "standard":
        # 标准模组结构：支持两种模式
        ui.print_menu_item(
            "1",
            "从XML注释提取",
            "从带 <!--EN: --> 注释的文件中提取中英文对",
            ui.Icons.SCAN,
        )
        ui.print_menu_item(
            "2",
            "从文件对比提取",
            "对比DefInjected和Keyed目录的英文和中文文件",
            ui.Icons.DATA,
        )
        valid_choices = ["1", "2"]
        prompt_text = "请选择模式 (1-2)"
    else:
        # 多DLC结构或其他：只支持模式1
        ui.print_menu_item(
            "1",
            "从XML注释提取",
            "从带 <!--EN: --> 注释的文件中提取中英文对",
            ui.Icons.SCAN,
        )
        ui.print_info("注意：当前项目结构只支持从XML注释提取模式")
        valid_choices = ["1"]
        prompt_text = "请选择模式 (1)"

    while True:
        choice = input(f"\n{ui.Icons.INFO} {prompt_text}: ").strip()

        if choice == "1":
            ui.print_info("已选择：从XML注释提取模式")
            return "1"
        elif choice == "2" and "2" in valid_choices:
            ui.print_info("已选择：从文件对比提取模式")
            return "2"
        else:
            ui.print_error(f"❌ 无效选择，请输入 {prompt_text}")


def handle_corpus():
    logger = get_logger(f"{__name__}.handle_corpus")

    """处理生成语料功能"""
    try:
        # 选择模组目录
        result = select_mod_path_with_version_detection(allow_multidlc=True)
        if not result:
            return

        # 解包结果：mod_dir, project_type
        if isinstance(result, tuple):
            mod_dir, project_type = result
        else:
            # 非多DLC结构，默认为标准结构
            mod_dir = result
            project_type = "standard"

        # 选择语料生成模式
        mode = select_corpus_mode(project_type)
        if not mode:
            return

        # 获取配置
        config = get_config()

        # 创建翻译门面实例
        facade = TranslationFacade(mod_dir, config.CN_language)

        # 生成语料
        show_info("=== 开始生成语料 ===")
        try:
            facade.generate_corpus(mode)
            show_success("语料生成完成！")
        except (OSError, IOError, ValueError, RuntimeError) as e:
            show_error(f"语料生成失败: {str(e)}")
            logger.error("语料生成失败: %s", str(e), exc_info=True)
    except (OSError, IOError, ValueError, RuntimeError, ImportError) as e:
        show_error(f"语料功能失败: {str(e)}")
        logger.error("语料功能失败: %s", str(e), exc_info=True)
