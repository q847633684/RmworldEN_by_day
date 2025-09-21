"""
统一翻译处理器
提供统一的翻译功能入口，替代原有的Java和Python翻译处理器
"""

import os
from typing import Optional
from utils.logging_config import get_logger
from utils.ui_style import ui
from utils.interaction import (
    select_csv_path_with_history,
    auto_generate_output_path,
    show_success,
    show_error,
    show_info,
    show_warning,
    confirm_action,
)
from utils.path_manager import PathManager
from utils.config import get_user_config
from core.translation_facade import TranslationFacade


def handle_unified_translate(csv_path: Optional[str] = None) -> bool:
    """
    处理统一翻译功能

    Returns:
        bool: 翻译是否完成（True=完成，False=未完成或中断）
    """
    logger = get_logger(f"{__name__}.handle_unified_translate")

    try:
        # 创建翻译门面实例（需要模组目录，这里使用临时目录）
        import tempfile

        temp_dir = tempfile.mkdtemp()
        facade = TranslationFacade(temp_dir, "ChineseSimplified")

        # 显示翻译器状态
        ui.print_section_header("翻译器状态", ui.Icons.SETTINGS)
        translator_status = facade.get_translator_status()

        for name, status in translator_status.items():
            if name == "error":
                ui.print_error(f"获取状态失败: {status}")
                continue

            if status.get("available", False):
                ui.print_success(f"✅ {name.upper()}翻译器: 可用")
                if "jar_path" in status:
                    ui.print_info(f"   JAR路径: {status['jar_path']}")
            else:
                reason = status.get("reason", "未知原因")
                ui.print_warning(f"❌ {name.upper()}翻译器: 不可用 ({reason})")

        ui.print_separator()

        # 检查是否有可用的翻译器
        available_translators = [
            name
            for name, status in translator_status.items()
            if status.get("available", False)
        ]

        if not available_translators:
            ui.print_error("没有可用的翻译器！")
            ui.print_info("请检查：")
            ui.print_info("1. Java环境是否正确安装")
            ui.print_info("2. Java翻译工具是否已构建")
            ui.print_info("3. 阿里云SDK是否已安装")
            return

        # 自动选择最佳翻译器
        translator_type = "auto"  # 默认自动选择最佳翻译器
        ui.print_info(
            f"🎯 自动选择翻译器: {'Java' if 'java' in available_translators else 'Python'}"
        )

        # 获取输入CSV文件
        if csv_path is None:
            csv_path = select_csv_path_with_history()
            if not csv_path:
                return False
        else:
            # 使用提供的CSV路径
            ui.print_info(f"📄 使用指定CSV文件: {os.path.basename(csv_path)}")

        # 检查是否可以恢复翻译
        resume_file = facade.can_resume_translation(csv_path)
        if resume_file:
            ui.print_info(f"检测到可恢复的翻译文件: {resume_file}")
            ui.print_info("自动恢复翻译...")
            success = facade.resume_translation(csv_path, resume_file)
            if success:
                ui.print_success("恢复翻译完成！")
                # 将输出CSV加入"导入翻译"的历史
                try:
                    PathManager().remember_path("import_csv", resume_file)
                except Exception:
                    pass
                return True  # 翻译完成
            else:
                return False  # 翻译未完成（用户中断）

        # 自动生成输出CSV文件路径
        output_csv = auto_generate_output_path(csv_path)

        # 将输出CSV加入"导入翻译"的历史
        try:
            PathManager().remember_path("import_csv", output_csv)
        except Exception:
            pass

        # 显示翻译配置（简化版）
        ui.print_section_header("翻译配置", ui.Icons.SETTINGS)
        ui.print_key_value("输入文件", os.path.basename(csv_path), ui.Icons.FILE)
        ui.print_key_value("输出文件", os.path.basename(output_csv), ui.Icons.FILE)
        ui.print_key_value(
            "翻译器",
            f"{'Java' if 'java' in available_translators else 'Python'}翻译器",
            ui.Icons.SETTINGS,
        )

        # 显示翻译器特性（简化版）
        if "java" in available_translators:
            ui.print_info("🚀 Java翻译器: 高性能，支持中断和恢复")
        else:
            ui.print_info("🐍 Python翻译器: 简单部署，稳定可靠")

        if confirm_action("确认开始翻译？"):
            ui.print_section_header("开始翻译", ui.Icons.TRANSLATE)

            # 检查API密钥配置
            user_config = get_user_config() or {}
            ak = user_config.get("aliyun_access_key_id", "").strip()
            sk = user_config.get("aliyun_access_key_secret", "").strip()

            if not ak or not sk:
                ui.print_error("未找到阿里云翻译密钥配置")
                ui.print_info("请先配置翻译密钥：")
                ui.print_info(
                    "1. 在配置文件中设置 aliyun_access_key_id 和 aliyun_access_key_secret"
                )
                ui.print_info("2. 或使用配置管理功能进行配置")
                return False

            # 执行翻译
            try:
                facade.machine_translate(csv_path, output_csv, translator_type)
                return True  # 翻译完成
            except Exception as e:
                ui.print_error(f"翻译失败: {str(e)}")
                return False  # 翻译失败

        else:
            ui.print_warning("用户取消翻译")
            return False  # 用户取消

    except Exception as e:
        ui.print_error(f"统一翻译失败: {str(e)}")
        logger.error("统一翻译失败: %s", str(e), exc_info=True)
        return False
