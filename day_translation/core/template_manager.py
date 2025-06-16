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

from .extractors import extract_keyed_translations, scan_defs_sync
from .generators import TemplateGenerator
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
            template_location (str): 模板位置
        """
        self.mod_dir = Path(mod_dir)
        self.language = language
        self.template_location = template_location
        self.generator = TemplateGenerator(str(self.mod_dir), language, template_location)
        self.processor = XMLProcessor()
    def extract_and_generate_templates(self, output_dir: str = None, en_keyed_dir: str = None) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译数据并生成模板，同时导出CSV
        
        Args:
            output_dir (str): 输出目录路径
            en_keyed_dir (str): 英文Keyed目录路径（可选）
            
        Returns:
            List[Tuple[str, str, str, str]]: 提取的翻译数据
        """
        logging.info("开始提取翻译数据并生成模板")
        
        # 步骤1：提取翻译数据
        translations = self._extract_all_translations()
        
        if not translations:
            logging.warning("未找到任何翻译数据")
            print(f"{Fore.YELLOW}⚠️ 未找到任何翻译数据{Style.RESET_ALL}")
            return []
              # 步骤2：生成翻译模板到指定输出目录
        if output_dir:
            self._generate_templates_to_output_dir(translations, output_dir, en_keyed_dir)
        else:        
            self._generate_all_templates(translations, en_keyed_dir)
        
        # 步骤3：导出CSV到输出目录
        if output_dir:
            csv_path = os.path.join(output_dir, "translations.csv")
            self._save_translations_to_csv(translations, csv_path)
            print(f"{Fore.GREEN}✅ CSV文件已生成: {csv_path}{Style.RESET_ALL}")
            
        logging.info(f"模板生成完成，总计 {len(translations)} 条翻译")
        print(f"{Fore.GREEN}✅ 提取完成：{len(translations)} 条{Style.RESET_ALL}")
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
        logging.info(f"开始导入翻译到模板: {csv_path}")
        
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
                logging.info(f"翻译导入到模板完成，更新了 {updated_count} 个文件")
                print(f"{Fore.GREEN}✅ 翻译已成功导入到模板{Style.RESET_ALL}")
            else:
                logging.warning("翻译导入可能存在问题")
                print(f"{Fore.YELLOW}⚠️ 翻译导入完成，但可能存在问题{Style.RESET_ALL}")
                
            return success
            
        except Exception as e:
            logging.error(f"导入翻译时发生错误: {e}", exc_info=True)
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
        
    def _extract_all_translations(self) -> List[Tuple[str, str, str, str]]:
        """提取所有翻译数据"""
        translations = []
        
        # 提取Keyed翻译
        keyed_translations = extract_keyed_translations(str(self.mod_dir), CONFIG.source_language)
        translations.extend(keyed_translations)
        logging.debug(f"提取到 {len(keyed_translations)} 条 Keyed 翻译")
        
        # 提取Defs翻译
        defs_translations = list(tqdm(scan_defs_sync(str(self.mod_dir)), desc="提取 DefInjected"))
        translations.extend(defs_translations)
        logging.debug(f"提取到 {len(defs_translations)} 条 DefInjected 翻译")
        
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
            logging.info(f"生成 {len(keyed_translations)} 条 Keyed 模板")
            
        # 生成DefInjected模板
        if def_translations:
            self.generator.generate_definjected_template(def_translations)
            logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板")
            
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
        original_base_dir = self.generator.config.base_dir
        self.generator.config.base_dir = str(output_path)
        
        try:
            # 生成Keyed模板
            if keyed_translations:
                if en_keyed_dir:
                    self.generator.generate_keyed_template(en_keyed_dir)
                self.generator.generate_keyed_template_from_data(keyed_translations)
                logging.info(f"生成 {len(keyed_translations)} 条 Keyed 模板到 {keyed_dir}")
                print(f"{Fore.GREEN}✅ Keyed模板已生成: {keyed_dir}{Style.RESET_ALL}")
                
            # 生成DefInjected模板
            if def_translations:
                self.generator.generate_definjected_template(def_translations)
                logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板到 {definjected_dir}")
                print(f"{Fore.GREEN}✅ DefInjected模板已生成: {definjected_dir}{Style.RESET_ALL}")
                
        finally:
            # 恢复原始输出目录
            self.generator.config.base_dir = original_base_dir
            
    def _save_translations_to_csv(self, translations: List[Tuple[str, str, str, str]], csv_path: str):
        """保存翻译数据到CSV文件"""
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])
            writer.writerows(translations)
            
        logging.info(f"翻译数据已保存到CSV: {csv_path}")
        
    def _validate_csv_file(self, csv_path: str) -> bool:
        """验证CSV文件"""
        if not Path(csv_path).is_file():
            logging.error(f"CSV文件不存在: {csv_path}")
            print(f"{Fore.RED}❌ CSV文件不存在: {csv_path}{Style.RESET_ALL}")
            return False
            
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header or not all(col in header for col in ["key", "text"]):
                    logging.error("CSV文件格式无效：缺少必要的列")
                    print(f"{Fore.RED}❌ CSV文件格式无效：缺少必要的列{Style.RESET_ALL}")
                    return False
                return True
        except Exception as e:
            logging.error(f"验证CSV文件时发生错误: {e}")
            print(f"{Fore.RED}❌ 验证CSV文件失败: {e}{Style.RESET_ALL}")
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
            logging.error(f"加载CSV文件时发生错误: {e}")
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
