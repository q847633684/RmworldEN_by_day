"""
统一翻译处理器
提供统一的翻译功能入口，替代原有的Java和Python翻译处理器
"""

import os
import threading
from pathlib import Path
from typing import Optional
from utils.logging_config import get_logger
from utils.ui_style import ui
from utils.interaction import select_csv_path_with_history
from user_config.path_manager import PathManager

# 延迟导入避免循环依赖


def handle_unified_translate(
    csv_path: Optional[str] = None, output_csv: Optional[str] = None
) -> Optional[str]:
    """
    处理统一翻译功能

    Returns:
        Optional[str]: 翻译完成时返回输出文件路径，失败或中断时返回None
    """
    logger = get_logger(f"{__name__}.handle_unified_translate")

    try:
        # 直接使用统一翻译器
        from translate.unified_translator import UnifiedTranslator

        # 创建统一翻译器实例
        translator = UnifiedTranslator()

        # 显示翻译器状态
        ui.print_section_header("翻译器状态", ui.Icons.SETTINGS)
        translator_status = translator.get_available_translators()

        for name, status in translator_status.items():
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
            ui.print_info("请安装免费翻译: pip install deep-translator")
            ui.print_info("或配置阿里云/Java 翻译。")
            return

        # 子选项：仅当未传入 csv_path 时显示
        if csv_path is None:
            ui.print_section_header("操作选择", ui.Icons.SETTINGS)
            ui.print_menu_item("1", "翻译 CSV", "使用当前翻译器翻译 CSV", ui.Icons.TRANSLATE, compact=True)
            ui.print_menu_item(
                "2",
                "仅恢复翻译列占位符",
                "将 translated 列中的 (PH_1) 等恢复为 [saw]、[nudity] 等（用于阿里云等未恢复的 CSV）",
                ui.Icons.SETTINGS,
                compact=True,
            )
            from utils.interaction import safe_input
            choice = safe_input(ui.get_input_prompt("请选择", options="1-2, q（回车=1）"), "1")
            if choice is None or choice.lower() == "q":
                return None
            if choice.strip() == "2":
                restore_path = select_csv_path_with_history()
                if not restore_path:
                    return None
                from translate.core.placeholders import PlaceholderManager
                pm = PlaceholderManager()
                ok, count = pm.restore_csv_translated_column(restore_path)
                if ok:
                    ui.print_success(f"✅ 翻译列占位符已恢复，共 {count} 条。可继续用「翻译 CSV」选 Google 重新翻译，或直接导入。")
                else:
                    ui.print_error("恢复失败，请确认 CSV 含 key / text / translated 列。")
                return restore_path if ok else None

        # 自动选择：优先 Google（免费），其次 Java/阿里云，最后 Python/阿里云
        translator_type = "auto"
        if "google" in available_translators:
            ui.print_info("🎯 自动选择: Google 翻译（免费，无需 API 密钥）")
        elif "java" in available_translators:
            ui.print_info("🎯 自动选择: Java/阿里云 翻译")
        else:
            ui.print_info("🎯 自动选择: Python/阿里云 翻译")

        # 获取输入CSV文件
        if csv_path is None:
            csv_path = select_csv_path_with_history()
            if not csv_path:
                return None
        else:
            # 使用提供的CSV路径
            ui.print_info(f"📄 使用指定CSV文件: {os.path.basename(csv_path)}")
        # 检查输出CSV文件
        if output_csv is None:
            output_csv = translator._generate_output_path(csv_path)
            ui.print_info(f"📄 自动生成输出CSV文件: {os.path.basename(output_csv)}")
        else:
            # 使用提供的输出CSV路径
            ui.print_info(f"📄 使用指定输出CSV文件: {os.path.basename(output_csv)}")
        # 检查是否可以恢复翻译
        resume_file = translator.can_resume_translation(csv_path, output_csv)
        if resume_file:
            ui.print_info(f"检测到可恢复的翻译文件: {resume_file}")
            ui.print_info("自动恢复翻译...")
            success = translator.resume_translation(
                csv_path, resume_file, "protected_text"
            )
            if success:
                # 断点续传未走「保护→翻译→恢复」全流程，此处补做占位符恢复：(PH_1) -> [saw] 等
                try:
                    placeholder_manager = translator.factory.create_dictionary_translator("adult")
                    _, placeholder_map, _ = placeholder_manager.translate_csv(csv_path, mode="protect")
                    restore_ok, _, _ = placeholder_manager.translate_csv(
                        resume_file, mode="restore", placeholder_map=placeholder_map
                    )
                    if restore_ok:
                        ui.print_success("占位符已恢复（(PH_1) 等已还原为 [saw] 等）")
                    else:
                        ui.print_warning("占位符恢复未完全成功，可稍后使用「仅恢复翻译列占位符」再试")
                except Exception as e:
                    logger.warning("断点续传后占位符恢复失败: %s", e)
                    ui.print_warning("占位符未自动恢复，请使用「仅恢复翻译列占位符」手动恢复")
                ui.print_success("恢复翻译完成！")
                # 将输出CSV加入"导入翻译"的历史
                PathManager().remember_path("import_csv", resume_file)
                return resume_file  # 翻译完成，返回输出文件路径
            else:
                return None  # 翻译未完成（用户中断）

        # 实际将使用的翻译器（与自动选择顺序一致）
        actual_translator = (
            "google"
            if "google" in available_translators
            else "java"
            if "java" in available_translators
            else "python"
        )

        # 显示翻译配置（与真实使用的翻译器一致）
        ui.print_section_header("翻译配置", ui.Icons.SETTINGS)
        ui.print_key_value("输入文件", os.path.basename(csv_path), ui.Icons.FILE)
        ui.print_key_value("输出文件", os.path.basename(output_csv), ui.Icons.FILE)
        translator_label = (
            "Google翻译器"
            if actual_translator == "google"
            else "Java翻译器"
            if actual_translator == "java"
            else "Python翻译器"
        )
        ui.print_key_value("翻译器", translator_label, ui.Icons.SETTINGS)

        # 显示翻译器特性（简化版）
        if actual_translator == "google":
            ui.print_info("🌐 Google 翻译: 免费，无需 API 密钥")
        elif actual_translator == "java":
            ui.print_info("🚀 Java翻译器: 高性能，支持中断和恢复")
        else:
            ui.print_info("🐍 Python翻译器: 简单部署，稳定可靠")

        ui.print_section_header("开始翻译", ui.Icons.TRANSLATE)

        # 仅在使用 Java/Python 时检查阿里云 API；Google 无需 API
        if actual_translator in ("java", "python"):
            try:
                from user_config import UserConfigManager

                config_manager = UserConfigManager()
                api_manager = config_manager.api_manager
                primary_api = api_manager.get_primary_api()

                if not primary_api or not primary_api.is_enabled():
                    ui.print_error("未找到启用的翻译API配置")
                    ui.print_info("请先配置翻译API：")
                    ui.print_info("1. 运行主程序选择'配置管理'")
                    ui.print_info("2. 选择'API配置'进行设置")
                    ui.print_info("3. 配置并启用至少一个翻译API")
                    return None

                if not primary_api.validate():
                    ui.print_error(f"{primary_api.name}配置不完整或无效")
                    ui.print_info("请检查API配置中的必需字段")
                    return None

                ui.print_info(f"🌐 使用翻译API: {primary_api.name}")

            except Exception as e:
                ui.print_error(f"加载翻译API配置失败: {str(e)}")
                ui.print_info("请检查配置系统是否正常工作")
                return None
        else:
            ui.print_info("🌐 使用翻译API: Google 翻译（免费）")

        # Google 翻译：后台线程「按 Enter 暂停」，当前块写盘后生效
        if actual_translator == "google":
            pause_flag = Path(output_csv).parent / "translate_pause.flag"

            def wait_pause():
                try:
                    input("按 Enter 暂停翻译（当前块完成后生效） ")
                except (EOFError, KeyboardInterrupt):
                    return
                try:
                    pause_flag.touch()
                except OSError:
                    pass

            pause_thread = threading.Thread(target=wait_pause, daemon=True)
            pause_thread.start()

        # 执行翻译
        try:
            success = translator.translate_csv(csv_path, output_csv, translator_type)
            if success:
                ui.print_success(f"翻译完成：{output_csv}")
                return output_csv  # 翻译完成，返回输出文件路径
            else:
                ui.print_warning("翻译未完成、已暂停或已中断，可重新运行翻译以继续")
                return None  # 翻译未完成
        except Exception as e:
            ui.print_error(f"翻译失败: {str(e)}")
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
