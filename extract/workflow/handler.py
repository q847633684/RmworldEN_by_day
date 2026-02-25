"""
RimWorld 翻译提取主处理器

负责协调整个翻译提取流程，包括：
- 用户交互和配置选择
- 智能工作流程管理
- 冲突处理和模式选择
- 错误处理和日志记录
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from user_config import UserConfigManager
from utils.logging_config import get_logger, log_user_action
from utils.error_handling import report_handler_error
from utils.interaction import (
    prompt_choose_from_list,
    select_mod_path_with_version_detection,
)
from utils.ui_style import ui, _get_mod_display_name
from utils.constants import LOAD_FOLDERS_FILENAME
from utils.rimworld_about import sanitize_mod_name_for_path
from utils.path_utils import (
    compute_scan_labels_for_roots,
    normalize_slashes,
    rel_path_str,
)
from extract.utils.merger import dedupe_translations_by_key
from utils.load_folders import get_load_folders_versions, get_version_dirs_from_fs
from .manager import (
    TemplateManager,
    generate_load_folders_xml,
    get_content_roots_from_load_folders,
)
from .interaction import InteractionManager


def _short_csv_basename(mod_name: str, export_rel: str) -> str:
    """生成简短 CSV 名。根目录用 {mod_name}_extracted.csv；子路径用 R_M_Biotech_extracted.csv 格式"""
    if not export_rel:
        return f"{mod_name}_extracted.csv" if mod_name else "extracted.csv"
    mod_prefix = (mod_name[0] if mod_name else "").upper()
    parts = [p for p in normalize_slashes(export_rel).split("/") if p]
    if not parts:
        return f"{mod_prefix}_extracted.csv" if mod_prefix else "extracted.csv"
    initials = "_".join(p[0].upper() for p in parts[:-1])
    last = parts[-1]
    if initials:
        base = f"{mod_prefix}_{initials}_{last}"
    else:
        base = f"{mod_prefix}_{last}"
    return f"{base}_extracted.csv"


def handle_extract(
    batch_mod_dir: Optional[str] = None,
    batch_output_dir: Optional[str] = None,
    batch_version: Optional[str] = None,
) -> Optional[tuple]:
    """处理提取模板功能

    Args:
        batch_mod_dir: 批量模式时传入的模组目录，与 batch_output_dir 同时传入则跳过模组/输出选择
        batch_output_dir: 批量模式时传入的输出目录
        batch_version: 仅批量模式使用，指定版本（如 "1.6"、"1.5"），单次提取不传，版本由 LoadFolders.xml 决定

    Returns:
        Optional[tuple]: (csv_path, mod_dir) 元组，如果失败则返回None
    """
    logger = get_logger(f"{__name__}.handle_extract")
    config = UserConfigManager.get_instance()
    batch_mode = batch_mod_dir is not None and batch_output_dir is not None

    print(f"日志文件路径：{config.system_config.get_value('log_file')}")
    if config.system_config.get_value("debug_mode"):
        print("调试模式已开启，详细日志见日志文件。")

    logger.info("开始处理提取模板功能")

    try:
        preselected_version = None
        if batch_mode:
            mod_dir = batch_mod_dir
            log_user_action("批量提取模组目录", mod_dir=mod_dir)
        else:
            # 选择模组目录（可能返回 (path, type) 或 (模组根, 版本名)，统一取路径）
            result = select_mod_path_with_version_detection()
            if not result:
                logger.info("用户取消了模组目录选择")
                return None
            mod_dir = result[0] if isinstance(result, tuple) else result
            # 版本结构下 path_manager 返回 (模组根, 版本名)，复用以免二次选择版本
            if isinstance(result, tuple) and len(result) >= 2:
                preselected_version = result[1]
            log_user_action("选择模组目录", mod_dir=mod_dir)

        # 用户输入即为模组根
        scan_base = mod_dir
        load_folders_mod_root = scan_base

        load_folders_entries: Optional[List[Tuple[str, Dict[str, str]]]] = None
        content_roots: List[str] = []

        # 1. 检查是否有 LoadFolders.xml
        has_load_folders_xml = (Path(scan_base) / LOAD_FOLDERS_FILENAME).is_file()
        if has_load_folders_xml:
            versions = get_load_folders_versions(scan_base)
            if versions:
                # 有版本号：批量用传入的版本参数，单次用路径选择时已选版本或再选一次
                if batch_mode:
                    ver = (batch_version or "1.6").strip()
                    if ver not in versions:
                        ver = versions[0]
                elif preselected_version and preselected_version in versions:
                    ver = preselected_version
                else:
                    ver = prompt_choose_from_list(versions, "请选择版本：")
                    if ver is None:
                        return None
                load_folders_entries = get_content_roots_from_load_folders(scan_base, ver)
                if load_folders_entries:
                    content_roots = [p for p, _ in load_folders_entries]
                    ui.print_info(f"已从 LoadFolders.xml 读取 <v{ver}> 共 {len(content_roots)} 个内容根")

        # 2. 没有 LoadFolders 或未读到：读取目录里的版本号（1.6 / v1.6），选版本后扫描该版本+根目录合并到一个 Languages
        if not content_roots:
            version_dirs = get_version_dirs_from_fs(scan_base)
            if version_dirs:
                # 批量用传入的版本参数，单次用路径选择时已选版本或再选一次
                if batch_mode:
                    sel = (batch_version or "1.6").strip()
                    picked = sel if sel in version_dirs else ("v" + sel if "v" + sel in version_dirs else version_dirs[0])
                elif preselected_version and (preselected_version in version_dirs or ("v" + preselected_version in version_dirs)):
                    picked = preselected_version if preselected_version in version_dirs else "v" + preselected_version
                else:
                    picked = prompt_choose_from_list(version_dirs, "请选择版本（目录名）：")
                    if picked is None:
                        return None
                version_path = Path(scan_base) / picked
                if version_path.exists() and version_path.is_dir():
                    content_roots = [str(version_path.resolve()), str(Path(scan_base).resolve())]
                    ui.print_info(f"已按版本 {picked} + 根目录扫描，合并到一个 Languages")
            else:
                # 没有读取到目录里的版本号：只提取根目录语言文件
                content_roots = [str(Path(scan_base).resolve())]
                ui.print_info("未检测到版本目录，已按根目录提取语言文件")

        if not content_roots:
            ui.print_error("未找到 Defs 或 Languages 目录，请确认模组路径正确")
            return None

        # 3. 构建 root_groups：有 LoadFolders 时无属性合并、有属性各自导出；否则全部合并为一组
        if load_folders_entries is not None:
            main_roots = [p for p, a in load_folders_entries if not a]
            compat_entries = [(p, a) for p, a in load_folders_entries if a]
            root_groups = []
            if main_roots:
                root_groups.append((main_roots, ""))
            scan_base_path = Path(scan_base).resolve()
            for full_path, _ in compat_entries:
                try:
                    rel_str = str(Path(full_path).resolve().relative_to(scan_base_path)).replace("\\", "/")
                except (ValueError, OSError):
                    rel_str = Path(full_path).name or ""
                root_groups.append(([full_path], rel_str))
        else:
            root_groups = [(content_roots, "")]
        num_groups = len(root_groups)
        multi_group_or_merge = num_groups > 1 or (num_groups == 1 and len(root_groups[0][0]) > 1)
        if multi_group_or_merge:
            ui.print_success(
                f"共 {num_groups} 个导出组，合并组导出到 Languages，其余按路径导出"
            )
            for roots, export_rel in root_groups:
                if export_rel:
                    ui.print_info(f"   · {export_rel}")
                else:
                    ui.print_info("   · / (合并到 Languages)")

        # 创建模板管理器和交互管理器
        template_manager = TemplateManager()
        interaction_manager = InteractionManager()

        if not batch_mode:
            ui.print_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程（批量模式时使用固定输出目录与默认选项）
            effective_dir = root_groups[0][0][0]
            smart_config = interaction_manager.handle_smart_extraction_workflow(
                effective_dir,
                skip_output_selection=batch_mode,
                fixed_output_dir=batch_output_dir if batch_mode else None,
                batch_mode=batch_mode,
            )

            conflict_resolution = smart_config["output_config"]["conflict_resolution"]
            data_source_choice = smart_config["data_sources"]["choice"]
            template_structure = smart_config["template_structure"]
            import_status = smart_config["data_sources"]["import_status"]
            import_language = import_status["language"]
            # 多根时对每个根检测 Keyed
            all_roots = [r for roots, _ in root_groups for r in roots]
            has_input_keyed = import_status.get("has_keyed", False)
            if len(all_roots) > 1:
                for r in all_roots:
                    keyed_dir = config.language_config.get_language_subdir(
                        str(r), import_language, "keyed"
                    )
                    if keyed_dir.exists():
                        has_input_keyed = True
                        break
            output_language = smart_config["output_config"]["output_status"]["language"]

            ui.print_info(
                f"配置: 数据={data_source_choice}, 模板={template_structure}, 冲突={conflict_resolution}"
            )

            default_csv_name = config.language_config.get_value(
                "output_csv", "translations.csv"
            )
            mod_root = load_folders_mod_root or mod_dir
            mod_name = sanitize_mod_name_for_path(_get_mod_display_name(mod_root))
            all_csv_paths: List[str] = []
            chosen_output_dir = smart_config["output_config"]["output_dir"]

            def _is_external_output(out_dir: str, base_dir: str) -> bool:
                try:
                    Path(out_dir).resolve().relative_to(Path(base_dir).resolve())
                    return False
                except (ValueError, TypeError):
                    return True

            multi_root_external = num_groups > 1 and _is_external_output(chosen_output_dir, mod_dir)
            groups_with_content: List[str] = []  # export_rel 列表，用于生成 LoadFolders.xml
            roots_with_content: set = set()
            roots_with_content_output_dirs: dict = {}

            ui.print_info(f"输出: {chosen_output_dir}")
            for roots, export_rel in root_groups:
                output_dir = chosen_output_dir if not export_rel else str(Path(chosen_output_dir) / export_rel)
                if mod_name:
                    output_csv_name = _short_csv_basename(mod_name, export_rel)
                else:
                    output_csv_name = default_csv_name
                # 传文件名给 manager，CSV 会写入 output_dir/Languages/{output_language}/ 与 Keyed/DefInjected 同级
                output_csv = output_csv_name
                output_path = Path(output_dir)
                import_dir = roots[0] if len(roots) == 1 else ""

                label = export_rel if export_rel else "/"
                # 根据冲突处理方式执行相应操作
                if conflict_resolution == "merge":
                    if len(roots) > 1:
                        all_keyed, all_def = [], []
                        for r in roots:
                            r_label = rel_path_str(scan_base, r)
                            k, d = template_manager.extract_all_translations(
                                r,
                                import_language,
                                data_source_choice=data_source_choice,
                                has_input_keyed=has_input_keyed,
                                scan_label=r_label,
                            )
                            all_keyed.extend(k)
                            all_def.extend(d)
                        all_keyed, all_def = dedupe_translations_by_key(
                            all_keyed, all_def
                        )
                        translations, csv_path = template_manager.merge_mode(
                            import_dir=roots[0],
                            import_language=import_language,
                            output_dir=output_dir,
                            output_language=output_language,
                            data_source_choice=data_source_choice,
                            has_input_keyed=has_input_keyed,
                            output_csv=output_csv,
                            input_keyed=all_keyed,
                            input_def=all_def,
                            import_label=label,
                            template_structure=template_structure,
                        )
                    else:
                        translations, csv_path = template_manager.merge_mode(
                            import_dir=import_dir,
                            import_language=import_language,
                            output_dir=output_dir,
                            output_language=output_language,
                            data_source_choice=data_source_choice,
                            has_input_keyed=has_input_keyed,
                            output_csv=output_csv,
                            import_label=label,
                            template_structure=template_structure,
                        )
                    if csv_path:
                        all_csv_paths.append(csv_path)
                        for r in roots:
                            roots_with_content.add(r)
                            roots_with_content_output_dirs[r] = output_dir
                        groups_with_content.append(export_rel if export_rel else "/")  # 单根/多根都记入
                    if num_groups == 1 and len(roots) == 1:
                        ui.print_success(f"完成，共 {len(translations)} 条 → {Path(csv_path).name}" if csv_path else "完成")
                        if not batch_mode and _is_external_output(output_dir, mod_dir):
                            _rel = export_rel if export_rel else "/"
                            _name = _rel if _rel == "/" or scan_base == mod_dir else f"{Path(mod_dir).name}/{export_rel}"
                            xml_path = generate_load_folders_xml(
                                chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                            )
                            if xml_path:
                                ui.print_info(f"LoadFolders.xml → {xml_path}")
                        return (csv_path, mod_dir)
                elif conflict_resolution == "incremental":
                    if len(roots) > 1:
                        all_keyed, all_def = [], []
                        for r in roots:
                            r_label = rel_path_str(scan_base, r)
                            k, d = template_manager.extract_all_translations(
                                r,
                                import_language,
                                data_source_choice=data_source_choice,
                                has_input_keyed=has_input_keyed,
                                scan_label=r_label,
                            )
                            all_keyed.extend(k)
                            all_def.extend(d)
                        all_keyed, all_def = dedupe_translations_by_key(
                            all_keyed, all_def
                        )
                        translations, csv_path = template_manager.incremental_mode(
                            import_dir=roots[0],
                            import_language=import_language,
                            output_dir=output_dir,
                            output_language=output_language,
                            data_source_choice=data_source_choice,
                            has_input_keyed=has_input_keyed,
                            output_csv=output_csv,
                            input_keyed=all_keyed,
                            input_def=all_def,
                            import_label=label,
                            template_structure=template_structure,
                        )
                    else:
                        translations, csv_path = template_manager.incremental_mode(
                            import_dir=import_dir,
                            import_language=import_language,
                            output_dir=output_dir,
                            output_language=output_language,
                            data_source_choice=data_source_choice,
                            has_input_keyed=has_input_keyed,
                            output_csv=output_csv,
                            import_label=label,
                            template_structure=template_structure,
                        )
                    if translations and csv_path:
                        all_csv_paths.append(csv_path)
                        for r in roots:
                            roots_with_content.add(r)
                            roots_with_content_output_dirs[r] = output_dir
                        groups_with_content.append(export_rel if export_rel else "/")
                        ui.print_success(f"新增 {len(translations)} 条 → {Path(csv_path).name}")
                        if num_groups == 1 and len(roots) == 1:
                            if not batch_mode and _is_external_output(output_dir, mod_dir):
                                _rel = export_rel if export_rel else "/"
                                _name = _rel if _rel == "/" or scan_base == mod_dir else f"{Path(mod_dir).name}/{export_rel}"
                                xml_path = generate_load_folders_xml(
                                    chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                                )
                                if xml_path:
                                    ui.print_info(f"LoadFolders.xml → {xml_path}")
                            return (csv_path, mod_dir)
                    else:
                        ui.print_info("新增模式：无缺少 key")
                        if num_groups == 1 and len(roots) == 1:
                            return None
                elif conflict_resolution in ["rebuild", "new"]:
                    language_dir = config.language_config.get_language_dir(
                        output_path, output_language
                    )
                    if language_dir.exists():
                        try:
                            import shutil

                            for item in language_dir.iterdir():
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            pass  # 已清空，不刷屏
                        except PermissionError as e:
                            ui.print_warning(
                                f"⚠️ 无法删除某些文件（可能是系统文件），跳过：{e}"
                            )
                    if len(roots) > 1:
                        scan_labels_for_roots = compute_scan_labels_for_roots(
                            roots, scan_base
                        )
                        translations, csv_path = template_manager.extract_and_generate_templates_from_roots(
                            import_dirs=roots,
                            import_language=import_language,
                            output_dir=output_dir,
                            output_language=output_language,
                            data_source_choice=data_source_choice,
                            template_structure=template_structure,
                            has_input_keyed=has_input_keyed,
                            output_csv=output_csv,
                            scan_labels=scan_labels_for_roots,
                        )
                    else:
                        translations, csv_path = (
                            template_manager.extract_and_generate_templates(
                                import_dir=import_dir,
                                import_language=import_language,
                                output_dir=output_dir,
                                output_language=output_language,
                                data_source_choice=data_source_choice,
                                template_structure=template_structure,
                                has_input_keyed=has_input_keyed,
                                output_csv=output_csv,
                                scan_label=label,
                            )
                        )
                    if csv_path:
                        all_csv_paths.append(csv_path)
                        for r in roots:
                            roots_with_content.add(r)
                            roots_with_content_output_dirs[r] = output_dir
                        groups_with_content.append(export_rel if export_rel else "/")
                    if num_groups > 1 or len(roots) > 1:
                        ui.print_info(f"  {label} → {len(translations)} 条")
                    else:
                        ui.print_success(f"完成，{len(translations)} 条 → {Path(csv_path).name}" if csv_path else "完成")
                    if num_groups == 1 and len(roots) == 1:
                        if not batch_mode and _is_external_output(output_dir, mod_dir):
                            _rel = export_rel if export_rel else "/"
                            _name = _rel if _rel == "/" or scan_base == mod_dir else f"{Path(mod_dir).name}/{export_rel}"
                            xml_path = generate_load_folders_xml(
                                chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                            )
                            if xml_path:
                                ui.print_info(f"LoadFolders.xml → {xml_path}")
                        return (csv_path, mod_dir)
                else:
                    ui.print_info(f"无效的冲突处理方式: {conflict_resolution}")
                    return None

            # 多组时汇总并返回；若为外部导出则用 groups_with_content 生成 LoadFolders.xml（批量模式不生成单独 xml）
            if num_groups > 1:
                if not batch_mode and multi_root_external and groups_with_content:
                    names_for_xml = [rel if rel != "/" else "/" for rel in groups_with_content]
                    xml_version = Path(mod_dir).name if scan_base != mod_dir else "1.6"
                    xml_path = generate_load_folders_xml(
                        chosen_output_dir,
                        names_for_xml,
                        version=xml_version,
                        mod_dir=load_folders_mod_root,
                    )
                    if xml_path:
                        ui.print_info(f"LoadFolders.xml → {xml_path}")
                    else:
                        ui.print_warning("未生成 LoadFolders.xml，请检查输出目录是否可写")
                if all_csv_paths:
                    ui.print_success(f"完成，{num_groups} 组，{len(all_csv_paths)} 个 CSV")
                    for p in all_csv_paths:
                        ui.print_info(f"   · {Path(p).name}")
                    return (all_csv_paths[0], mod_dir)
                return (all_csv_paths[0], mod_dir) if all_csv_paths else None
            # num_groups==1 且 len(roots)>1（合并根）时，for 循环内已处理但未 return，需在此返回
            if num_groups == 1 and all_csv_paths:
                return (all_csv_paths[0], mod_dir)

        except (OSError, RuntimeError) as e:
            report_handler_error(e, "智能提取失败", mod_dir=mod_dir)
            return None
        except ValueError as e:
            ui.print_error(
                f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
            )
            report_handler_error(e, "配置错误", mod_dir=mod_dir)
            return None

    except (OSError, ImportError, AttributeError) as e:
        report_handler_error(e, "提取模板功能失败")
        return None
    except ValueError as e:
        ui.print_error(
            f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
        )
        report_handler_error(e, "配置错误")
        return None
