"""
RimWorld 翻译提取主处理器

负责协调整个翻译提取流程，包括：
- 用户交互和配置选择
- 智能工作流程管理
- 冲突处理和模式选择
- 错误处理和日志记录
"""

import re
from pathlib import Path
from typing import Optional, List, Tuple
from user_config import UserConfigManager
from utils.logging_config import get_logger, log_user_action, log_error_with_context
from utils.interaction import (
    select_mod_path_with_version_detection,
)
from utils.ui_style import ui, _get_mod_display_name
from .manager import (
    TemplateManager,
    find_content_roots,
    generate_load_folders_xml,
    get_content_roots_from_load_folders,
)
from .interaction import InteractionManager


def _sanitize_mod_name_for_filename(name: str) -> str:
    """将模组名转为安全的文件名（替换非法字符）"""
    import re
    s = re.sub(r'[\\/:*?"<>|]', "_", str(name).strip())
    return s[:64] if s else ""


def _short_csv_basename(mod_name: str, export_rel: str) -> str:
    """生成简短 CSV 名。根目录用 {mod_name}_extracted.csv；子路径用 R_M_Biotech_extracted.csv 格式"""
    if not export_rel:
        return f"{mod_name}_extracted.csv" if mod_name else "extracted.csv"
    mod_prefix = (mod_name[0] if mod_name else "").upper()
    parts = [p for p in export_rel.replace("\\", "/").split("/") if p]
    if not parts:
        return f"{mod_prefix}_extracted.csv" if mod_prefix else "extracted.csv"
    initials = "_".join(p[0].upper() for p in parts[:-1])
    last = parts[-1]
    if initials:
        base = f"{mod_prefix}_{initials}_{last}"
    else:
        base = f"{mod_prefix}_{last}"
    return f"{base}_extracted.csv"


def _dedupe_translations_by_key(
    keyed_list: List, def_list: List
) -> Tuple[List, List]:
    """多根合并时按 key 去重，避免同一 Keyed/Def 目录被多个根解析到导致重复。"""
    seen_k, seen_d = set(), set()
    out_k, out_d = [], []
    for item in keyed_list:
        k = item[0] if item else None
        if k is not None and k not in seen_k:
            seen_k.add(k)
            out_k.append(item)
    for item in def_list:
        k = item[0] if item else None
        if k is not None and k not in seen_d:
            seen_d.add(k)
            out_d.append(item)
    return out_k, out_d


def handle_extract() -> Optional[tuple]:
    """处理提取模板功能

    Returns:
        Optional[tuple]: (csv_path, mod_dir) 元组，如果失败则返回None
    """
    logger = get_logger(f"{__name__}.handle_extract")
    config = UserConfigManager()

    print(f"日志文件路径：{config.system_config.get_value('log_file')}")
    if config.system_config.get_value("debug_mode"):
        print("调试模式已开启，详细日志见日志文件。")

    logger.info("开始处理提取模板功能")

    try:
        # 选择模组目录（可能返回 tuple，如 (path, type)，统一取路径）
        result = select_mod_path_with_version_detection()
        if not result:
            logger.info("用户取消了模组目录选择")
            return None
        mod_dir = result[0] if isinstance(result, tuple) else result

        # 记录用户操作
        log_user_action("选择模组目录", mod_dir=mod_dir)

        # 若当前路径在「版本号结构」下（如 mod/1.6），用模组根做扫描，避免漏掉根下 Defs；再只保留所选版本下的根
        def _is_version_number(name: str) -> bool:
            return bool(re.match(r"^v?(\d+\.)+\d+$", name.strip()))

        scan_base = mod_dir
        mod_path = Path(mod_dir)
        parent = mod_path.parent
        if (
            mod_path.is_dir()
            and parent.is_dir()
            and (parent / "About").exists()
            and any(
                d.is_dir() and _is_version_number(d.name)
                for d in parent.iterdir()
            )
        ):
            scan_base = str(parent)
        en_lang = config.language_config.get_value("en_language", "English")
        # 版本结构：先选版本 → 扫 LoadFolders；无则扫版本目录+根目录，合并导出到一个 Languages
        use_load_folders = False
        if scan_base != mod_dir:
            version_name = mod_path.name
            load_folders_roots = get_content_roots_from_load_folders(
                scan_base, version_name
            )
            if load_folders_roots:
                use_load_folders = True
                content_roots = load_folders_roots
                ui.print_info(
                    f"已从 LoadFolders.xml 读取 <v{version_name}> 共 {len(content_roots)} 个内容根"
                )
            else:
                # 无 LoadFolders：仅所选版本目录 + 模组根（若根下含 Defs/Languages），不包含其他版本目录
                all_found = find_content_roots(scan_base, language=en_lang)
                mod_dir_resolved = str(Path(mod_dir).resolve())
                scan_base_resolved = str(Path(scan_base).resolve())
                content_roots = [
                    r for r in all_found
                    if r == mod_dir_resolved
                    or r == scan_base_resolved
                    or r.replace("\\", "/").startswith(mod_dir_resolved.replace("\\", "/") + "/")
                ]
                # 所选版本目录放首位，供智能流程默认检测/输出
                if content_roots and mod_dir_resolved in content_roots:
                    content_roots = [mod_dir_resolved] + [r for r in content_roots if r != mod_dir_resolved]
                if content_roots:
                    ui.print_info(
                        "未找到 LoadFolders.xml，已按所选版本目录+模组根扫描，合并导出到 Languages"
                    )
        else:
            # 用户选择模组根时，也尝试从 LoadFolders.xml 读取（Defs 可能在 1.6/ 等版本子目录下）
            content_roots = find_content_roots(scan_base, language=en_lang)
            for ver in ("1.6", "1.5"):
                lf_roots = get_content_roots_from_load_folders(scan_base, ver)
                if lf_roots:
                    content_roots = lf_roots
                    ui.print_info(
                        f"已从 LoadFolders.xml 读取 <v{ver}> 共 {len(content_roots)} 个内容根"
                    )
                    use_load_folders = True
                    break
        if not content_roots and (Path(mod_dir) / "Defs").exists():
            content_roots = [mod_dir]
        if not content_roots:
            try:
                content_roots = find_content_roots(mod_dir, language=en_lang)
            except (OSError, ValueError, TypeError, AttributeError):
                pass
        if not content_roots:
            ui.print_error("未找到 Defs 或 Languages 目录，请确认模组路径正确")
            return None
        load_folders_mod_root = scan_base
        # 构建 root_groups：(roots, export_rel)。版本组只用版本路径单根，Defs/Languages 均「版本优先、根目录回退」
        if scan_base == mod_dir:
            # 若有 content_roots（来自 LoadFolders 或 find_content_roots），用其扫描；否则仅用模组根
            root_groups: List[tuple] = (
                [(content_roots, "")] if content_roots else [([mod_dir], "")]
            )
        elif not use_load_folders:
            root_groups = [(content_roots, "")]
        else:
            root_groups = []
            seen_version = False
            for full in content_roots:
                try:
                    rel_str = str(Path(full).resolve().relative_to(Path(scan_base).resolve())).replace("\\", "/")
                except (ValueError, OSError):
                    rel_str = Path(full).name or ""
                if rel_str in ("", ".", version_name):
                    if not seen_version:
                        # 版本组：传版本路径 mod_dir（如 v1.6），提取时 Defs/Keyed 自动「版本有则用版本，无则用根」
                        root_groups.append(([mod_dir], ""))
                        seen_version = True
                else:
                    root_groups.append(([full], rel_str))
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

        ui.print_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程（始终显示输出目录选择，支持外部导出）
            effective_dir = root_groups[0][0][0]
            smart_config = interaction_manager.handle_smart_extraction_workflow(
                effective_dir,
                skip_output_selection=False,
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
                    # 目录存在即视为有 Keyed，不强制要求 *.xml（避免漏检）
                    if keyed_dir.exists():
                        has_input_keyed = True
                        break
                    root_parent = config.language_config.get_language_subdir(
                        str(Path(r).parent), import_language, "keyed"
                    )
                    if root_parent.exists():
                        has_input_keyed = True
                        break
            output_language = smart_config["output_config"]["output_status"]["language"]

            ui.print_info(
                f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}"
            )

            default_csv_name = config.language_config.get_value(
                "output_csv", "translations.csv"
            )
            mod_root = load_folders_mod_root or mod_dir
            mod_name = _sanitize_mod_name_for_filename(_get_mod_display_name(mod_root))
            all_csv_paths: List[str] = []
            chosen_output_dir = smart_config["output_config"]["output_dir"]
            rel_names: List[str] = []

            def _is_external_output(out_dir: str, base_dir: str) -> bool:
                try:
                    Path(out_dir).resolve().relative_to(Path(base_dir).resolve())
                    return False
                except (ValueError, TypeError):
                    return True

            rel_base = Path(load_folders_mod_root).resolve() if load_folders_mod_root else Path(mod_dir).resolve()
            multi_root_external = num_groups > 1 and _is_external_output(chosen_output_dir, mod_dir)
            groups_with_content: List[str] = []  # export_rel 列表，用于生成 LoadFolders.xml
            roots_with_content: set = set()
            roots_with_content_output_dirs: dict = {}

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

                if num_groups > 1 or len(roots) > 1:
                    label = export_rel if export_rel else "/"
                    ui.print_info(f"正在处理: {label}")

                # 根据冲突处理方式执行相应操作
                if conflict_resolution == "merge":
                    ui.print_info("合并模式")
                    if len(roots) > 1:
                        all_keyed, all_def = [], []
                        for r in roots:
                            k, d = template_manager.extract_all_translations(
                                r, import_language,
                                data_source_choice=data_source_choice,
                                has_input_keyed=has_input_keyed,
                            )
                            all_keyed.extend(k)
                            all_def.extend(d)
                        all_keyed, all_def = _dedupe_translations_by_key(
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
                        )
                    if csv_path:
                        all_csv_paths.append(csv_path)
                        for r in roots:
                            roots_with_content.add(r)
                            roots_with_content_output_dirs[r] = output_dir
                        groups_with_content.append(export_rel if export_rel else "/")  # 单根/多根都记入
                    if num_groups == 1 and len(roots) == 1:
                        ui.print_success(f"智能提取完成！共提取 {len(translations)} 条翻译")
                        if csv_path:
                            ui.print_info(f"CSV文件：{csv_path}")
                        ui.print_info(f"输出目录：{output_dir}")
                        if _is_external_output(output_dir, mod_dir):
                            _rel = export_rel if export_rel else "/"
                            _name = _rel if _rel == "/" or scan_base == mod_dir else f"{Path(mod_dir).name}/{export_rel}"
                            xml_path = generate_load_folders_xml(
                                chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                            )
                            if xml_path:
                                ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                        return (csv_path, mod_dir)
                elif conflict_resolution == "incremental":
                    ui.print_info("新增模式")
                    if len(roots) > 1:
                        all_keyed, all_def = [], []
                        for r in roots:
                            k, d = template_manager.extract_all_translations(
                                r, import_language,
                                data_source_choice=data_source_choice,
                                has_input_keyed=has_input_keyed,
                            )
                            all_keyed.extend(k)
                            all_def.extend(d)
                        all_keyed, all_def = _dedupe_translations_by_key(
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
                        )
                    if translations:
                        all_csv_paths.append(csv_path)
                        for r in roots:
                            roots_with_content.add(r)
                            roots_with_content_output_dirs[r] = output_dir
                        groups_with_content.append(export_rel if export_rel else "/")
                        ui.print_success(f"新增模式完成！新增了 {len(translations)} 条翻译")
                        ui.print_info(f"CSV文件：{csv_path}")
                        ui.print_info(f"输出目录：{output_dir}")
                        if num_groups == 1 and len(roots) == 1:
                            if _is_external_output(output_dir, mod_dir):
                                _rel = export_rel if export_rel else "/"
                                _name = _rel if _rel == "/" or scan_base == mod_dir else f"{Path(mod_dir).name}/{export_rel}"
                                xml_path = generate_load_folders_xml(
                                    chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                                )
                                if xml_path:
                                    ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                            return (csv_path, mod_dir)
                    else:
                        ui.print_success("新增模式完成！没有发现缺少的key")
                        if num_groups == 1 and len(roots) == 1:
                            return None
                elif conflict_resolution in ["rebuild", "new"]:
                    ui.print_info("重建模式")
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
                            ui.print_info(f"🗑️ 已清空输出目录：{language_dir}")
                        except PermissionError as e:
                            ui.print_warning(
                                f"⚠️ 无法删除某些文件（可能是系统文件），跳过：{e}"
                            )
                    if len(roots) > 1:
                        translations, csv_path = template_manager.extract_and_generate_templates_from_roots(
                            import_dirs=roots,
                            import_language=import_language,
                            output_dir=output_dir,
                            output_language=output_language,
                            data_source_choice=data_source_choice,
                            template_structure=template_structure,
                            has_input_keyed=has_input_keyed,
                            output_csv=output_csv,
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
                            )
                        )
                    if csv_path:
                        all_csv_paths.append(csv_path)
                        for r in roots:
                            roots_with_content.add(r)
                            roots_with_content_output_dirs[r] = output_dir
                        groups_with_content.append(export_rel if export_rel else "/")
                    ui.print_success(f"重建完成！共提取 {len(translations)} 条翻译")
                    ui.print_info(f"CSV文件：{csv_path}")
                    ui.print_info(f"输出目录：{output_dir}")
                    if num_groups == 1 and len(roots) == 1:
                        if _is_external_output(output_dir, mod_dir):
                            _rel = export_rel if export_rel else "/"
                            _name = _rel if _rel == "/" or scan_base == mod_dir else f"{Path(mod_dir).name}/{export_rel}"
                            xml_path = generate_load_folders_xml(
                                chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                            )
                            if xml_path:
                                ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                        return (csv_path, mod_dir)
                else:
                    ui.print_info(f"无效的冲突处理方式: {conflict_resolution}")
                    return None

            # 多组时汇总并返回；若为外部导出则用 groups_with_content 生成 LoadFolders.xml
            if num_groups > 1:
                if multi_root_external and groups_with_content:
                    names_for_xml = [rel if rel != "/" else "/" for rel in groups_with_content]
                    xml_version = Path(mod_dir).name if scan_base != mod_dir else "1.6"
                    xml_path = generate_load_folders_xml(
                        chosen_output_dir,
                        names_for_xml,
                        version=xml_version,
                        mod_dir=load_folders_mod_root,
                    )
                    if xml_path:
                        ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                    else:
                        ui.print_warning("未生成 LoadFolders.xml，请检查输出目录是否可写")
                if all_csv_paths:
                    ui.print_success(
                        f"智能提取完成！共处理 {num_groups} 个导出组，生成 CSV: {len(all_csv_paths)} 个"
                    )
                    for p in all_csv_paths:
                        ui.print_info(f"   · {p}")
                    return (all_csv_paths[0], mod_dir)
                return (all_csv_paths[0], mod_dir) if all_csv_paths else None

        except (OSError, RuntimeError) as e:
            ui.print_error(f"智能提取失败: {str(e)}")
            log_error_with_context(e, "智能提取失败", mod_dir=mod_dir)
            if config.system_config.get_value("debug_mode", False):
                import traceback

                traceback.print_exc()
            return None
        except ValueError as e:
            ui.print_error(
                f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
            )
            log_error_with_context(e, "配置错误", mod_dir=mod_dir)
            if config.system_config.get_value("debug_mode", False):
                import traceback

                traceback.print_exc()
            return None

    except (OSError, ImportError, AttributeError) as e:
        ui.print_error(f"提取模板功能失败: {str(e)}")
        log_error_with_context(e, "提取模板功能失败")
        if config.system_config.get_value("debug_mode", False):
            import traceback

            traceback.print_exc()
        return None
    except ValueError as e:
        ui.print_error(
            f"❌ 配置错误：{e}\n请检查 config.py 或用户配置文件，或尝试重新加载配置。"
        )
        log_error_with_context(e, "配置错误")
        if config.system_config.get_value("debug_mode", False):
            import traceback

            traceback.print_exc()
        return None
