"""
模板管理器 - 负责翻译模板的完整生命周期管理，包括提取、生成、导入和验证
"""
import logging
import csv
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from tqdm import tqdm
from colorama import Fore, Style
from day_translation.extract.extractors import extract_keyed_translations, scan_defs_sync, extract_definjected_translations
from day_translation.extract.generators import TemplateGenerator
from day_translation.extract.exporters import export_definjected_with_original_structure, export_definjected_with_defs_structure, export_definjected_with_file_structure, export_keyed_template
from day_translation.utils.config import get_config
from day_translation.utils.utils import XMLProcessor, get_language_folder_path
import xml.etree.ElementTree as ET
from day_translation.utils.filters import ContentFilter
from day_translation.extract.smart_merger import SmartMerger

CONFIG = get_config()

class TemplateManager:
    """翻译模板管理器，负责模板的完整生命周期管理"""

    def __init__(self, mod_dir: str, language: str = CONFIG.default_language, template_location: str = "mod"):
        """
        初始化模板管理器

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言
            template_location (str): 模板位置        """
        self.mod_dir = Path(mod_dir)
        self.language = language
        self.template_location = template_location
        self.generator = TemplateGenerator(str(self.mod_dir), language, template_location)
        self.processor = XMLProcessor()

    def extract_and_generate_templates(self, output_dir: Optional[str] = None, en_keyed_dir: Optional[str] = None, data_source_choice: str = 'defs_only',template_structure: str = 'defs_structure') -> List[Tuple[str, str, str, str]]:
        """
        提取翻译数据并生成模板，同时导出CSV

        Args:
            output_dir (str): 输出目录路径
            en_keyed_dir (str): 英文Keyed目录路径（可选）
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
        translations = self._extract_all_translations(data_source_choice=data_source_choice)

        if not translations:
            logging.warning("未找到任何翻译数据")
            print(f"{Fore.YELLOW}⚠️ 未找到任何翻译数据{Style.RESET_ALL}")
            return []

        # 步骤3：根据用户选择的输出模式生成翻译模板
        self._generate_templates_to_output_dir_with_structure(translations, output_dir, template_structure=template_structure)

        # 步骤4：导出CSV到输出目录
        if output_dir:
            csv_path = os.path.join(output_dir, "translations.csv")
            self._save_translations_to_csv(translations, csv_path)
            print(f"{Fore.GREEN}✅ CSV文件已生成: {csv_path}{Style.RESET_ALL}")

        logging.info("模板生成完成，总计 %s 条翻译", len(translations))
        print(f"{Fore.GREEN}✅ 提取完成：{len(translations)} 条{Style.RESET_ALL}")
        return translations

    def _extract_all_translations(self, data_source_choice: str = "defs", direct_dir: str = None) -> List[Tuple[str, str, str, str]]:
        """
        提取所有翻译数据

        Args:
            data_source_choice (str): 数据来源选择 ('definjected_only', 'defs_only', 'merge_sources')
            direct_dir (str): 直接指定DefInjected目录路径，用于从输出目录提取现有翻译

        Returns:
            List[Tuple[str, str, str, str]]: 翻译数据列表
        """
        translations = []
        
        # 提取Keyed翻译（总是提取）
        print(f"📊 正在扫描 Keyed 翻译...")
        keyed_translations = extract_keyed_translations(str(self.mod_dir), CONFIG.source_language)
        translations.extend(keyed_translations)
        print(f"   ✅ 提取到 {len(keyed_translations)} 条 Keyed 翻译")
        logging.debug("提取到 %s 条 Keyed 翻译", len(keyed_translations))

        if data_source_choice == "definjected_only":
            logging.info("从英文 DefInjected 目录提取翻译数据")
            print(f"📊 正在扫描英文 DefInjected 目录提取翻译...")
            # 从模组的英文DefInjected目录提取翻译数据
            definjected_translations = extract_definjected_translations(str(self.mod_dir), CONFIG.source_language, direct_dir=direct_dir)
            translations.extend(definjected_translations)
            print(f"   ✅ 提取到 {len(definjected_translations)} 条 DefInjected 翻译")
            logging.debug("从英文DefInjected提取到 %s 条翻译", len(definjected_translations))

        elif data_source_choice == "defs_only":
            print(f"📊 正在扫描 Defs 目录...")
            defs_translations = scan_defs_sync(str(self.mod_dir), language=CONFIG.source_language)
            translations.extend(defs_translations)
            print(f"   ✅ 提取到 {len(defs_translations)} 条 DefInjected 翻译")
            logging.debug("提取到 %s 条 DefInjected 翻译", len(defs_translations))

        elif data_source_choice == "merge_sources":
            # 5.1合并提取逻辑：从选择的数据源提取新数据，与输出目录现有文件合并
            logging.info("执行5.1合并提取逻辑")
            print(f"🔄 正在执行5.1合并提取逻辑...")
            
            # 这里应该由外部调用者决定使用哪种数据源
            # merge_sources模式实际上是一个占位符，真正的合并在extract_with_merge_logic中处理
            pass

        return translations

    def _generate_templates_to_output_dir_with_structure(self, translations: List[Tuple[str, str, str, str]], output_dir: str, template_structure: str):
        """在指定输出目录生成翻译模板结构（完全复用原有逻辑）"""
        output_path = Path(output_dir)

        # 分离Keyed和DefInjected翻译
        # 改进分离逻辑：同时支持两种数据格式
        keyed_translations = []
        def_translations = []
        
        for k, t, g, f in translations:
            # 判断是否为DefInjected翻译的规则：
            # 1. key包含'/'（scan_defs_sync格式）：如 "ThingDef/Apparel_Pants.label"
            # 2. key包含'.'且file_path是DefInjected相关（extract_definjected_translations格式）：如 "Apparel_Pants.label"
            # 3. 或者根据tag和file_path判断
            if '/' in k:
                # scan_defs_sync格式：包含Def类型前缀
                def_translations.append((k, t, g, f))
            elif '.' in k and (f.endswith('.xml') or 'DefInjected' in str(f)):
                # extract_definjected_translations格式：key包含点号且来自DefInjected文件
                def_translations.append((k, t, g, f))
            else:
                # Keyed翻译：不包含'/'和'.'，或者来自Keyed文件
                keyed_translations.append((k, t, g, f))

        # 生成Keyed模板 - 使用exporters.py中的函数
        if keyed_translations:
            print(f"📁 正在生成 Keyed 模板...")
            export_keyed_template(
                mod_dir=str(self.mod_dir),
                export_dir=str(output_path),
                selected_translations=keyed_translations,
                language=self.language
            )
            logging.info("生成 %s 条 Keyed 模板到 %s", len(keyed_translations), output_path)
            print(f"   ✅ Keyed 模板已生成: {output_path}")
        
        # 生成DefInjected模板 - 完全复用exporters.py中的函数
        if def_translations:
            print(f"📁 正在生成 DefInjected 模板...")
            self._generate_definjected_with_structure(def_translations, str(output_path), template_structure)

    def _generate_definjected_with_structure(self, def_translations: List[Tuple[str, str, str, str]], export_dir: str, template_structure: str):
        """根据智能配置的结构选择生成DefInjected模板，直接调用对应的export函数"""
        if template_structure == 'original_structure':
            # 使用原有结构的导出函数
            export_definjected_with_original_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（保持原结构）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（保持原结构）")
        elif template_structure == 'defs_by_type':
            # 需要实现按DefType分组的导出函数
            export_definjected_with_defs_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（按DefType分组）")
        elif template_structure == 'defs_by_file_structure':
            # 需要实现按文件结构的导出函数
            export_definjected_with_file_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（按文件结构）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（按文件结构）")
        else:
            # 默认使用按DefType分组
            export_definjected_with_defs_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（默认分组）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（默认分组）")

    def _save_translations_to_csv(self, translations: List[Tuple[str, str, str, str]], csv_path: str):
        """保存翻译数据到CSV文件"""
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])
            writer.writerows(translations)

        logging.info("翻译数据已保存到CSV: %s", csv_path)