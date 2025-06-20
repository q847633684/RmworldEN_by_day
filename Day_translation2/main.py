"""
Day Translation 2 - 主程序入口

游戏本地化翻译工具的主程序，提供完整的翻译工作流程。
遵循提示文件标准：接口兼容、用户友好、渐进式迁移。
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("day_translation2.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# 添加当前目录到sys.path以支持模块导入
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from config import get_config
from core.translation_facade import TranslationFacade
from interaction.interaction_manager import UnifiedInteractionManager
from models.exceptions import ConfigError, TranslationError


def main() -> None:
    """主程序入口"""
    try:
        print("=== Day Translation 2 - 游戏本地化翻译工具 ===\n")

        # 加载配置
        config = get_config()
        logging.info("Day Translation 2 启动")

        # 创建交互管理器
        interaction_manager = UnifiedInteractionManager()

        # 显示主菜单并处理用户选择
        while True:
            try:
                choice = interaction_manager.show_main_menu()

                if choice == "quit":
                    print("感谢使用 Day Translation 2！")
                    break
                elif choice == "extraction":
                    handle_extraction_mode(interaction_manager)
                elif choice == "import":
                    handle_import_mode(interaction_manager)
                elif choice == "translation":
                    handle_translation_mode(interaction_manager)
                elif choice == "corpus":
                    handle_corpus_mode(interaction_manager)
                elif choice == "batch":
                    handle_batch_mode(interaction_manager)
                elif choice == "config":
                    handle_config_mode(interaction_manager)
                else:
                    print(f"未知选择: {choice}")

            except KeyboardInterrupt:
                print("\n用户中断操作")
                break
            except Exception as e:
                logging.error(f"处理用户选择时发生错误: {e}")
                print(f"发生错误: {e}")
                print("请重试或联系技术支持")

    except ConfigError as e:
        logging.error(f"配置错误: {e}")
        print(f"配置错误: {e}")
        print("请检查配置文件或重新配置")
        sys.exit(1)
    except Exception as e:
        logging.error(f"程序启动失败: {e}")
        print(f"程序启动失败: {e}")
        sys.exit(1)


def handle_extraction_mode(interaction_manager: UnifiedInteractionManager) -> None:
    """处理提取模式"""
    try:
        print("\n=== 提取翻译模板 ===")

        # 获取用户输入
        params = interaction_manager.get_extraction_parameters()

        if not params:
            print("提取操作已取消")
            return

        # 创建翻译门面
        facade = TranslationFacade(
            mod_dir=params["mod_dir"],
            language=params.get("language"),
            template_location=params.get("template_location", "mod"),
        )

        # 执行提取
        result = facade.extract_templates_and_generate_csv(
            output_dir=params["output_dir"],
            en_keyed_dir=params.get("en_keyed_dir"),
            auto_choose_definjected=params.get("auto_choose_definjected", False),
            structure_choice=params.get("structure_choice", "original"),
            merge_mode=params.get("merge_mode", "smart-merge"),
        )

        # 显示结果
        interaction_manager.show_operation_result(result)

    except Exception as e:
        logging.error(f"提取模式处理失败: {e}")
        print(f"提取失败: {e}")


def handle_import_mode(interaction_manager: UnifiedInteractionManager) -> None:
    """处理导入模式"""
    try:
        print("\n=== 导入翻译 ===")

        # 获取用户输入
        params = interaction_manager.get_import_parameters()

        if not params:
            print("导入操作已取消")
            return

        # 创建翻译门面
        facade = TranslationFacade(
            mod_dir=params["mod_dir"],
            language=params.get("language"),
            template_location=params.get("template_location", "mod"),
        )

        # 执行导入
        result = facade.import_translations_to_templates(
            csv_path=params["csv_path"], merge=params.get("merge", True)
        )

        # 显示结果
        interaction_manager.show_operation_result(result)

    except Exception as e:
        logging.error(f"导入模式处理失败: {e}")
        print(f"导入失败: {e}")


def handle_translation_mode(interaction_manager: UnifiedInteractionManager) -> None:
    """处理翻译模式"""
    try:
        print("\n=== 机器翻译 ===")

        # 获取用户输入
        params = interaction_manager.get_translation_parameters()

        if not params:
            print("翻译操作已取消")
            return

        # 导入机器翻译服务
        from .services.translation_service import MachineTranslateService

        # 创建翻译服务
        translate_service = MachineTranslateService()

        # 执行翻译
        result = translate_service.translate_csv(
            csv_path=params["csv_path"],
            output_path=params.get("output_path"),
            source_language=params.get("source_language", "English"),
            target_language=params.get("target_language", "ChineseSimplified"),
        )

        # 显示结果
        interaction_manager.show_operation_result(result)

    except Exception as e:
        logging.error(f"翻译模式处理失败: {e}")
        print(f"翻译失败: {e}")


def handle_corpus_mode(interaction_manager: UnifiedInteractionManager) -> None:
    """处理语料生成模式"""
    try:
        print("\n=== 生成平行语料 ===")

        # 获取用户输入
        params = interaction_manager.get_corpus_parameters()

        if not params:
            print("语料生成操作已取消")
            return

        # 创建翻译门面
        facade = TranslationFacade(
            mod_dir=params["mod_dir"],
            language=params.get("language"),
            template_location=params.get("template_location", "mod"),
        )

        # 生成语料
        result = facade.generate_corpus()

        # 显示结果
        interaction_manager.show_operation_result(result)

    except Exception as e:
        logging.error(f"语料生成模式处理失败: {e}")
        print(f"语料生成失败: {e}")


def handle_batch_mode(interaction_manager: UnifiedInteractionManager) -> None:
    """处理批量处理模式"""
    try:
        print("\n=== 批量处理 ===")

        # 获取用户输入
        params = interaction_manager.get_batch_parameters()

        if not params:
            print("批量处理操作已取消")
            return

        # 导入批量处理服务
        from .services.batch_processor import BatchProcessor

        # 创建批量处理器
        batch_processor = BatchProcessor(
            max_workers=params.get("max_workers", 10),
            timeout=params.get("timeout", 300),
        )

        # 执行批量处理
        result = batch_processor.process_multiple_mods(
            mod_list=params["mod_list"],
            csv_path=params.get("csv_path"),
            language=params.get("language"),
        )

        # 显示结果
        interaction_manager.show_operation_result(result)

    except Exception as e:
        logging.error(f"批量处理模式处理失败: {e}")
        print(f"批量处理失败: {e}")


def handle_config_mode(interaction_manager: UnifiedInteractionManager) -> None:
    """处理配置模式"""
    try:
        print("\n=== 配置管理 ===")

        # 显示配置菜单
        interaction_manager.show_config_menu()

    except Exception as e:
        logging.error(f"配置模式处理失败: {e}")
        print(f"配置管理失败: {e}")


if __name__ == "__main__":
    main()
