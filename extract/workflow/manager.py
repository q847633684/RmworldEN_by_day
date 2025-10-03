"""
模板管理器

负责翻译模板的完整生命周期管理，协调各个组件完成复杂的翻译提取和生成流程
"""

import csv
import re
from pathlib import Path
from typing import List, Tuple, Optional
from utils.ui_style import ui
from utils.utils import sanitize_xml
from utils.logging_config import (
    get_logger,
    log_data_processing,
    log_user_action,
)
from ..core.extractors import DefInjectedExtractor, KeyedExtractor, DefsScanner
from ..core.exporters import DefInjectedExporter, KeyedExporter
from ..utils import SmartMerger
from user_config import UserConfigManager
from user_config.path_manager import PathManager


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
        self.config = UserConfigManager.get_instance()
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
    ) -> tuple[List[Tuple[str, str, str, str]], str]:
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
            tuple[List[Tuple[str, str, str, str]], str]: (提取的翻译数据, CSV文件路径)
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
        keyed_translations, def_translations = self.extract_all_translations(
            import_dir,
            import_language,
            data_source_choice=data_source_choice,
            has_input_keyed=has_input_keyed,
        )

        if not keyed_translations and not def_translations:
            self.logger.warning("未找到任何翻译数据")
            ui.print_warning("未找到任何翻译数据")
            return []

        # 步骤2：根据用户选择的输出模式生成翻译模板
        self._generate_templates_to_output_dir_with_structure(
            output_dir=output_dir,
            output_language=output_language,
            keyed_translations=keyed_translations,
            def_translations=def_translations,
            template_structure=template_structure,
            has_input_keyed=has_input_keyed,
        )

        # 步骤3：导出CSV到输出目录
        csv_path = self._save_translations_to_csv(
            keyed_translations,
            def_translations,
            output_dir,
            output_language,
            output_csv,
        )
        all_translations = keyed_translations + def_translations
        # 记录数据处理统计
        log_data_processing(
            "提取翻译模板",
            len(all_translations),
            data_source=data_source_choice,
            template_structure=template_structure,
        )

        self.logger.debug("模板生成完成，总计 %s 条翻译", len(all_translations))
        return all_translations, csv_path

    def merge_mode(
        self,
        import_dir: str,
        import_language: str,
        output_dir: str,
        output_language: str,
        data_source_choice: str = "defs_only",
        has_input_keyed: bool = True,
        output_csv: Optional[str] = None,
    ) -> tuple[List[Tuple[str, str, str, str]], str]:
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
            tuple[List[Tuple[str, str, str, str]], str]: (合并后的翻译数据列表, CSV文件路径)
        """
        # 步骤1：提取输入数据
        input_keyed, input_def = self.extract_all_translations(
            import_dir,
            import_language,
            data_source_choice=data_source_choice,
            has_input_keyed=has_input_keyed,
        )

        # 步骤2：提取输出数据
        output_keyed, output_def = self.extract_all_translations(
            output_dir,
            output_language,
            data_source_choice="definjected_only",
            has_input_keyed=has_input_keyed,
        )

        # 步骤3：智能合并翻译数据
        keyed_translations = SmartMerger.smart_merge_translations(
            input_data=input_keyed,
            output_data=output_keyed,
            include_unchanged=False,
        )
        def_translations = SmartMerger.smart_merge_translations(
            input_data=input_def,
            output_data=output_def,
            include_unchanged=False,
        )
        # 写入合并结果
        if keyed_translations:
            ui.print_info("正在合并 Keyed ...")
            self._write_merged_translations(
                keyed_translations, output_dir, output_language, "Keyed"
            )

        if def_translations:
            ui.print_info("正在合并 DefInjected ...")
            self._write_merged_translations(
                def_translations, output_dir, output_language, "DefInjected"
            )

        # 步骤4：导出CSV到输出目录
        csv_path = self._save_translations_to_csv(
            keyed_translations,
            def_translations,
            output_dir,
            output_language,
            output_csv,
        )
        translations = keyed_translations + def_translations
        return translations, csv_path

    def extract_all_translations(
        self,
        import_dir: str,
        import_language: str,
        data_source_choice: Optional[str] = None,
        has_input_keyed: bool = True,
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        提取所有翻译数据

        Args:
            import_dir: 输入目录路径
            import_language: 输入语言代码
            data_source_choice: 数据来源选择 ('definjected_only', 'defs_only')
            has_input_keyed: 是否包含Keyed输入

        Returns:
            List[Tuple[str, str, str, str, str]]: 五元组列表 (key, text, tag, rel_path, en_text)
        """
        data_source_choice = data_source_choice or "defs_only"

        # 提取Keyed翻译
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
            # 将Keyed四元组转换为五元组，保持数据一致性
            keyed_translations = [
                (key, text, tag, rel_path, text)  # en_text用text填充
                for key, text, tag, rel_path in keyed_translations
            ]
        else:
            keyed_translations = []

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
            return (keyed_translations, definjected_translations)

        elif data_source_choice == "defs_only":
            self.logger.debug("正在扫描 Defs 目录...")
            defs_translations = self.defs_scanner.extract(import_dir)

            ui.print_success(f"从Defs目录提取到 {len(defs_translations)} 条 Defs 翻译")
            self.logger.debug(
                "从Defs目录提取到 %s 条 Defs 翻译", len(defs_translations)
            )
            # 将Defs四元组转换为五元组，保持数据一致性
            defs_translations = [
                (key, text, tag, rel_path, text)
                for key, text, tag, rel_path in defs_translations  # en_text用text填充
            ]
            return (keyed_translations, defs_translations)

        # 如果到了这里，说明没有匹配的data_source_choice
        self.logger.warning("未知的data_source_choice: %s", data_source_choice)
        return []

    def _generate_templates_to_output_dir_with_structure(
        self,
        output_dir: str,
        output_language: str,
        keyed_translations: List[Tuple],
        def_translations: List[Tuple],
        template_structure: Optional[str],
        has_input_keyed: bool = True,
    ):
        """在指定输出目录生成翻译模板结构"""
        template_structure = template_structure or "defs_by_type"
        output_path = Path(output_dir)

        if not keyed_translations and not def_translations:
            ui.print_warning("没有翻译数据需要生成模板")
            return

        # 生成Keyed模板
        if has_input_keyed:
            if keyed_translations:
                ui.print_info(f"生成 {len(keyed_translations)} 条 Keyed 模板...")
                self.keyed_exporter.export_keyed_template(
                    output_dir, output_language, keyed_translations
                )
                self.logger.debug(
                    "生成 %s 条 Keyed 模板到 %s", len(keyed_translations), output_path
                )
                ui.print_success("Keyed 模板已生成")
            else:
                ui.print_warning("未找到 Keyed 翻译数据，已跳过 Keyed 模板生成。")
        else:
            ui.print_warning("未检测到输入 Keyed 目录，已跳过 Keyed 模板生成。")

        # 生成DefInjected模板
        if def_translations:
            ui.print_info(f"生成 {len(def_translations)} 条 DefInjected 模板...")
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
            ui.print_success("未知结构 请检查配置")
            self.logger.warning("未知结构 请检查配置")
            raise ValueError("未知结构 请检查配置")

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

        # 使用新配置系统获取语言目录
        config_manager = UserConfigManager.get_instance()
        base_dir = (
            config_manager.language_config.get_language_dir(output_dir, output_language)
            / sub_dir
        )

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
                    # 更新现有元素 - 采用旧代码的简单逻辑
                    original_text = existing_elem.text or ""
                    if original_text != test:
                        elem_index = list(root).index(existing_elem)

                        # 删除紧挨着元素的前一个EN注释（匹配具体内容）
                        if elem_index > 0 and en_test:
                            prev_child = root[elem_index - 1]
                            expected_en_text = f"EN: {en_test}"
                            if (
                                type(prev_child).__name__ == "_Comment"
                                and hasattr(prev_child, "text")
                                and prev_child.text
                                and prev_child.text.strip() == expected_en_text
                            ):
                                root.remove(prev_child)
                                elem_index -= 1  # 调整索引

                        # 添加历史注释
                        if history and history.strip():
                            history_comment = processor.create_comment(history)
                            root.insert(elem_index, history_comment)
                            elem_index += 1  # 调整索引

                        # 添加新的英文注释
                        if test:
                            en_comment = processor.create_comment(f"EN: {test}")
                            root.insert(elem_index, en_comment)
                            elem_index += 1  # 调整索引

                    existing_elem.text = sanitize_xml(test)
                else:
                    # 添加新元素
                    # 先添加历史注释（如果有，且不为空）
                    if history and history.strip():
                        history_comment = processor.create_comment(history)
                        root.append(history_comment)

                    # 添加英文注释（如果有）
                    if test:
                        en_comment = processor.create_comment(f"EN: {test}")
                        root.append(en_comment)
                    else:
                        en_comment = processor.create_comment(f"EN: {en_test}")
                        root.append(en_comment)

                    # 创建新的翻译元素
                    processor.create_subelement(root, clean_key, sanitize_xml(test))

            # 保存更新后的文件
            success = processor.save_xml(root, output_file, pretty_print=True)
            if success:
                logger.info("成功保存文件: %s (%s 条翻译)", output_file, len(items))
            else:
                logger.error("保存文件失败: %s", output_file)

        # 统计合并结果
        updated_count = sum(1 for item in merged if len(item) > 5 and item[5])
        new_count = sum(1 for item in merged if len(item) > 5 and "新增于" in item[5])
        ui.print_success(
            f"{sub_dir} 智能合并完成！共处理 {len(merged)} 条翻译（更新: {updated_count} 条，新增: {new_count} 条）"
        )

    def _save_translations_to_csv(
        self,
        keyed_translations: List[Tuple],
        def_translations: List[Tuple],
        output_dir: str,
        output_language: str,
        output_csv: Optional[str] = None,
    ) -> str:
        """保存翻译数据到CSV文件

        Args:
            keyed_translations: Keyed翻译数据列表
            def_translations: DefInjected翻译数据列表
            output_dir: 输出目录
            output_language: 输出语言
            output_csv: CSV文件名，默认为"translations.csv"

        Returns:
            str: CSV文件路径
        """
        config_manager = UserConfigManager.get_instance()
        csv_path = (
            config_manager.language_config.get_language_dir(output_dir, output_language)
            / output_csv
        )
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "text", "tag", "file", "type"])

            # 合并所有翻译数据
            all_translations = []

            # 添加Keyed翻译数据
            for item in keyed_translations:
                if len(item) >= 4:
                    all_translations.append((*item[:4], "keyed"))

            # 添加DefInjected翻译数据
            for item in def_translations:
                if len(item) >= 4:
                    all_translations.append((*item[:4], "def"))

            # 使用进度条进行导出
            for _, item in ui.iter_with_progress(
                all_translations,
                prefix="导出CSV",
                description=f"正在导出 {len(all_translations)} 条翻译到CSV",
            ):
                writer.writerow(item)

        ui.print_success(f"CSV文件已生成: {csv_path}")
        self.logger.debug("翻译数据已保存到CSV: %s", csv_path)

        # 记入历史：让提取生成的 CSV 出现在后续"Python机翻/导入翻译"的历史列表
        try:
            PathManager().remember_path("import_csv", str(csv_path))
        except (OSError, IOError, PermissionError) as e:
            self.logger.warning("无法记录CSV历史路径: %s, 错误: %s", csv_path, e)

        return str(csv_path)
