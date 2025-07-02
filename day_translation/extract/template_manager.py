"""
模板管理器 - 负责翻译模板的完整生命周期管理，包括提取、生成、导入和验证
"""

import logging
import csv
import os
from pathlib import Path
from typing import List, Tuple, Optional, TYPE_CHECKING
from colorama import Fore, Style
from day_translation.extract.extractors import (
    extract_keyed_translations,
    scan_defs_sync,
    extract_definjected_translations,
)
from day_translation.extract.exporters import (
    export_definjected_with_original_structure,
    export_definjected_with_defs_structure,
    export_definjected_with_file_structure,
    export_keyed_template,
)
from day_translation.utils.config import get_config

if TYPE_CHECKING:
    from typing_extensions import Literal
CONFIG = get_config()


class TemplateManager:
    """翻译模板管理器，负责模板的完整生命周期管理"""

    def __init__(
        self,
        mod_dir: str,
        language: str = CONFIG.default_language,
        template_location: str = "mod",
    ):
        """
        初始化模板管理器

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言
            template_location (str): 模板位置"""
        self.mod_dir = Path(mod_dir)
        self.language = language
        self.template_location = template_location

    def extract_and_generate_templates(
        self,
        output_dir: Optional[str] = None,
        data_source_choice: str = "defs_only",
        template_structure: str = "defs_structure",
    ) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译数据并生成模板，同时导出CSV

        Args:
            output_dir (str): 输出目录路径
            data_source_choice (str): 数据来源选择 ('definjected_only' 或 'defs_only')

        Returns:
            List[Tuple[str, str, str, str]]: 提取的翻译数据
        """
        # 记录操作开始，便于调试和跟踪处理流程
        logging.info("开始提取翻译数据并生成模板")

        # 步骤1：智能选择DefInjected提取方式
        #
        # 【背景说明】
        # RimWorld模组有两种DefInjected数据来源：
        # 1. 英文DefInjected目录：ModDir/Languages/English/DefInjected/
        #    - 这是模组作者手工整理的翻译结构，通常更精确
        #    - 适合已有翻译基础的情况，保持结构一致性
        #
        # 2. Defs目录：ModDir/Defs/
        #    - 这是模组的原始定义文件，包含所有可翻译字段
        #    - 适合首次翻译或结构有变动的情况，确保完整性
        #
        # 【智能选择逻辑】
        # - data_source_choice: 数据来源选择（'definjected_only', 'defs_only', 'both'）
        # - data_source_choice='definjected_only': 使用"definjected"模式（从英文DefInjected目录提取）
        # - data_source_choice='defs_only': 使用"defs"模式（从Defs目录扫描提取）
        # 步骤2：提取翻译数据
        translations = self.extract_all_translations(
            data_source_choice=data_source_choice,
        )

        if not translations:
            logging.warning("未找到任何翻译数据")
            print(f"{Fore.YELLOW}⚠️ 未找到任何翻译数据{Style.RESET_ALL}")
            return []

        # 步骤3：根据用户选择的输出模式生成翻译模板
        if output_dir:
            self._generate_templates_to_output_dir_with_structure(
                translations, output_dir, template_structure=template_structure
            )

        # 步骤4：导出CSV到输出目录
        if output_dir:
            csv_path = os.path.join(output_dir, "translations.csv")
            self._save_translations_to_csv(translations, csv_path)
            logging.info("翻译数据已保存到CSV: %s", csv_path)
            print(f"{Fore.GREEN}✅ CSV文件已生成: {csv_path}{Style.RESET_ALL}")

        logging.info("模板生成完成，总计 %s 条翻译", len(translations))
        print(f"{Fore.GREEN}✅ 提取完成：{len(translations)} 条{Style.RESET_ALL}")
        return translations

    def extract_all_translations(
        self,
        data_source_choice: str = "defs",
        language: str = CONFIG.source_language,
    ):
        """
        提取所有翻译数据
        Args:
            data_source_choice (str): 数据来源选择 ('definjected_only', 'defs_only')
            language (str): 目标语言代码

        Returns:
            返回五元组 (key, test, tag, rel_path, en_test)

            提取参数说明：
                extract_keyed_translations: 提取 Keyed 翻译
                scan_defs_sync: 扫描 Defs 目录中的可翻译内容
                extract_definjected_translations: 从 DefInjected 目录提取翻译结构
        """
        # 提取Keyed翻译（总是提取）
        logging.info("正在扫描 Keyed 目录...")
        print(f"{Fore.GREEN}📊 正在扫描 Keyed 目录...{Style.RESET_ALL}")
        keyed_translations = extract_keyed_translations(str(self.mod_dir), language)
        print(f"   ✅ 从Keyed 目录提取到 {len(keyed_translations)} 条 Keyed 翻译")
        logging.info("从Keyed 目录提取到 %s 条 Keyed 翻译", len(keyed_translations))

        if data_source_choice == "definjected_only":
            logging.info("正在扫描 DefInjected 目录...")
            print(f"{Fore.GREEN}📊 正在扫描 DefInjected 目录...{Style.RESET_ALL}")
            # 从DefInjected目录提取翻译数据
            definjected_translations = extract_definjected_translations(
                str(self.mod_dir), language
            )

            # 现在总是返回五元组，需要将Keyed也转换为五元组保持一致性
            keyed_as_five = [
                (k, t, g, f, t)  # en_test用test填充
                for k, t, g, f in keyed_translations
            ]
            print(
                f"   ✅ 从DefInjected 目录提取到 {len(definjected_translations)} 条 DefInjected 翻译"
            )
            logging.info(
                "从DefInjected 目录提取到 %s 条 DefInjected 翻译",
                len(definjected_translations),
            )
            return keyed_as_five + definjected_translations  # type: ignore

        elif data_source_choice == "defs_only":
            logging.info("正在扫描 Defs 目录...")
            print(f"{Fore.GREEN}📊 正在扫描 Defs 目录...{Style.RESET_ALL}")
            defs_translations = scan_defs_sync(str(self.mod_dir))

            # defs_translations 总是四元组，需要转换为五元组
            keyed_as_five = [
                (k, t, g, f, t)
                for k, t, g, f in keyed_translations  # en_test用test填充
            ]
            defs_as_five = [
                (k, t, g, f, t) for k, t, g, f in defs_translations  # en_test用test填充
            ]
            print(f"   ✅ 从Defs目录提取到 {len(defs_translations)} 条 Defs 翻译")
            logging.info("从Defs目录提取到 %s 条 Defs 翻译", len(defs_translations))
            return keyed_as_five + defs_as_five

        # 如果到了这里，说明没有匹配的data_source_choice
        logging.warning("未知的data_source_choice: %s", data_source_choice)
        return []

    def _generate_templates_to_output_dir_with_structure(
        self, translations: list, output_dir: str, template_structure: str
    ):
        """在指定输出目录生成翻译模板结构（完全复用原有逻辑）"""
        output_path = Path(output_dir)

        # 分离Keyed和DefInjected翻译
        # 改进分离逻辑：同时支持两种数据格式
        keyed_translations = []
        def_translations = []

        for item in translations:
            k, _, _, f = item[:4]  # 兼容五元组和四元组
            # 判断是否为DefInjected翻译的规则：
            # 1. key包含'/'（scan_defs_sync格式）：如 "ThingDef/Apparel_Pants.label"
            # 2. key包含'.'且file_path是DefInjected相关（extract_definjected_translations格式）：如 "Apparel_Pants.label"
            # 3. 或者根据tag和file_path判断
            if "/" in k:
                def_translations.append(item)
            elif "." in k and (f.endswith(".xml") or "DefInjected" in str(f)):
                def_translations.append(item)
            else:
                keyed_translations.append(item)

        # 生成Keyed模板 - 使用exporters.py中的函数
        if keyed_translations:
            print("📁 正在生成 Keyed 模板...")
            export_keyed_template(
                mod_dir=str(self.mod_dir),
                export_dir=str(output_path),
                selected_translations=[item[:4] for item in keyed_translations],
            )
            logging.info(
                "生成 %s 条 Keyed 模板到 %s", len(keyed_translations), output_path
            )
            print("   ✅ Keyed 模板已生成")

        # 生成DefInjected模板 - 完全复用exporters.py中的函数
        if def_translations:
            print("📁 正在生成 DefInjected 模板...")
            self._generate_definjected_with_structure(
                [item[:4] for item in def_translations],
                str(output_path),
                template_structure,
            )

    def _generate_definjected_with_structure(
        self,
        def_translations: List[Tuple[str, str, str, str]],
        export_dir: str,
        template_structure: str,
    ):
        """根据智能配置的结构选择生成DefInjected模板，直接调用对应的export函数
        1. original_structure: 使用原有结构的导出函数
        2. defs_by_type: 需要实现按DefType分组的导出函数
        3. file_by_type: 需要实现按文件分组的导出函数
        导出参数
            export_definjected_with_original_structure  按 file_path 创建目录和文件结构导出 DefInjected 翻译
            export_definjected_with_defs_structure  按照按DefType分组导出DefInjected翻译
            export_definjected_with_file_structure  按原始Defs文件目录结构导出DefInjected翻译
            export_keyed_template   导出 Keyed 翻译模板
            export_keyed    导出 Keyed 翻译，添加 EN 注释
        """
        if template_structure == "original_structure":
            # 使用原有结构的导出函数
            export_definjected_with_original_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
            )
            logging.info(
                "生成 %s 条 DefInjected 模板（保持原结构）", len(def_translations)
            )
            print("   ✅ DefInjected 模板已生成（保持原结构）")
        elif template_structure == "defs_by_type":
            # 需要实现按DefType分组的导出函数
            export_definjected_with_defs_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
            )
            logging.info(
                "生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations)
            )
            print("   ✅ DefInjected 模板已生成（按DefType分组）")
            print("   ✅ DefInjected 模板已生成（按DefType分组）")
        elif template_structure == "defs_by_file_structure":
            # 需要实现按文件结构的导出函数
            export_definjected_with_file_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
            )
            logging.info(
                "生成 %s 条 DefInjected 模板（按文件结构）", len(def_translations)
            )
            print("   ✅ DefInjected 模板已生成（按文件结构）")
        else:
            # 默认使用按DefType分组
            export_definjected_with_defs_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
            )
            logging.info(
                "生成 %s 条 DefInjected 模板（默认分组）", len(def_translations)
            )
            print("   ✅ DefInjected 模板已生成（默认分组）")

    def _save_translations_to_csv(self, translations: list, csv_path: str):
        """保存翻译数据到CSV文件"""
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])
            for item in translations:
                writer.writerow(item[:4])  # 只导出前四个字段，兼容五元组

        logging.info("翻译数据已保存到CSV: %s", csv_path)
