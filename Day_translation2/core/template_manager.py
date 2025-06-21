"""
Day Translation 2 - 模板管理器

负责翻译模板的完整生命周期管理，包括提取、生成、导入和验证。
遵循提示文件标准：模块级文档字符串、具体异常类型、用户友好错误信息。
"""

import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.generators import TemplateGenerator as Generator
from models.exceptions import ConfigError, ExportError
from models.exceptions import ImportError as TranslationImportError
from models.result_models import OperationResult, OperationStatus, OperationType
from models.translation_data import TranslationData
from services.config_service import config_service
from utils.xml_processor import AdvancedXMLProcessor as XMLProcessor


class TemplateManager:
    """翻译模板管理器，负责模板的完整生命周期管理"""

    def __init__(
        self,
        mod_dir: str,
        language: Optional[str] = None,
        template_location: str = "mod",
    ):
        """
        初始化模板管理器

        Args:
            mod_dir (str): 模组目录路径
            language (str): 目标语言
            template_location (str): 模板位置
        """
        self.config = config_service.get_unified_config()
        self.mod_dir = Path(mod_dir)
        self.language = language or self.config.core.default_language
        self.template_location = template_location
        self.generator = Generator(str(self.mod_dir), self.language, template_location)
        self.processor = XMLProcessor()

    def extract_and_generate_templates(
        self,
        output_dir: Optional[str] = None,
        en_keyed_dir: Optional[str] = None,
        auto_choose_definjected: bool = False,
        structure_choice: str = "original",
        merge_mode: str = "smart-merge",
    ) -> List[TranslationData]:
        """
        提取翻译数据并生成模板，同时导出CSV

        Args:
            output_dir (str): 输出目录路径
            en_keyed_dir (str): 英文Keyed目录路径（可选）
            auto_choose_definjected (bool): 是否自动选择DefInjected提取方式
            structure_choice (str): 结构选择（"original", "defs", "structured"）
            merge_mode (str): 合并模式（"merge", "replace", "backup", "skip", "smart-merge"）

        Returns:
            List[TranslationData]: 提取的翻译数据
        """
        logging.info("开始提取翻译数据并生成模板")

        try:
            # 步骤1：智能选择DefInjected提取方式
            definjected_extract_mode = self._handle_definjected_extraction_choice(
                output_dir, auto_choose_definjected
            )

            # 步骤2：提取翻译数据
            translations = self._extract_all_translations(definjected_mode=definjected_extract_mode)

            if not translations:
                logging.warning("未找到任何翻译数据")
                from colorama import Fore, Style

                print(f"{Fore.YELLOW}⚠️ 未找到任何翻译数据{Style.RESET_ALL}")
                return []

            # 步骤3：根据用户选择的输出模式生成翻译模板
            if output_dir:
                self._generate_templates_to_output_dir(
                    translations, output_dir, en_keyed_dir, structure_choice, merge_mode
                )
            else:
                self._generate_all_templates(
                    translations, en_keyed_dir, structure_choice, merge_mode
                )

            # 步骤4：导出CSV到输出目录
            if output_dir:
                csv_path = os.path.join(output_dir, "translations.csv")
                self._save_translations_to_csv(translations, csv_path)
                from colorama import Fore, Style

                print(f"{Fore.GREEN}✅ CSV文件已生成: {csv_path}{Style.RESET_ALL}")

            logging.info(f"模板生成完成，总计 {len(translations)} 条翻译")
            from colorama import Fore, Style

            print(f"{Fore.GREEN}✅ 提取完成：{len(translations)} 条{Style.RESET_ALL}")

            return translations

        except Exception as e:
            error_msg = f"提取和生成模板失败: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise ExportError(error_msg, output_path=output_dir)

    def import_translations(
        self, csv_path: str, merge: bool = True, auto_create_templates: bool = True
    ) -> bool:
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
                    raise TranslationImportError("无法创建翻译模板")

            # 步骤2：验证CSV文件
            if not self._validate_csv_file(csv_path):
                raise TranslationImportError(f"CSV文件验证失败: {csv_path}")

            # 步骤3：加载翻译数据
            translations = self._load_translations_from_csv(csv_path)
            if not translations:
                raise TranslationImportError("没有有效的翻译数据")

            # 步骤4：更新XML文件
            updated_count = self._update_all_xml_files(translations, merge)

            # 步骤5：验证导入结果
            success = self._verify_import_results()

            if success:
                logging.info(f"翻译导入到模板完成，更新了 {updated_count} 个文件")
                from colorama import Fore, Style

                print(f"{Fore.GREEN}✅ 翻译已成功导入到模板{Style.RESET_ALL}")
            else:
                logging.warning("翻译导入可能存在问题")
                from colorama import Fore, Style

                print(f"{Fore.YELLOW}⚠️ 翻译导入完成，但可能存在问题{Style.RESET_ALL}")

            return success

        except Exception as e:
            logging.error(f"导入翻译时发生错误: {e}", exc_info=True)
            from colorama import Fore, Style

            print(f"{Fore.RED}❌ 导入失败: {e}{Style.RESET_ALL}")
            raise TranslationImportError(f"导入翻译失败: {str(e)}", file_path=csv_path)

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
        try:
            translations = self.extract_and_generate_templates()
            return len(translations) > 0
        except Exception as e:
            logging.error(f"自动创建模板失败: {e}")
            return False

    def _extract_all_translations(self, definjected_mode: str = "defs") -> List[TranslationData]:
        """
        提取所有翻译数据

        Args:
            definjected_mode (str): DefInjected 提取模式 ('definjected' 或 'defs')

        Returns:
            List[TranslationData]: 翻译数据列表
        """
        translations = []

        # 延迟导入避免循环依赖
        from .extractors import (
            extract_definjected_translations,
            extract_keyed_translations,
            scan_defs_sync,
        )

        # 提取Keyed翻译
        try:
            keyed_translations = extract_keyed_translations(
                str(self.mod_dir), self.config.core.source_language
            )
            translations.extend(keyed_translations)
            logging.debug(f"提取到 {len(keyed_translations)} 条 Keyed 翻译")
        except Exception as e:
            logging.warning(f"提取Keyed翻译失败: {e}")

        # 根据模式提取DefInjected翻译
        try:
            if definjected_mode == "definjected":
                logging.info("从英文 DefInjected 目录提取翻译数据")

                # 从模组的英文DefInjected目录提取翻译数据
                from utils.file_utils import get_language_folder_path

                src_lang_path = get_language_folder_path(
                    self.config.core.source_language, str(self.mod_dir)
                )
                src_definjected_dir = Path(src_lang_path) / self.config.core.definjected_dir

                if src_definjected_dir.exists():
                    definjected_translations = extract_definjected_translations(
                        str(self.mod_dir), self.config.core.source_language
                    )
                    translations.extend(definjected_translations)
                    logging.debug(f"从英文DefInjected提取到 {len(definjected_translations)} 条翻译")
                else:
                    logging.warning(
                        f"英文DefInjected目录不存在: {src_definjected_dir}，回退到defs模式"
                    )
                    definjected_mode = "defs"

            if definjected_mode == "defs":
                defs_translations = scan_defs_sync(
                    str(self.mod_dir), language=self.config.core.source_language
                )
                translations.extend(defs_translations)
                logging.debug(f"提取到 {len(defs_translations)} 条 DefInjected 翻译")

        except Exception as e:
            logging.warning(f"提取DefInjected翻译失败: {e}")

        return translations

    def _generate_all_templates(
        self,
        translations: List[TranslationData],
        en_keyed_dir: Optional[str] = None,
        structure_choice: str = "original",
        merge_mode: str = "smart-merge",
    ):
        """生成所有翻译模板"""
        from models.translation_data import TranslationType

        # 分离Keyed和DefInjected翻译
        keyed_translations = [
            t for t in translations if t.translation_type == TranslationType.KEYED
        ]
        def_translations = [
            t for t in translations if t.translation_type == TranslationType.DEFINJECTED
        ]  # 生成Keyed模板
        if keyed_translations:
            if en_keyed_dir:
                self.generator.generate_keyed_template(en_keyed_dir)
            # 转换TranslationData对象为元组格式
            keyed_tuples = [t.to_tuple() for t in keyed_translations]
            self.generator.generate_keyed_template_from_data(keyed_tuples)
            logging.info(f"生成 {len(keyed_translations)} 条 Keyed 模板")

        # 生成DefInjected模板
        if def_translations:
            self._handle_definjected_structure_choice(
                def_translations=def_translations,
                export_dir=str(self.mod_dir),  # 内部模式：输出到模组目录
                is_internal_mode=True,
                structure_choice=structure_choice,
                merge_mode=merge_mode,
            )

    def _generate_templates_to_output_dir(
        self,
        translations: List[TranslationData],
        output_dir: str,
        en_keyed_dir: Optional[str] = None,
        structure_choice: str = "original",
        merge_mode: str = "smart-merge",
    ):
        """在指定输出目录生成翻译模板结构"""
        from models.translation_data import TranslationType

        output_path = Path(output_dir)

        # 创建语言目录结构
        lang_dir = output_path / "Languages" / "ChineseSimplified"
        keyed_dir = lang_dir / "Keyed"
        definjected_dir = lang_dir / "DefInjected"

        # 确保目录存在
        keyed_dir.mkdir(parents=True, exist_ok=True)
        definjected_dir.mkdir(parents=True, exist_ok=True)

        # 分离Keyed和DefInjected翻译
        keyed_translations = [
            t for t in translations if t.translation_type == TranslationType.KEYED
        ]
        def_translations = [
            t for t in translations if t.translation_type == TranslationType.DEFINJECTED
        ]

        # 临时切换生成器的输出目录
        original_mod_dir = self.generator.mod_dir
        self.generator.mod_dir = output_path

        try:
            # 生成Keyed模板
            if keyed_translations:
                if en_keyed_dir:
                    self.generator.generate_keyed_template(en_keyed_dir)
                # 转换TranslationData对象为元组格式
                keyed_tuples = [t.to_tuple() for t in keyed_translations]
                self.generator.generate_keyed_template_from_data(keyed_tuples)
                logging.info(f"生成 {len(keyed_translations)} 条 Keyed 模板到 {keyed_dir}")

            # 生成DefInjected模板
            if def_translations:
                self._handle_definjected_structure_choice(
                    def_translations=def_translations,
                    export_dir=str(output_path),  # 外部模式：输出到指定目录
                    is_internal_mode=False,
                    structure_choice=structure_choice,
                    merge_mode=merge_mode,
                )

        finally:
            # 恢复原始输出目录
            self.generator.mod_dir = original_mod_dir

    def _save_translations_to_csv(self, translations: List[TranslationData], csv_path: str):
        """保存翻译数据到CSV文件"""
        try:
            Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["key", "text", "tag", "file"])
                for translation in translations:
                    writer.writerow(
                        [
                            translation.key,
                            translation.original_text,
                            translation.tag,
                            translation.file_path,
                        ]
                    )

            logging.info(f"翻译数据已保存到CSV: {csv_path}")
        except Exception as e:
            raise ExportError(
                f"保存CSV文件失败: {str(e)}", output_path=csv_path, export_format="csv"
            )

    def _validate_csv_file(self, csv_path: str) -> bool:
        """验证CSV文件"""
        if not Path(csv_path).is_file():
            logging.error(f"CSV文件不存在: {csv_path}")
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
            logging.error(f"验证CSV文件时发生错误: {e}")
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
            from colorama import Fore, Style

            print(f"{Fore.RED}❌ 加载CSV文件失败: {e}{Style.RESET_ALL}")
            return {}

    def _update_all_xml_files(self, translations: Dict[str, str], merge: bool = True) -> int:
        """更新所有XML文件中的翻译"""
        from utils.file_utils import get_language_folder_path

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
            except Exception as e:
                logging.error(f"处理文件失败: {xml_file}: {e}")

        return updated_count

    def _verify_import_results(self) -> bool:
        """验证导入结果"""
        template_dir = self.mod_dir / "Languages" / self.language

        if not template_dir.exists():
            logging.error("导入后模板目录不存在")
            return False

        # 检查是否有翻译文件
        has_keyed = (
            any((template_dir / "Keyed").glob("*.xml"))
            if (template_dir / "Keyed").exists()
            else False
        )
        has_definjected = (
            any((template_dir / "DefInjected").glob("**/*.xml"))
            if (template_dir / "DefInjected").exists()
            else False
        )

        if not has_keyed and not has_definjected:
            logging.warning("导入后未找到翻译文件")
            return False

        logging.info("导入结果验证通过")
        return True

    def _handle_definjected_extraction_choice(
        self, output_dir: Optional[str] = None, auto_choose: bool = False
    ) -> str:
        """处理 DefInjected 提取方式选择"""

        if auto_choose:
            logging.info("自动选择 defs 提取模式")
            return "defs"

        if output_dir:
            # 简化逻辑：直接使用 defs 模式
            logging.info("使用 defs 提取模式")
            return "defs"
        else:
            logging.info("未指定输出目录，使用 defs 提取模式")
            return "defs"

    def _handle_definjected_structure_choice(
        self,
        def_translations: List[TranslationData],
        export_dir: str,
        is_internal_mode: bool = False,
        structure_choice: str = "original",
        merge_mode: str = "smart-merge",
    ):
        """处理 DefInjected 结构选择逻辑"""
        if not def_translations:
            return

        from utils.file_utils import get_language_folder_path

        from .exporters import (
            export_definjected_with_defs_structure,
            export_definjected_with_original_structure,
        )

        # def_translations 已经是 TranslationData 格式，直接使用
        # 检查是否存在英文 DefInjected 目录
        src_lang_path = get_language_folder_path(
            self.config.core.source_language, str(self.mod_dir)
        )
        src_definjected_dir = Path(src_lang_path) / self.config.core.definjected_dir

        if src_definjected_dir.exists():
            # 有英文 DefInjected 的情况
            if structure_choice == "defs":
                # 按原Defs目录结构
                export_definjected_with_defs_structure(
                    translations=def_translations,
                    output_dir=export_dir,
                    language=self.language,
                )
                logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板（按Defs结构）")
            elif structure_choice == "structured":  # 按DefType自动分组
                if is_internal_mode:
                    # 转换TranslationData对象为元组格式
                    def_tuples = [t.to_tuple() for t in def_translations]
                    self.generator.generate_definjected_template(def_tuples)
                else:
                    # 外部模式需要临时切换生成器目录
                    original_mod_dir_1 = self.generator.mod_dir
                    self.generator.mod_dir = Path(export_dir)
                    try:
                        # 转换TranslationData对象为元组格式
                        def_tuples = [t.to_tuple() for t in def_translations]
                        self.generator.generate_definjected_template(def_tuples)
                    finally:
                        self.generator.mod_dir = original_mod_dir_1
                logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板（按DefType分组）")
            else:
                # 默认：保持原英文DefInjected结构（original）
                export_definjected_with_original_structure(
                    translations=def_translations,
                    output_dir=export_dir,
                    language=self.language,
                )
                logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板（保持原结构）")
        else:
            # 没有英文 DefInjected 的情况
            if structure_choice == "structured":
                # 按DefType自动分组
                if is_internal_mode:
                    # 转换TranslationData对象为元组格式
                    def_tuples = [t.to_tuple() for t in def_translations]
                    self.generator.generate_definjected_template(def_tuples)
                else:  # 外部模式需要临时切换生成器目录
                    original_mod_dir_2 = self.generator.mod_dir
                    self.generator.mod_dir = Path(export_dir)
                    try:
                        # 转换TranslationData对象为元组格式
                        def_tuples = [t.to_tuple() for t in def_translations]
                        self.generator.generate_definjected_template(def_tuples)
                    finally:
                        self.generator.mod_dir = original_mod_dir_2
                logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板（按DefType分组）")
            else:
                # 默认：按原Defs目录结构（original或defs都用这个）
                export_definjected_with_defs_structure(
                    translations=def_translations,
                    output_dir=export_dir,
                    language=self.language,
                )
                logging.info(f"生成 {len(def_translations)} 条 DefInjected 模板（按Defs结构）")
