"""
模板管理器 - 负责翻译模板的完整生命周期管理，包括提取、生成、导入和验证
"""
import logging
import csv
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from tqdm import tqdm
from colorama import Fore, Style
from .extractors import extract_keyed_translations, scan_defs_sync, extract_definjected_translations
from .generators import TemplateGenerator
from .exporters import handle_extract_translate, export_definjected_with_original_structure, export_definjected_with_defs_structure
from ..utils.config import get_config
from ..utils.utils import XMLProcessor, get_language_folder_path, handle_exceptions

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
        
    def extract_and_generate_templates(self, output_dir: str = None, en_keyed_dir: str = None, auto_choose_definjected: bool = False) -> List[Tuple[str, str, str, str]]:
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
        # - auto_choose=True: 自动选择"defs"模式（批量处理时使用）
        # - auto_choose=False: 检测英文DefInjected目录，让用户选择最佳方式
        # - 如果有英文DefInjected: 询问用户选择基础模式还是全量模式
        # - 如果无英文DefInjected: 自动使用全量模式
        definjected_extract_mode = self._handle_definjected_extraction_choice(output_dir, auto_choose_definjected)
        
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
        # 【两种输出模式说明】
        if output_dir:
            # 外部输出模式：生成到用户指定的外部目录
            # 优势：独立管理，便于翻译工作、版本控制和分发
            # 适用：翻译团队协作、多版本管理、模组包分发
            self._generate_templates_to_output_dir(translations, output_dir, en_keyed_dir)
        else:        
            # 内部输出模式：生成到模组内部Languages目录
            # 优势：直接集成到模组中，开发和测试方便
            # 适用：模组开发、快速测试、单机使用
            self._generate_all_templates(translations, en_keyed_dir)
        
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
        
    def _extract_all_translations(self, definjected_mode: str = "defs") -> List[Tuple[str, str, str, str]]:
        """
        提取所有翻译数据
        
        Args:
            definjected_mode (str): DefInjected 提取模式 ('definjected' 或 'defs')
            
        Returns:
            List[Tuple[str, str, str, str]]: 翻译数据列表
        """
        translations = []
        
        # 提取Keyed翻译
        keyed_translations = extract_keyed_translations(str(self.mod_dir), CONFIG.source_language)
        translations.extend(keyed_translations)
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
            
            # 从模组的英文DefInjected目录提取翻译数据
            src_lang_path = get_language_folder_path(CONFIG.source_language, str(self.mod_dir))
            src_definjected_dir = Path(src_lang_path) / CONFIG.def_injected_dir
            
            if src_definjected_dir.exists():
                # 使用专门的 DefInjected 提取函数
                definjected_translations = extract_definjected_translations(str(self.mod_dir), CONFIG.source_language)
                translations.extend(definjected_translations)
                logging.debug("从英文DefInjected提取到 %s 条翻译", len(definjected_translations))
            else:
                logging.warning("英文DefInjected目录不存在: %s，回退到defs模式", src_definjected_dir)
                definjected_mode = "defs"
        
        if definjected_mode == "defs":
            # 模式2："defs" - 从Defs目录全量提取
            # 
            # 工作原理：
            # 1. 扫描模组的Defs目录下所有XML定义文件
            # 2. 解析每个定义，提取所有可翻译的字段（label, description等）
            # 3. 生成完整的DefInjected翻译条目
            # 
            # 优势：确保所有可翻译内容都被提取，不会遗漏
            # 适用：首次翻译、英文DefInjected不完整、模组结构有更新
            defs_translations = scan_defs_sync(str(self.mod_dir), language=CONFIG.source_language)
            translations.extend(defs_translations)
            logging.debug("提取到 %s 条 DefInjected 翻译", len(defs_translations))
        
        return translations
        
    def _generate_all_templates(self, translations: List[Tuple[str, str, str, str]], en_keyed_dir: str = None):
        """生成所有翻译模板"""
        # 分离Keyed和DefInjected翻译
        keyed_translations = [(k, t, g, f) for k, t, g, f in translations if '/' not in k]
        def_translations = [(k, t, g, f) for k, t, g, f in translations if '/' in k]
        
        # 生成Keyed模板
        if keyed_translations:
            if en_keyed_dir:
                self.generator.generate_keyed_template(en_keyed_dir)
            self.generator.generate_keyed_template_from_data(keyed_translations)
            logging.info("生成 %s 条 Keyed 模板", len(keyed_translations))        # 生成DefInjected模板
        if def_translations:
            try:
                self._handle_definjected_structure_choice(
                    def_translations=def_translations,
                    export_dir=str(self.mod_dir),  # 内部模式：输出到模组目录
                    is_internal_mode=True
                )
            except KeyboardInterrupt:
                # 用户选择返回，重新抛出异常
                raise
            
    def _generate_templates_to_output_dir(self, translations: List[Tuple[str, str, str, str]], output_dir: str, en_keyed_dir: str = None):
        """在指定输出目录生成翻译模板结构"""
        output_path = Path(output_dir)
        
        # 创建语言目录结构
        lang_dir = output_path / "Languages" / "ChineseSimplified"
        keyed_dir = lang_dir / "Keyed"
        definjected_dir = lang_dir / "DefInjected"
        
        # 确保目录存在
        keyed_dir.mkdir(parents=True, exist_ok=True)
        definjected_dir.mkdir(parents=True, exist_ok=True)
          # 分离Keyed和DefInjected翻译
        keyed_translations = [(k, t, g, f) for k, t, g, f in translations if '/' not in k]
        def_translations = [(k, t, g, f) for k, t, g, f in translations if '/' in k]
        
        # 临时切换生成器的输出目录
        original_mod_dir = self.generator.mod_dir
        self.generator.mod_dir = output_path
        
        try:
            # 生成Keyed模板
            if keyed_translations:
                if en_keyed_dir:
                    self.generator.generate_keyed_template(en_keyed_dir)
                self.generator.generate_keyed_template_from_data(keyed_translations)
                logging.info("生成 %s 条 Keyed 模板到 %s", len(keyed_translations), keyed_dir)
                print(f"{Fore.GREEN}✅ Keyed模板已生成: {keyed_dir}{Style.RESET_ALL}")            # 生成DefInjected模板
            if def_translations:
                try:
                    self._handle_definjected_structure_choice(
                        def_translations=def_translations,
                        export_dir=str(output_path),  # 外部模式：输出到指定目录
                        is_internal_mode=False
                    )
                except KeyboardInterrupt:
                    # 用户选择返回，重新抛出异常
                    raise
                
        finally:
            # 恢复原始输出目录
            self.generator.mod_dir = original_mod_dir
            
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
    
    def _handle_definjected_extraction_choice(self, output_dir: str = None, auto_choose: bool = False) -> str:
        """
        处理 DefInjected 提取方式选择
        
        Args:
            output_dir (str): 输出目录（用于调用 handle_extract_translate）
            auto_choose (bool): 是否自动选择，True时自动选择 'defs' 模式
            
        Returns:
            str: 选择的提取方式 ('definjected' 或 'defs')
        """
        if auto_choose:
            logging.info("自动选择 defs 提取模式")
            return "defs"
            
        # 如果提供了输出目录，使用智能选择逻辑
        if output_dir:
            try:
                extraction_mode = handle_extract_translate(
                    mod_dir=str(self.mod_dir),
                    export_dir=output_dir,
                    language=self.language,
                    source_language=CONFIG.source_language
                )
                return extraction_mode
            except KeyboardInterrupt:
                # 用户选择返回，抛出异常让上层处理
                raise
            except Exception as e:
                logging.warning("智能选择失败，回退到 defs 模式: %s", e)
                return "defs"
        else:
            # 没有输出目录时，默认使用 defs 模式
            logging.info("未指定输出目录，使用 defs 提取模式")
            return "defs"
        
    def _handle_definjected_structure_choice(self, def_translations: List[Tuple[str, str, str, str]], export_dir: str, is_internal_mode: bool = False):
        """处理 DefInjected 结构选择逻辑"""
        if not def_translations:
            return
            
        # 检查是否存在英文 DefInjected 目录
        src_lang_path = get_language_folder_path(CONFIG.source_language, str(self.mod_dir))
        src_definjected_dir = Path(src_lang_path) / CONFIG.def_injected_dir
        
        if src_definjected_dir.exists():
            # 有英文 DefInjected，提供3种选择
            print(f"\n{Fore.CYAN}检测到英文 DefInjected 目录，请选择文件结构：{Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}保持原英文DefInjected结构{Style.RESET_ALL}")
            print(f"   💡 与原模组翻译文件保持一致，便于维护和更新")
            print(f"2. {Fore.GREEN}按原Defs目录结构生成{Style.RESET_ALL}")
            print(f"   💡 按原始定义文件的目录结构组织翻译")
            print(f"3. {Fore.GREEN}按DefType自动分组{Style.RESET_ALL}")
            print(f"   💡 传统方式：ThingDefs、PawnKindDefs等类型分组")
            print(f"b. {Fore.YELLOW}返回上级菜单{Style.RESET_ALL}")
        else:
            # 没有英文 DefInjected，提供2种选择
            print(f"\n{Fore.YELLOW}未检测到英文 DefInjected 目录，请选择文件结构：{Style.RESET_ALL}")
            print(f"1. {Fore.GREEN}按原Defs目录结构生成{Style.RESET_ALL}")
            print(f"   💡 推荐：按原始定义文件的目录结构组织翻译")
            print(f"2. {Fore.GREEN}按DefType自动分组{Style.RESET_ALL}")
            print(f"   💡 传统方式：ThingDefs、PawnKindDefs等类型分组")
            print(f"b. {Fore.YELLOW}返回上级菜单{Style.RESET_ALL}")
        
        while True:
            structure_choice = input(f"\n{Fore.CYAN}请输入选项编号（回车默认1）：{Style.RESET_ALL}").strip().lower()
            
            if structure_choice == 'b':
                raise KeyboardInterrupt("用户选择返回")
            elif structure_choice in ['1', '2', '3', '']:
                break
            else:
                print(f"{Fore.RED}❌ 无效选择，请重新输入{Style.RESET_ALL}")
        
        # 处理用户选择（确保默认值为'1'）
        if structure_choice == '':
            structure_choice = '1'
        
        # 生成成功消息后缀
        location_suffix = "到模组内部" if is_internal_mode else f": {Path(export_dir) / 'Languages' / self.language / 'DefInjected'}"
        
        if src_definjected_dir.exists():
            # 有英文 DefInjected 的情况
            if structure_choice == "2":
                # 按原Defs目录结构
                export_definjected_with_defs_structure(
                    mod_dir=str(self.mod_dir),
                    export_dir=export_dir,
                    selected_translations=def_translations,
                    language=self.language
                )
                logging.info("生成 %s 条 DefInjected 模板（按Defs结构）", len(def_translations))
                print(f"{Fore.GREEN}✅ DefInjected模板已生成（按Defs结构）{location_suffix}{Style.RESET_ALL}")
            elif structure_choice == "3":
                # 按DefType自动分组
                if is_internal_mode:
                    self.generator.generate_definjected_template(def_translations)
                else:
                    # 外部模式需要临时切换生成器目录
                    original_mod_dir = self.generator.mod_dir
                    self.generator.mod_dir = export_dir
                    try:
                        self.generator.generate_definjected_template(def_translations)
                    finally:
                        self.generator.mod_dir = original_mod_dir
                logging.info("生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations))
                print(f"{Fore.GREEN}✅ DefInjected模板已生成（按DefType分组）{location_suffix}{Style.RESET_ALL}")
            else:
                # 默认：保持原英文DefInjected结构
                export_definjected_with_original_structure(
                    mod_dir=str(self.mod_dir),
                    export_dir=export_dir,
                    selected_translations=def_translations,
                    language=self.language
                )
                logging.info("生成 %s 条 DefInjected 模板（保持原结构）", len(def_translations))
                print(f"{Fore.GREEN}✅ DefInjected模板已生成（保持原结构）{location_suffix}{Style.RESET_ALL}")
        else:
            # 没有英文 DefInjected 的情况
            if structure_choice == "2":
                # 按DefType自动分组
                if is_internal_mode:
                    self.generator.generate_definjected_template(def_translations)
                else:
                    # 外部模式需要临时切换生成器目录
                    original_mod_dir = self.generator.mod_dir
                    self.generator.mod_dir = export_dir
                    try:
                        self.generator.generate_definjected_template(def_translations)
                    finally:
                        self.generator.mod_dir = original_mod_dir
                logging.info("生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations))
                print(f"{Fore.GREEN}✅ DefInjected模板已生成（按DefType分组）{location_suffix}{Style.RESET_ALL}")
            else:
                # 默认：按原Defs目录结构
                export_definjected_with_defs_structure(
                    mod_dir=str(self.mod_dir),
                    export_dir=export_dir,
                    selected_translations=def_translations,
                    language=self.language
                )
                logging.info("生成 %s 条 DefInjected 模板（按Defs结构）", len(def_translations))
                print(f"{Fore.GREEN}✅ DefInjected模板已生成（按Defs结构）{location_suffix}{Style.RESET_ALL}")
