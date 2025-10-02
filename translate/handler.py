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
)
from user_config.path_manager import PathManager

# 延迟导入避免循环依赖
from core.exceptions import TranslationError


def handle_unified_translate(csv_path: Optional[str] = None) -> Optional[str]:
    """
    处理统一翻译功能

    Returns:
        Optional[str]: 翻译完成时返回输出文件路径，失败或中断时返回None
    """
    logger = get_logger(f"{__name__}.handle_unified_translate")

    try:
        # 创建翻译门面实例（需要模组目录，这里使用临时目录）
        import tempfile
        from core.translation_facade import TranslationFacade
        from user_config import UserConfigManager

        # 获取配置中的中文语言设置
        config = UserConfigManager()
        cn_language = config.language_config.get_value(
            "cn_language", "ChineseSimplified"
        )

        temp_dir = tempfile.mkdtemp()
        facade = TranslationFacade(temp_dir, cn_language)

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
                return None
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
                PathManager().remember_path("import_csv", resume_file)
                return resume_file  # 翻译完成，返回输出文件路径
            else:
                return None  # 翻译未完成（用户中断）

        # 自动生成输出CSV文件路径
        output_csv = auto_generate_output_path(csv_path)

        # 将输出CSV加入"导入翻译"的历史
        PathManager().remember_path("import_csv", output_csv)

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

        ui.print_section_header("开始翻译", ui.Icons.TRANSLATE)

        # 检查API密钥配置（使用新配置系统）
        try:
            from user_config import UserConfigManager

            config_manager = UserConfigManager()
            api_manager = config_manager.api_manager

            # 获取主要API配置
            primary_api = api_manager.get_primary_api()

            if not primary_api or not primary_api.is_enabled():
                ui.print_error("未找到启用的翻译API配置")
                ui.print_info("请先配置翻译API：")
                ui.print_info("1. 运行主程序选择'配置管理'")
                ui.print_info("2. 选择'API配置'进行设置")
                ui.print_info("3. 配置并启用至少一个翻译API")
                return None

            # 验证API配置
            if not primary_api.validate():
                ui.print_error(f"{primary_api.name}配置不完整或无效")
                ui.print_info("请检查API配置中的必需字段")
                return None

            ui.print_info(f"🌐 使用翻译API: {primary_api.name}")

        except Exception as e:
            ui.print_error(f"加载翻译API配置失败: {str(e)}")
            ui.print_info("请检查配置系统是否正常工作")
            return None

        # 执行翻译
        try:
            facade.machine_translate(csv_path, output_csv, translator_type)
            return output_csv  # 翻译完成，返回输出文件路径
        except TranslationError as e:
            ui.print_error(f"翻译失败: {str(e)}")
            return None  # 翻译失败
        except (OSError, IOError, ValueError) as e:
            ui.print_error(f"翻译过程中发生错误: {str(e)}")
            return None  # 翻译失败

    except (KeyboardInterrupt,) as e:
        # 用户中断异常
        ui.print_error(f"用户中断翻译: {str(e)}")
        logger.error("用户中断翻译: %s", str(e), exc_info=True)
        return None
    except (ConnectionError, TimeoutError) as e:
        # 网络相关异常（在OSError之前，因为它们是OSError的子类）
        ui.print_error(f"统一翻译发生网络错误: {str(e)}")
        logger.error("统一翻译发生网络错误: %s", str(e), exc_info=True)
        return None
    except (
        TranslationError,
        ValueError,
        RuntimeError,
        ImportError,
    ) as e:
        ui.print_error(f"统一翻译失败: {str(e)}")
        logger.error("统一翻译失败: %s", str(e), exc_info=True)
        return None
    except (OSError, IOError) as e:
        # 系统IO相关异常（放在最后，因为它是其他异常的父类）
        ui.print_error(f"统一翻译发生系统错误: {str(e)}")
        logger.error("统一翻译发生系统错误: %s", str(e), exc_info=True)
        return None
