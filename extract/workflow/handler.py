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
from typing import Optional, List
from user_config import UserConfigManager
from utils.logging_config import get_logger, log_user_action, log_error_with_context
from utils.interaction import (
    select_mod_path_with_version_detection,
)
from utils.ui_style import ui
from .manager import TemplateManager, find_content_roots, generate_load_folders_xml
from .interaction import InteractionManager


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
        content_roots = find_content_roots(scan_base)
        if scan_base != mod_dir:
            mod_dir_n = mod_dir.replace("\\", "/")
            content_roots = [
                r for r in content_roots
                if r == mod_dir or r.replace("\\", "/").startswith(mod_dir_n + "/")
            ]
        if not content_roots and (Path(mod_dir) / "Defs").exists():
            content_roots = [mod_dir]
        if not content_roots:
            ui.print_error("未找到 Defs 目录，请确认模组路径正确")
            return None
        # 读取 LoadFolders.xml 时用模组根（版本结构下 = scan_base）
        load_folders_mod_root = scan_base
        if len(content_roots) > 1:
            ui.print_success(
                f"检测到 {len(content_roots)} 个汉化目录，将按「Defs 在哪就在同目录生成 Languages」逐一处理"
            )
            try:
                mod_path_base = Path(mod_dir).resolve()
                for r in content_roots:
                    rp = Path(r).resolve()
                    if rp == mod_path_base or mod_path_base in rp.parents:
                        rel = rp.relative_to(mod_path_base)
                    else:
                        rel = r
                    ui.print_info(f"   · {rel}")
            except (ValueError, OSError):
                for r in content_roots:
                    ui.print_info(f"   · {r}")

        # 创建模板管理器和交互管理器
        template_manager = TemplateManager()
        interaction_manager = InteractionManager()

        ui.print_info("=== 开始智能提取模板 ===")
        try:
            # 执行四步智能流程（始终显示输出目录选择，支持外部导出）
            effective_dir = content_roots[0]
            smart_config = interaction_manager.handle_smart_extraction_workflow(
                effective_dir, skip_output_selection=False
            )

            conflict_resolution = smart_config["output_config"]["conflict_resolution"]
            data_source_choice = smart_config["data_sources"]["choice"]
            template_structure = smart_config["template_structure"]
            has_input_keyed = smart_config["data_sources"]["import_status"].get(
                "has_keyed", False
            )
            import_language = smart_config["data_sources"]["import_status"]["language"]
            output_language = smart_config["output_config"]["output_status"]["language"]

            ui.print_info(
                f"智能配置：数据来源={data_source_choice}, 模板结构={template_structure}, 冲突处理={conflict_resolution}"
            )

            output_csv_name = config.language_config.get_value(
                "output_csv", "translations.csv"
            )
            all_csv_paths: List[str] = []
            chosen_output_dir = smart_config["output_config"]["output_dir"]

            def _is_external_output(out_dir: str, base_dir: str) -> bool:
                try:
                    Path(out_dir).resolve().relative_to(Path(base_dir).resolve())
                    return False
                except (ValueError, TypeError):
                    return True

            # 多根且选择外部目录时，各内容根导出到 外部目录/相对路径，并生成 LoadFolders.xml
            multi_root_external = (
                len(content_roots) > 1 and _is_external_output(chosen_output_dir, mod_dir)
            )
            if multi_root_external:
                try:
                    mod_path_base = Path(mod_dir).resolve()
                    rel_names = [
                        str(Path(r).resolve().relative_to(mod_path_base)).replace("\\", "/")
                        for r in content_roots
                    ]
                except (ValueError, OSError):
                    rel_names = [Path(r).name or "." for r in content_roots]
            # 仅对有导出内容的根生成 LoadFolders；版本结构下用「版本/路径」格式以匹配原 mod 取 IfModActive
            roots_with_content: set = set()

            # 单根且外部导出时也按「外部/相对路径」创建子目录（如 Common），与多根行为一致
            single_root_external = (
                len(content_roots) == 1 and _is_external_output(chosen_output_dir, mod_dir)
            )
            # 对每个内容根分别执行；外部导出=外部/相对路径（含单根），模组内=各根
            for root in content_roots:
                import_dir = root
                if single_root_external or multi_root_external:
                    try:
                        rel = Path(root).resolve().relative_to(Path(mod_dir).resolve())
                        output_dir = str(Path(chosen_output_dir) / rel)
                    except (ValueError, OSError):
                        output_dir = str(Path(chosen_output_dir) / (Path(root).name or "."))
                elif len(content_roots) == 1:
                    output_dir = chosen_output_dir
                else:
                    output_dir = root
                output_csv = str(Path(output_dir) / output_csv_name)
                output_path = Path(output_dir)

                if len(content_roots) > 1:
                    ui.print_info(f"正在处理: {Path(root).name or root}")

                # 根据冲突处理方式执行相应操作
                if conflict_resolution == "merge":
                    ui.print_info("合并模式")
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
                        roots_with_content.add(root)
                    if len(content_roots) == 1:
                        ui.print_success(f"智能提取完成！共提取 {len(translations)} 条翻译")
                        if csv_path:
                            ui.print_info(f"CSV文件：{csv_path}")
                        ui.print_info(f"输出目录：{output_dir}")
                        if _is_external_output(output_dir, mod_dir):
                            _rel = (
                                "."
                                if Path(root).resolve() == Path(mod_dir).resolve()
                                else str(Path(root).resolve().relative_to(Path(mod_dir).resolve())).replace("\\", "/")
                            )
                            _name = _rel
                            if scan_base != mod_dir and _rel != ".":
                                _name = f"{Path(mod_dir).name}/{_rel}"
                            xml_path = generate_load_folders_xml(
                                chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                            )
                            if xml_path:
                                ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                        return (csv_path, mod_dir)
                elif conflict_resolution == "incremental":
                    ui.print_info("新增模式")
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
                        roots_with_content.add(root)
                        ui.print_success(f"新增模式完成！新增了 {len(translations)} 条翻译")
                        ui.print_info(f"CSV文件：{csv_path}")
                        ui.print_info(f"输出目录：{output_dir}")
                        if len(content_roots) == 1:
                            if _is_external_output(output_dir, mod_dir):
                                _rel = (
                                    "."
                                    if Path(root).resolve() == Path(mod_dir).resolve()
                                    else str(Path(root).resolve().relative_to(Path(mod_dir).resolve())).replace("\\", "/")
                                )
                                _name = _rel if _rel == "." or scan_base == mod_dir else f"{Path(mod_dir).name}/{_rel}"
                                xml_path = generate_load_folders_xml(
                                    chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                                )
                                if xml_path:
                                    ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                            return (csv_path, mod_dir)
                    else:
                        ui.print_success("新增模式完成！没有发现缺少的key")
                        if len(content_roots) == 1:
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
                        roots_with_content.add(root)
                    ui.print_success(f"重建完成！共提取 {len(translations)} 条翻译")
                    ui.print_info(f"CSV文件：{csv_path}")
                    ui.print_info(f"输出目录：{output_dir}")
                    if len(content_roots) == 1:
                        if _is_external_output(output_dir, mod_dir):
                            _rel = (
                                "."
                                if Path(root).resolve() == Path(mod_dir).resolve()
                                else str(Path(root).resolve().relative_to(Path(mod_dir).resolve())).replace("\\", "/")
                            )
                            _name = _rel if _rel == "." or scan_base == mod_dir else f"{Path(mod_dir).name}/{_rel}"
                            xml_path = generate_load_folders_xml(
                                chosen_output_dir, [_name], mod_dir=load_folders_mod_root
                            )
                            if xml_path:
                                ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                        return (csv_path, mod_dir)
                else:
                    ui.print_info(f"无效的冲突处理方式: {conflict_resolution}")
                    return None

            # 多根时汇总并返回；若为外部导出则生成 LoadFolders.xml（仅含实际有导出的根，版本结构下用 1.6/Mods/xxx 以匹配原 mod 取 IfModActive）
            if len(content_roots) > 1:
                if multi_root_external and rel_names:
                    # 只对有导出内容的根生成 <li>
                    indices_with_content = [i for i, r in enumerate(content_roots) if r in roots_with_content]
                    names_for_xml = [rel_names[i] for i in indices_with_content if i < len(rel_names)]
                    if scan_base != mod_dir:
                        version_prefix = Path(mod_dir).name
                        names_for_xml = [f"{version_prefix}/{n}".replace("\\", "/") for n in names_for_xml]
                    if names_for_xml:
                        xml_path = generate_load_folders_xml(
                            chosen_output_dir, names_for_xml, mod_dir=load_folders_mod_root
                        )
                        if xml_path:
                            ui.print_info(f"已生成 LoadFolders.xml：{xml_path}")
                        else:
                            ui.print_warning("未生成 LoadFolders.xml，请检查输出目录是否可写")
                if all_csv_paths:
                    ui.print_success(
                        f"智能提取完成！共处理 {len(content_roots)} 个目录，生成 CSV: {len(all_csv_paths)} 个"
                    )
                    for p in all_csv_paths:
                        ui.print_info(f"   · {p}")
                    return (all_csv_paths[0], mod_dir)
                return (all_csv_paths[0], mod_dir) if all_csv_paths else None

        except (OSError, IOError, ValueError, RuntimeError) as e:
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

    except (OSError, IOError, ValueError, ImportError, AttributeError) as e:
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
