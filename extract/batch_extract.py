"""
批量提取 - Vanilla 前缀模组批量提取翻译模板
归属 extract 模块，职责：批量扫描 Workshop 并调用单次提取
"""

import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from utils.constants import TOTAL_CSV_NAME
from utils.csv_utils import open_csv_reader, open_csv_writer
from utils.interaction import prompt_choose_from_list, safe_input
from utils.rimworld_about import (
    get_mod_name_from_about,
    get_package_id_from_about,
    sanitize_mod_name_for_path,
)
from utils.ui_style import ui


def _batch_extract_one(
    args: Tuple[str, str, str, str, str]
) -> Tuple[str, str, str, bool, Optional[str]]:
    """多进程 worker：执行单个模组提取。返回 (mod_name, mod_dir, safe_name, success, error_msg)。"""
    mod_dir, out_dir, batch_version, mod_name, safe_name = args
    try:
        from extract.workflow.handler import handle_extract

        ret = handle_extract(
            batch_mod_dir=mod_dir,
            batch_output_dir=out_dir,
            batch_version=batch_version,
        )
        ok = ret is not None
        err = None if ok else "提取返回 None"
        return (mod_name, mod_dir, safe_name, ok, err)
    except Exception as e:  # pylint: disable=broad-except
        return (mod_name, mod_dir, safe_name, False, str(e))


DEFAULT_WORKSHOP_CONTENT = (
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100"
)


def scan_vanilla_mods(workshop_content_dir: str) -> List[Tuple[str, str]]:
    """
    扫描 Workshop 目录，返回名字以 Vanilla 开头的模组列表。

    Returns:
        [(mod_dir_abs, mod_display_name), ...]
    """
    workshop = Path(workshop_content_dir)
    if not workshop.is_dir():
        return []
    result: List[Tuple[str, str]] = []
    for sub in workshop.iterdir():
        if not sub.is_dir():
            continue
        name = get_mod_name_from_about(str(sub))
        if name and name.strip().startswith("Vanilla"):
            result.append((str(sub.resolve()), name.strip()))
    return result


def handle_batch_vanilla_extract() -> Optional[str]:
    """批量提取：仅处理 About 名字前缀为 Vanilla 的模组，输出到 指定文件夹/模组名/。
    成功时返回输出根目录路径，否则返回 None。"""
    ui.print_section_header("批量提取（Vanilla 前缀模组）", ui.Icons.BATCH)

    workshop_dir = DEFAULT_WORKSHOP_CONTENT
    ui.print_info(f"Workshop 目录（可回车使用默认）: {workshop_dir}")
    raw = safe_input(ui.get_input_prompt("Workshop 目录", default=workshop_dir))
    if raw is None:
        return
    if raw.strip():
        workshop_dir = raw.strip()
    workshop_path = Path(workshop_dir)
    if not workshop_path.is_dir():
        ui.print_error(f"目录不存在: {workshop_dir}")
        return

    vanilla_list = scan_vanilla_mods(workshop_dir)
    if not vanilla_list:
        ui.print_warning(
            "未找到名字以 Vanilla 开头的模组，请确认路径与 About/About.xml 中的 <name>。"
        )
        return
    ui.print_success(f"找到 {len(vanilla_list)} 个 Vanilla 前缀模组")
    ui.print_header("选择游戏版本")
    ui.print_info("批量提取将统一使用所选版本，不会自动回退到其他版本。")
    batch_version = prompt_choose_from_list(["1.6", "1.5"], "请选择版本：", default="1")
    if batch_version is None:
        return
    ui.print_success(f"已选择版本: {batch_version}")

    for mod_dir, mod_name in vanilla_list:
        ui.print_info(f"  · {mod_name}")

    ui.print_header("选择输出根目录")
    out_prompt = "请输入输出根目录（每个模组将导出到 该目录/模组名/，例如 123 即 123/Vanilla Christmas Expanded/）"
    out_raw = safe_input(ui.get_input_prompt(out_prompt))
    if out_raw is None:
        return
    output_base = (out_raw or "").strip()
    if not output_base:
        ui.print_error("未输入输出根目录，已取消")
        return
    output_base_path = Path(output_base)
    try:
        output_base_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        ui.print_error(f"无法创建输出根目录: {e}")
        return

    workers_prompt = safe_input(
        ui.get_input_prompt("并行数（1=顺序，2-8 推荐 4）", default="4")
    )
    if workers_prompt is None:
        return
    try:
        max_workers = max(1, min(8, int((workers_prompt or "4").strip())))
    except ValueError:
        max_workers = 4
    if max_workers == 1:
        ui.print_info("顺序执行（单线程）")
    else:
        ui.print_info(f"多进程并行，workers={max_workers}")

    success_count = 0
    failed: List[Tuple[str, str, str]] = []
    success_list: List[Tuple[str, str, str]] = []  # (mod_dir, mod_name, safe_name)

    tasks = []
    for mod_dir, mod_name in vanilla_list:
        safe_name = sanitize_mod_name_for_path(mod_name)
        if not safe_name:
            safe_name = Path(mod_dir).name
        out_dir = str(output_base_path / safe_name)
        tasks.append((mod_dir, out_dir, batch_version, mod_name, safe_name))

    if max_workers <= 1:
        from extract.workflow.handler import handle_extract

        for mod_dir, out_dir, _bv, mod_name, safe_name in tasks:
            ui.print_info(f"正在提取: {mod_name} -> {out_dir}")
            try:
                ret = handle_extract(
                    batch_mod_dir=mod_dir,
                    batch_output_dir=out_dir,
                    batch_version=batch_version,
                )
                if ret is not None:
                    success_count += 1
                    success_list.append((mod_dir, mod_name, safe_name))
                else:
                    failed.append((mod_name, mod_dir, "提取返回 None"))
            except Exception as e:  # pylint: disable=broad-except
                failed.append((mod_name, mod_dir, str(e)))
                ui.print_warning(f"  失败: {e}")
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(_batch_extract_one, t): t for t in tasks
            }
            for future in as_completed(future_to_task):
                mod_name, mod_dir, safe_name, ok, err = future.result()
                if ok:
                    success_count += 1
                    success_list.append((mod_dir, mod_name, safe_name))
                    ui.print_info(f"完成: {mod_name}")
                else:
                    failed.append((mod_name, mod_dir, err or "未知错误"))
                    ui.print_warning(f"失败: {mod_name} - {err}")

    if success_list:
        from extract.workflow.manager import (
            _parse_load_folders_from_mod,
            generate_total_load_folders_xml,
        )

        total_entries: List[Tuple[str, Dict[str, str], Optional[str]]] = []
        for mod_dir, mod_name, safe_name in success_list:
            package_id = get_package_id_from_about(mod_dir)
            li_attrs, ordered_paths = _parse_load_folders_from_mod(
                mod_dir, batch_version
            )
            comment_first = f"<!-- {mod_name} -->"
            if not ordered_paths:
                attrs = {"IfModActive": package_id} if package_id else {}
                total_entries.append((safe_name, attrs, comment_first))
            else:
                seen_out: Set[str] = set()
                for i, path in enumerate(ordered_paths):
                    path_norm = (path or "").strip().replace("\\", "/")
                    if path_norm in ("", "/", "."):
                        out_path = safe_name
                    else:
                        out_path = f"{safe_name}/{path_norm}"
                    if out_path in seen_out:
                        continue
                    seen_out.add(out_path)
                    attrs = dict(li_attrs.get(path, {}))
                    if not attrs and package_id:
                        attrs = {"IfModActive": package_id}
                    total_entries.append(
                        (out_path, attrs, comment_first if i == 0 else None)
                    )
        xml_path = generate_total_load_folders_xml(
            str(output_base_path),
            batch_version,
            total_entries,
        )
        if xml_path:
            ui.print_success(f"已生成总 LoadFolders.xml：{xml_path}")
        else:
            ui.print_warning("未生成总 LoadFolders.xml，请检查输出目录是否可写")

        try:
            from user_config import UserConfigManager

            language = UserConfigManager.get_instance().language_config.get_default_cn_language()
            total_rows: List[Dict[str, str]] = []
            header: Optional[List[str]] = None
            for _mod_dir, _mod_name, safe_name in success_list:
                mod_root = output_base_path / safe_name
                if not mod_root.is_dir():
                    continue
                for lang_parent in mod_root.rglob("Languages"):
                    lang_dir = lang_parent / language
                    if not lang_dir.is_dir():
                        continue
                    content_root = lang_parent.parent
                    try:
                        mod_path = str(
                            content_root.relative_to(output_base_path)
                        ).replace("\\", "/")
                    except ValueError:
                        mod_path = safe_name
                    for csv_file in lang_dir.glob("*.csv"):
                        with open_csv_reader(csv_file) as f:
                            reader = csv.DictReader(f)
                            if header is None and reader.fieldnames:
                                header = list(reader.fieldnames) + ["mod"]
                            for row in reader:
                                row["mod"] = mod_path
                                total_rows.append(row)
            if header and total_rows:
                total_csv_path = output_base_path / TOTAL_CSV_NAME
                with open_csv_writer(total_csv_path) as f:
                    writer = csv.DictWriter(
                        f, fieldnames=header, extrasaction="ignore"
                    )
                    writer.writeheader()
                    writer.writerows(total_rows)
                ui.print_success(
                    f"已生成总 CSV：{total_csv_path}（共 {len(total_rows)} 条，含 mod 列）"
                )
            else:
                ui.print_info("未找到可合并的模组 CSV，跳过总 CSV 生成")
        except (OSError, IOError, PermissionError) as e:
            ui.print_warning(f"生成总 CSV 时出错: {e}")

    ui.print_section_header("批量提取完成", ui.Icons.SUCCESS)
    ui.print_info(f"成功: {success_count}，失败: {len(failed)}")
    if failed:
        for mod_name, mod_dir, reason in failed:
            ui.print_warning(f"  · {mod_name}: {reason}")
    if success_count > 0:
        return str(output_base_path)
    return None
