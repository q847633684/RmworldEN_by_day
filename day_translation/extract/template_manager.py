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
from day_translation.extract.exporters import handle_extract_translate, export_definjected_with_original_structure, export_definjected_with_defs_structure, export_definjected
from day_translation.utils.config import get_config
from day_translation.utils.utils import XMLProcessor, get_language_folder_path
import xml.etree.ElementTree as ET
from day_translation.utils.filters import ContentFilter

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

    def extract_and_generate_templates(self, output_dir: Optional[str] = None, en_keyed_dir: Optional[str] = None, auto_choose_definjected: bool = False) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译数据并生成模板，同时导出CSV

        Args:
            output_dir (str): 输出目录路径
            en_keyed_dir (str): 英文Keyed目录路径（可选）
            auto_choose_definjected (bool): 是否自动选择DefInjected提取方式

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
        # - auto_choose=True: 使用"definjected"模式（从英文DefInjected目录提取）
        # - auto_choose=False: 使用"defs"模式（从Defs目录扫描提取）
        if auto_choose_definjected:
            definjected_extract_mode = "definjected"
        else:
            definjected_extract_mode = "defs"

        # 步骤2：提取翻译数据
        # 根据选择的模式提取Keyed和DefInjected翻译数据
        # 返回格式：[(key, text, group, file_info), ...]
        translations = self._extract_all_translations(definjected_mode=definjected_extract_mode)

        # 数据有效性检查：如果没有提取到任何翻译数据，记录警告并返回空列表
        if not translations:
            logging.warning("未找到任何翻译数据")
            print(f"{Fore.YELLOW}⚠️ 未找到任何翻译数据{Style.RESET_ALL}")
            return []

              # 步骤3：根据用户选择的输出模式生成翻译模板
        #
        # 【统一输出模式说明】
        # 智能流程总是会提供正确的output_dir，无论是外部目录还是内部目录
        # 统一使用_generate_templates_to_output_dir_with_structure处理
        self._generate_templates_to_output_dir_with_structure(translations, output_dir, template_structure="defs_structure")

        # 步骤4：导出CSV到输出目录
        # 只有指定了输出目录才生成CSV文件，方便后续翻译和导入操作
        if output_dir:
            csv_path = os.path.join(output_dir, "translations.csv")
            self._save_translations_to_csv(translations, csv_path)
            print(f"{Fore.GREEN}✅ CSV文件已生成: {csv_path}{Style.RESET_ALL}")

        # 记录完成状态并向用户显示结果统计
        logging.info("模板生成完成，总计 %s 条翻译", len(translations))
        print(f"{Fore.GREEN}✅ 提取完成：{len(translations)} 条{Style.RESET_ALL}")

        # 返回提取到的翻译数据，供调用方进一步处理（如机器翻译、导入等）
        return translations

    def import_translations(self, csv_path: str, merge: bool = True, auto_create_templates: bool = True) -> bool:
        """
        将翻译CSV导入到翻译模板

        Args:
            csv_path (str): 翻译CSV文件路径
            merge (bool): 是否合并现有翻译
            auto_create_templates (bool): 是否自动创建模板

        Returns:
            bool: 导入是否成功
        """
        logging.info("开始导入翻译到模板: %s", csv_path)

        try:
            # 步骤1：确保翻译模板存在
            if auto_create_templates:
                if not self.ensure_templates_exist():
                    logging.error("无法创建翻译模板")
                    print(f"{Fore.RED}❌ 无法创建翻译模板{Style.RESET_ALL}")
                    return False

            # 步骤2：验证CSV文件
            if not self._validate_csv_file(csv_path):
                return False

            # 步骤3：加载翻译数据
            translations = self._load_translations_from_csv(csv_path)
            if not translations:
                return False

            # 步骤4：更新XML文件
            updated_count = self._update_all_xml_files(translations, merge)

            # 步骤5：验证导入结果
            success = self._verify_import_results()

            if success:
                logging.info("翻译导入到模板完成，更新了 %s 个文件", updated_count)
                print(f"{Fore.GREEN}✅ 翻译已成功导入到模板{Style.RESET_ALL}")
            else:
                logging.warning("翻译导入可能存在问题")
                print(f"{Fore.YELLOW}⚠️ 翻译导入完成，但可能存在问题{Style.RESET_ALL}")

            return success

        except Exception as e:
            logging.error("导入翻译时发生错误: %s", e, exc_info=True)
            print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")
            return False

    def ensure_templates_exist(self) -> bool:
        """
        确保翻译模板存在，如果不存在则自动创建

        Returns:
            bool: 模板是否存在或创建成功
        """
        template_dir = self.mod_dir / "Languages" / self.language

        if template_dir.exists():
            logging.debug("翻译模板目录已存在")
            return True

        logging.info("翻译模板不存在，正在自动创建...")
        translations = self.extract_and_generate_templates()
        return len(translations) > 0

    def _extract_all_translations(self, definjected_mode: str = "defs", direct_dir: str = None) -> List[Tuple[str, str, str, str]]:
        """
        提取所有翻译数据

        Args:
            definjected_mode (str): DefInjected 提取模式 ('definjected' 或 'defs')
            direct_dir (str): 直接指定DefInjected目录路径，用于从输出目录提取现有翻译

        Returns:
            List[Tuple[str, str, str, str]]: 翻译数据列表
        """
        translations = []

        # 提取Keyed翻译
        print(f"📊 正在提取 Keyed 翻译...")
        keyed_translations = extract_keyed_translations(str(self.mod_dir), CONFIG.source_language)
        translations.extend(keyed_translations)
        print(f"   ✅ 提取到 {len(keyed_translations)} 条 Keyed 翻译")
        logging.debug("提取到 %s 条 Keyed 翻译", len(keyed_translations))

        # 根据模式提取DefInjected翻译
        #
        # 【两种提取模式的区别】
        if definjected_mode == "definjected":
            # 模式1："definjected" - 以英文DefInjected为基础
            #
            # 工作原理：
            # 1. 用户在 handle_extract_translate 中选择"以英文DefInjected为基础"
            # 2. 直接从模组的英文DefInjected目录提取翻译数据
            # 3. 保持与原模组相同的翻译结构，兼容性好
            #
            # 优势：基于现有的翻译结构，避免重复劳动
            # 适用：模组已有完整的英文DefInjected，结构稳定
            logging.info("从英文 DefInjected 目录提取翻译数据")
            print(f"📊 正在从 DefInjected 目录提取翻译...")
            # 从模组的英文DefInjected目录提取翻译数据
            definjected_translations = extract_definjected_translations(str(self.mod_dir), CONFIG.source_language, direct_dir=direct_dir)
            translations.extend(definjected_translations)
            print(f"   ✅ 提取到 {len(definjected_translations)} 条 DefInjected 翻译")
            logging.debug("从英文DefInjected提取到 %s 条翻译", len(definjected_translations))

        elif definjected_mode == "defs":
            # 模式2："defs" - 从Defs目录全量提取
            #
            # 工作原理：
            # 1. 扫描模组的Defs目录下所有XML定义文件
            # 2. 解析每个定义，提取所有可翻译的字段（label, description等）
            # 3. 生成完整的DefInjected翻译条目
            #
            # 优势：确保所有可翻译内容都被提取，不会遗漏
            # 适用：首次翻译、英文DefInjected不完整、模组结构有更新
            print(f"📊 正在扫描 Defs 目录...")
            defs_translations = scan_defs_sync(str(self.mod_dir), language=CONFIG.source_language)
            translations.extend(defs_translations)
            print(f"   ✅ 提取到 {len(defs_translations)} 条 DefInjected 翻译")
            logging.debug("提取到 %s 条 DefInjected 翻译", len(defs_translations))

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

        # 生成Keyed模板 - 完全复用generators.py中的函数
        if keyed_translations:
            print(f"📁 正在生成 Keyed 模板...")
            # 临时修改TemplateGenerator的template_location为"export"，确保能正确处理外部目录
            original_template_location = self.generator.template_location
            self.generator.template_location = "export"
            try:
                # 复用generators.py中的generate_keyed_template_from_data函数，参数名为export_dir
                self.generator.generate_keyed_template_from_data(keyed_translations, export_dir=str(output_path))
                logging.info("生成 %s 条 Keyed 模板到 %s", len(keyed_translations), output_path)
                print(f"   ✅ Keyed 模板已生成: {output_path}")
            finally:
                # 恢复原来的template_location
                self.generator.template_location = original_template_location
        
        # 生成DefInjected模板 - 完全复用exporters.py中的函数
        if def_translations:
            print(f"📁 正在生成 DefInjected 模板...")
            self._generate_definjected_with_structure(def_translations, str(output_path), template_structure)

    def _generate_definjected_with_structure(self, def_translations: List[Tuple[str, str, str, str]], export_dir: str, template_structure: str):
        """根据智能配置的结构选择生成DefInjected模板，直接调用对应的export函数"""
        if template_structure == 'original_structure':
            # 保持原英文DefInjected结构 - 复用export_definjected_with_original_structure
            export_definjected_with_original_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（保持原结构）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（保持原结构）")
        elif template_structure == 'defs_structure':
            # 按原Defs目录结构生成 - 复用export_definjected_with_defs_structure
            export_definjected_with_defs_structure(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（按Defs结构）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（按Defs结构）")
        else:
            # 默认：按DefType自动分组 - 复用export_definjected
            export_definjected(
                mod_dir=str(self.mod_dir),
                export_dir=export_dir,
                selected_translations=def_translations,
                language=self.language
            )
            logging.info("生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations))
            print(f"   ✅ DefInjected 模板已生成（按DefType分组）")

    def _save_translations_to_csv(self, translations: List[Tuple[str, str, str, str]], csv_path: str):
        """保存翻译数据到CSV文件"""
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])
            writer.writerows(translations)

        logging.info("翻译数据已保存到CSV: %s", csv_path)

    def _validate_csv_file(self, csv_path: str) -> bool:
        """验证CSV文件"""
        if not Path(csv_path).is_file():
            logging.error("CSV文件不存在: %s", csv_path)
            return False

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header or not all(col in header for col in ["key", "text"]):
                    logging.error("CSV文件格式无效：缺少必要的列")
                    return False
                return True
        except Exception as e:
            logging.error("验证CSV文件时发生错误: %s", e)
            return False

    def _load_translations_from_csv(self, csv_path: str) -> Dict[str, str]:
        """从CSV文件加载翻译数据"""
        translations = {}
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["key"] and row["text"]:
                        translations[row["key"]] = row["text"]
            return translations
        except Exception as e:
            logging.error("加载CSV文件时发生错误: %s", e)
            print(f"{Fore.RED}❌ 加载CSV文件失败: {e}{Style.RESET_ALL}")
            return {}

    def _update_all_xml_files(self, translations: Dict[str, str], merge: bool = True) -> int:
        """更新所有XML文件中的翻译"""
        language_dir = get_language_folder_path(self.language, str(self.mod_dir))
        updated_count = 0

        for xml_file in Path(language_dir).rglob("*.xml"):
            try:
                tree = self.processor.parse_xml(str(xml_file))
                if tree is None:
                    continue

                if self.processor.update_translations(tree, translations, merge=merge):
                    self.processor.save_xml(tree, str(xml_file))
                    updated_count += 1
                    print(f"{Fore.GREEN}更新文件: {xml_file}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}处理文件失败: {xml_file}: {e}{Style.RESET_ALL}")

        return updated_count

    def _verify_import_results(self) -> bool:
        """验证导入结果"""
        template_dir = self.mod_dir / "Languages" / self.language

        if not template_dir.exists():
            logging.error("导入后模板目录不存在")
            return False
              # 检查是否有翻译文件
        has_keyed = any((template_dir / "Keyed").glob("*.xml")) if (template_dir / "Keyed").exists() else False
        has_definjected = any((template_dir / "DefInjected").glob("**/*.xml")) if (template_dir / "DefInjected").exists() else False

        if not has_keyed and not has_definjected:
            logging.warning("导入后未找到翻译文件")
            return False

        logging.info("导入结果验证通过")
        return True