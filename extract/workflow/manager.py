"""
模板管理器

负责翻译模板的完整生命周期管理，协调各个组件完成复杂的翻译提取和生成流程
"""

import csv
import re
from pathlib import Path
from typing import List, Tuple, Optional
from utils.ui_style import ui
from utils.logging_config import (
    get_logger,
    log_data_processing,
    log_user_action,
)
from ..core.extractors import DefInjectedExtractor, KeyedExtractor, DefsScanner
from ..core.exporters import DefInjectedExporter, KeyedExporter
from ..utils import SmartMerger
from utils.config import get_config, get_language_dir
from utils.path_manager import PathManager


class TemplateManager:
    """
    翻译模板管理器

    负责翻译模板的完整生命周期管理，协调各个组件完成复杂的翻译提取和生成流程
    """

    def __init__(self):
        """初始化模板管理器"""
        self.logger = get_logger(f"{__name__}.TemplateManager")
        self.logger.debug("初始化TemplateManager")

        # 初始化组件
        self.config = get_config()
        self.definjected_extractor = DefInjectedExtractor(self.config)
        self.keyed_extractor = KeyedExtractor(self.config)
        self.defs_scanner = DefsScanner(self.config)
        self.definjected_exporter = DefInjectedExporter(self.config)
        self.keyed_exporter = KeyedExporter(self.config)

    def extract_and_generate_templates(
        self,
        import_dir: str,
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: Optional[str] = None,
        template_structure: Optional[str] = None,
        has_input_keyed: bool = True,
        output_csv: Optional[str] = None,
    ) -> List[Tuple[str, str, str, str]]:
        """
        提取翻译数据并生成模板，同时导出CSV

        Args:
            import_dir: 输入目录路径
            import_language: 输入语言代码
            output_dir: 输出目录路径
            output_language: 输出语言代码
            data_source_choice: 数据来源选择 ('definjected_only' 或 'defs_only')
            template_structure: 模板结构选择
            has_input_keyed: 是否包含Keyed输入
            output_csv: CSV输出文件名

        Returns:
            List[Tuple[str, str, str, str]]: 提取的翻译数据
        """
        self.logger.debug(
            "开始提取翻译数据并生成模板: import_dir=%s, output_dir=%s",
            import_dir,
            output_dir,
        )
        log_user_action(
            "提取翻译模板",
            import_dir=import_dir,
            output_dir=output_dir,
            data_source=data_source_choice,
            template_structure=template_structure,
        )

        # 步骤1：提取翻译数据
        translations = self.extract_all_translations(
            import_dir,
            import_language,
            data_source_choice=data_source_choice,
            has_input_keyed=has_input_keyed,
        )

        if not translations:
            self.logger.warning("未找到任何翻译数据")
            ui.print_warning("未找到任何翻译数据")
            return []

        # 步骤2：根据用户选择的输出模式生成翻译模板
        self._generate_templates_to_output_dir_with_structure(
            output_dir=output_dir,
            output_language=output_language,
            translations=translations,
            template_structure=template_structure,
            has_input_keyed=has_input_keyed,
        )

        # 步骤3：导出CSV到输出目录
        self._save_translations_to_csv(
            translations, output_dir, output_language, output_csv
        )

        # 记录数据处理统计
        log_data_processing(
            "提取翻译模板",
            len(translations),
            data_source=data_source_choice,
            template_structure=template_structure,
        )

        self.logger.debug("模板生成完成，总计 %s 条翻译", len(translations))
        ui.print_success(f"提取完成：{len(translations)} 条")
        return translations

    def merge_mode(
        self,
        import_dir: str,
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: str = "defs_only",
        has_input_keyed: bool = True,
        output_csv: Optional[str] = None,
    ) -> List[Tuple[str, str, str, str]]:
        """
        执行智能合并模式处理翻译数据

        Args:
            import_dir: 输入目录路径
            import_language: 输入语言代码
            output_dir: 输出目录路径
            output_language: 输出语言代码
            data_source_choice: 数据来源选择
            has_input_keyed: 是否包含Keyed输入
            output_csv: CSV输出文件名

        Returns:
            List[Tuple[str, str, str, str]]: 合并后的翻译数据列表
        """
        # 步骤1：提取输入数据
        input_data = self.extract_all_translations(
            import_dir,
            import_language,
            data_source_choice=data_source_choice,
            has_input_keyed=has_input_keyed,
        )

        # 步骤2：提取输出数据
        output_data = self.extract_all_translations(
            output_dir,
            output_language,
            data_source_choice="definjected_only",
            has_input_keyed=has_input_keyed,
        )

        # 步骤3：智能合并翻译数据
        translations = SmartMerger.smart_merge_translations(
            input_data=input_data,
            output_data=output_data,
            include_unchanged=False,
        )

        for item in translations:
            self.logger.debug(item)

        # 分离键值对和定射
        keyed_translations = []
        def_translations = []
        for item in translations:
            k, _, _, f = item[:4]  # 兼容五元组和四元组
            if "." in k and (f.endswith(".xml") or "DefInjected" in str(f)):
                def_translations.append(item)
                print(f"DefInjected翻译: {item}")
            else:
                keyed_translations.append(item)
                print(f"Keyed翻译: {item}")

        # 写入合并结果
        if has_input_keyed and keyed_translations:
            ui.print_info("正在合并 Keyed ...")
            self._write_merged_translations(
                keyed_translations, output_dir, output_language, "keyed"
            )
            ui.print_success("Keyed 模板已合并")

        if def_translations:
            ui.print_info("正在合并 DefInjected ...")
            self._write_merged_translations(
                def_translations, output_dir, output_language, "defInjected"
            )
            ui.print_success("DefInjected 模板已合并")

        # 步骤4：导出CSV到输出目录
        self._save_translations_to_csv(
            translations, output_dir, output_language, output_csv
        )
        return translations

    def extract_all_translations(
        self,
        import_dir: str,
        import_language: str,
        data_source_choice: Optional[str] = None,
        has_input_keyed: bool = True,
    ) -> List[Tuple[str, str, str, str]]:
        """
        提取所有翻译数据

        Args:
            import_dir: 输入目录路径
            import_language: 输入语言代码
            data_source_choice: 数据来源选择 ('definjected_only', 'defs_only')
            has_input_keyed: 是否包含Keyed输入

        Returns:
            List[Tuple[str, str, str, str]]: 四元组列表 (key, text, tag, rel_path)
        """
        data_source_choice = data_source_choice or "defs_only"

        # 提取Keyed翻译（总是提取）
        if has_input_keyed:
            self.logger.debug("正在扫描 Keyed 目录...")
            keyed_translations = self.keyed_extractor.extract(
                import_dir, import_language
            )
            ui.print_success(
                f"从Keyed 目录提取到 {len(keyed_translations)} 条 Keyed 翻译"
            )
            self.logger.debug(
                "从Keyed 目录提取到 %s 条 Keyed 翻译", len(keyed_translations)
            )
        else:
            keyed_translations = []
            ui.print_warning("未检测到输入 Keyed 目录，已跳过 Keyed 提取。")

        if data_source_choice == "definjected_only":
            self.logger.debug("正在扫描 DefInjected 目录...")
            # 从DefInjected目录提取翻译数据
            definjected_translations = self.definjected_extractor.extract(
                import_dir, import_language
            )

            ui.print_success(
                f"从DefInjected 目录提取到 {len(definjected_translations)} 条 DefInjected 翻译"
            )
            self.logger.info(
                "从DefInjected 目录提取到 %s 条 DefInjected 翻译",
                len(definjected_translations),
            )
            # 将DefInjected五元组转换为四元组，以保持数据一致性
            definjected_translations_normalized = [
                (key, text, tag, rel_path)
                for key, text, tag, rel_path, _ in definjected_translations
            ]
            return keyed_translations + definjected_translations_normalized

        elif data_source_choice == "defs_only":
            self.logger.debug("正在扫描 Defs 目录...")
            defs_translations = self.defs_scanner.extract(import_dir)

            ui.print_success(f"从Defs目录提取到 {len(defs_translations)} 条 Defs 翻译")
            self.logger.debug(
                "从Defs目录提取到 %s 条 Defs 翻译", len(defs_translations)
            )
            return keyed_translations + defs_translations

        # 如果到了这里，说明没有匹配的data_source_choice
        self.logger.warning("未知的data_source_choice: %s", data_source_choice)
        return []

    def _generate_templates_to_output_dir_with_structure(
        self,
        output_dir: str,
        output_language: str,
        translations: List[Tuple],
        template_structure: Optional[str],
        has_input_keyed: bool = True,
    ):
        """在指定输出目录生成翻译模板结构"""
        template_structure = template_structure or "defs_by_type"
        output_path = Path(output_dir)

        # 分离Keyed和DefInjected翻译
        keyed_translations = []
        def_translations = []
        for item in translations:
            k, _, _, f = item[:4]  # 兼容五元组和四元组
            # 判断是否为DefInjected翻译的规则：
            # 1. key包含'/'（scan_defs_sync格式）：如 "ThingDef/Apparel_Pants.label"
            # 2. key包含'.'且file_path是DefInjected相关（extract_definjected_translations格式）：如 "Apparel_Pants.label"
            if "/" in k:
                def_translations.append(item)
            elif "." in k and (f.endswith(".xml") or "DefInjected" in str(f)):
                def_translations.append(item)
            else:
                keyed_translations.append(item)

        # 生成Keyed模板
        if has_input_keyed and keyed_translations:
            self.keyed_exporter.export_keyed_template(
                output_dir, output_language, keyed_translations
            )
            self.logger.debug(
                "生成 %s 条 Keyed 模板到 %s", len(keyed_translations), output_path
            )
            ui.print_success("Keyed 模板已生成")
        elif not has_input_keyed:
            ui.print_warning("未检测到输入 Keyed 目录，已跳过 Keyed 模板生成。")

        # 生成DefInjected模板
        if def_translations:
            self._generate_definjected_with_structure(
                def_translations,
                output_dir,
                output_language,
                template_structure,
            )

    def _generate_definjected_with_structure(
        self,
        def_translations: List[Tuple[str, str, str, str]],
        output_dir: str,
        output_language: str,
        template_structure: str,
    ):
        """根据智能配置的结构选择生成DefInjected模板"""
        if template_structure == "original_structure":
            # 使用原有结构的导出函数
            self.definjected_exporter.export_with_original_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug(
                "生成 %s 条 DefInjected 模板（保持原结构）", len(def_translations)
            )
            ui.print_success("DefInjected 模板已生成（保持原结构）")
        elif template_structure == "defs_by_type":
            # 按DefType分组的导出函数
            self.definjected_exporter.export_with_defs_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug(
                "生成 %s 条 DefInjected 模板（按DefType分组）", len(def_translations)
            )
            ui.print_success("DefInjected 模板已生成（按DefType分组）")
        elif template_structure == "defs_by_file_structure":
            # 按文件结构的导出函数
            self.definjected_exporter.export_with_file_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug(
                "生成 %s 条 DefInjected 模板（按文件结构）", len(def_translations)
            )
            ui.print_success("DefInjected 模板已生成（按文件结构）")
        else:
            # 默认使用按DefType分组
            self.definjected_exporter.export_with_defs_structure(
                output_dir, output_language, def_translations
            )
            self.logger.debug(
                "生成 %s 条 DefInjected 模板（默认分组）", len(def_translations)
            )
            ui.print_success("DefInjected 模板已生成（默认分组）")

    def _write_merged_translations(
        self, merged: List[Tuple], output_dir: str, output_language: str, sub_dir: str
    ) -> None:
        """
        通用写回 XML 方法，支持 DefInjected 和 Keyed

        Args:
            merged: List[(key, test, tag, rel_path, en_test, history)]
            output_dir: 输出根目录
            sub_dir: 子目录名（defInjected 或 keyed）
        """
        logger = get_logger(f"{__name__}.write_merged_translations")

        base_dir = get_language_dir(output_dir, output_language) / sub_dir

        # 按 rel_path 分组
        file_groups = {}
        for item in merged:
            rel_path = item[3]
            file_groups.setdefault(rel_path, []).append(item)

        processor = self.definjected_exporter.processor
        for rel_path, items in file_groups.items():
            output_file = base_dir / rel_path

            # 检查文件是否已存在
            if output_file.exists():
                # 读取现有XML文件
                existing_tree = processor.parse_xml(str(output_file))
                if existing_tree is not None:
                    root = existing_tree.getroot()
                    logger.info("更新现有文件: %s", output_file)
                else:
                    # 文件存在但解析失败，创建新的
                    logger.warning("无法解析现有文件，将重新创建: %s", output_file)
                    root = processor.create_element("LanguageData")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                # 文件不存在，创建新文件和目录
                logger.info("创建新文件: %s", output_file)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                root = processor.create_element("LanguageData")

            # 更新或添加翻译条目
            for key, test, _, _, en_test, history in sorted(items, key=lambda x: x[0]):
                # 清理标签名：去除斜杠，只保留字母、数字、下划线、点号
                clean_key = re.sub(r"[^A-Za-z0-9_.]", ".", key)
                if not re.match(r"^[A-Za-z_]", clean_key):
                    clean_key = "_" + clean_key

                # 查找现有元素
                existing_elem = root.find(clean_key)
                if existing_elem is not None:
                    # 更新现有元素
                    original_text = existing_elem.text or ""
                    # 根据设计文档5.1规则：比较input_text和output_en_text
                    if en_test != test:
                        # 内容有更新：用新内容替换原翻译，保留历史注释
                        if history and history.strip():
                            history_comment = processor.create_comment(history)
                            elem_index = list(root).index(existing_elem)
                            root.insert(elem_index, history_comment)
                        existing_elem.text = test
                    # 如果en_test == test，则保持原状，不做修改
                else:
                    # 添加新元素
                    # 先添加历史注释（如果有，且不为空）
                    if history and history.strip():
                        history_comment = processor.create_comment(
                            f"HISTORY: 原翻译内容：{history}，替换于YYYY-MM-DD"
                        )
                        root.append(history_comment)

                    # 添加英文注释（如果有）
                    if en_test:
                        en_comment = processor.create_comment(f"EN: {en_test}")
                        root.append(en_comment)

                    # 创建新的翻译元素
                    processor.create_subelement(root, clean_key, test)

            # 保存更新后的文件
            success = processor.save_xml(root, output_file, pretty_print=True)
            if success:
                logger.info("成功保存文件: %s (%s 条翻译)", output_file, len(items))
            else:
                logger.error("保存文件失败: %s", output_file)

    def _save_translations_to_csv(
        self,
        translations: List[Tuple],
        output_dir: str,
        output_language: str,
        output_csv: Optional[str] = None,
    ):
        """保存翻译数据到CSV文件"""
        csv_path = get_language_dir(output_dir, output_language) / output_csv
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file"])

            # 使用进度条进行导出
            for _, item in ui.iter_with_progress(
                translations,
                prefix="导出CSV",
                description=f"正在导出 {len(translations)} 条翻译到CSV",
            ):
                # 只导出前四个字段，兼容不同长度的元组
                if len(item) >= 4:
                    writer.writerow(item[:4])
                else:
                    self.logger.warning("数据格式错误，跳过导出: %s", item)

        ui.print_success(f"CSV文件已生成: {csv_path}")
        self.logger.debug("翻译数据已保存到CSV: %s", csv_path)

        # 记入历史：让提取生成的 CSV 出现在后续"Python机翻/导入翻译"的历史列表
        try:
            PathManager().remember_path("import_csv", str(csv_path))
        except (OSError, IOError, PermissionError) as e:
            self.logger.warning("无法记录CSV历史路径: %s, 错误: %s", csv_path, e)
