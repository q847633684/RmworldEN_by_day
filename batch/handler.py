"""
批量处理处理器
处理多个模组的批量操作
"""

import csv
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from utils.constants import CSV_TRANSLATION_HEADER
from utils.csv_utils import open_csv_reader, open_csv_writer
from utils.interaction import prompt_choose_from_list, safe_input
from utils.rimworld_about import (
    get_mod_name_from_about,
    get_package_id_from_about,
    sanitize_mod_name_for_path,
)
from utils.ui_style import ui
from extract.workflow.manager import get_version_dirs_from_fs

TOTAL_CSV_NAME = "total_translations.csv"

# 将选择的 1.6 或 1.5 下所有 Languages/ChineseSimplified 里的 Keyed 和 DefInjected 汇总到根目录：
#   Languages/ChineseSimplified/Keyed/ 和 Languages/ChineseSimplified/DefInjected/
# 使用原始文件名；同名时在扩展名前加序号 1、2、3…（如 AbilityDef1.xml），不覆盖。


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


# RimWorld Workshop 默认路径 (content/294100 为 RimWorld 的 appid 对应 workshop)
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


def handle_batch_vanilla_extract():
    """批量提取：仅处理 About 名字前缀为 Vanilla 的模组，输出到 指定文件夹/模组名/。"""
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
        ui.print_warning("未找到名字以 Vanilla 开头的模组，请确认路径与 About/About.xml 中的 <name>。")
        return
    ui.print_success(f"找到 {len(vanilla_list)} 个 Vanilla 前缀模组")
    ui.print_header("选择游戏版本")
    ui.print_info("批量提取将统一使用所选版本，不会自动回退到其他版本。")
    batch_version = prompt_choose_from_list(
        ["1.6", "1.5"], "请选择版本：", default="1"
    )
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

    # 并行数：1=顺序执行，2-8 推荐 4
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
                executor.submit(_batch_extract_one, t): t
                for t in tasks
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

    # 在输出根目录生成一个总的 LoadFolders.xml：按各模组原 LoadFolders 展开，路径前加模组文件夹名，
    # 保留原有 IfModActive/IfModNotActive；无属性的条目用该模组 About 的 packageId 作为 IfModActive。
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
                # 无 LoadFolders 或为空：仅一条，模组根目录，用 packageId 作为 IfModActive
                attrs = {"IfModActive": package_id} if package_id else {}
                total_entries.append((safe_name, attrs, comment_first))
            else:
                # 总 XML 与各模组原 LoadFolders 一致，不合并根路径；无属性路径的「合并到一个 Languages」已在提取侧处理
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
                    total_entries.append((out_path, attrs, comment_first if i == 0 else None))
        xml_path = generate_total_load_folders_xml(
            str(output_base_path),
            batch_version,
            total_entries,
        )
        if xml_path:
            ui.print_success(f"已生成总 LoadFolders.xml：{xml_path}")
        else:
            ui.print_warning("未生成总 LoadFolders.xml，请检查输出目录是否可写")

        # 生成总 CSV：合并各模组 CSV，增加 mod 列便于批量导入时 key+路径 双校验
        try:
            from user_config import UserConfigManager
            language = UserConfigManager.get_instance().language_config.get_value(
                "cn_language", "ChineseSimplified"
            )
            total_rows: List[Dict[str, str]] = []
            header: Optional[List[str]] = None
            for _mod_dir, _mod_name, safe_name in success_list:
                lang_dir = output_base_path / safe_name / "Languages" / language
                if not lang_dir.is_dir():
                    continue
                for csv_file in lang_dir.glob("*.csv"):
                    with open_csv_reader(csv_file) as f:
                        reader = csv.DictReader(f)
                        if header is None and reader.fieldnames:
                            header = list(reader.fieldnames) + ["mod"]
                        for row in reader:
                            row["mod"] = safe_name
                            total_rows.append(row)
            if header and total_rows:
                total_csv_path = output_base_path / TOTAL_CSV_NAME
                with open_csv_writer(total_csv_path) as f:
                    writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(total_rows)
                ui.print_success(f"已生成总 CSV：{total_csv_path}（共 {len(total_rows)} 条，含 mod 列）")
            else:
                ui.print_info("未找到可合并的模组 CSV，跳过总 CSV 生成")
        except (OSError, IOError, PermissionError) as e:
            ui.print_warning(f"生成总 CSV 时出错: {e}")

    ui.print_section_header("批量提取完成", ui.Icons.SUCCESS)
    ui.print_info(f"成功: {success_count}，失败: {len(failed)}")
    if failed:
        for mod_name, mod_dir, reason in failed:
            ui.print_warning(f"  · {mod_name}: {reason}")


def _unique_dest_path(dest_dir: Path, rel_path: str, used_names: Set[str]) -> Path:
    """生成唯一目标路径，同名时在扩展名前加序号 1、2、3…"""
    rel_norm = rel_path.replace("\\", "/")
    dest_file = dest_dir / rel_norm
    base = dest_file.parent
    stem = dest_file.stem
    suffix = dest_file.suffix
    if rel_norm not in used_names:
        used_names.add(rel_norm)
        return dest_file
    n = 1
    while True:
        new_name = f"{stem}{n}{suffix}"
        if base != dest_dir:
            new_rel = str(base.relative_to(dest_dir)).replace("\\", "/") + "/" + new_name
        else:
            new_rel = new_name
        if new_rel not in used_names:
            used_names.add(new_rel)
            return (base / new_name) if base != dest_dir else (dest_dir / new_name)
        n += 1


def aggregate_chinese_translations_to_root(
    root_dir: str,
    versions: Optional[List[str]] = None,
    language: Optional[str] = None,
    include_root: bool = True,
) -> Tuple[int, int]:
    """
    将根目录下各模组的 Languages/ChineseSimplified 的 Keyed 和 DefInjected 汇总到根目录。
    同名文件在扩展名前加序号 1、2、3…，不覆盖。

    Args:
        root_dir: 批量导出根目录（含多个模组子目录）
        versions: 可选，版本目录名列表如 ["1.5","1.6"]；为 None 时自动检测根目录下的版本号子目录
        language: 语言目录名，默认 ChineseSimplified
        include_root: 是否同时扫描根目录；选单个版本时应为 False，避免 root 的 rglob 扫到其他版本

    Returns:
        (keyed_count, definjected_count) 复制的文件数
    """
    from user_config import UserConfigManager
    config = UserConfigManager.get_instance()
    lang = language or config.language_config.get_value("cn_language", "ChineseSimplified")
    keyed_name = config.language_config.get_value("keyed_dir", "Keyed")
    def_name = config.language_config.get_value("definjected_dir", "DefInjected")

    root = Path(root_dir)
    if not root.is_dir():
        return 0, 0

    out_keyed = root / "Languages" / lang / keyed_name
    out_def = root / "Languages" / lang / def_name
    out_keyed.mkdir(parents=True, exist_ok=True)
    out_def.mkdir(parents=True, exist_ok=True)

    used_keyed: Set[str] = set()
    used_def: Set[str] = set()
    keyed_count = 0
    def_count = 0

    def _collect_and_copy(src_dir: Path, out_dir: Path, used: Set[str]) -> int:
        cnt = 0
        if not src_dir.is_dir():
            return 0
        for f in src_dir.rglob("*.xml"):
            if not f.is_file():
                continue
            rel = str(f.relative_to(src_dir)).replace("\\", "/")
            dest_path = _unique_dest_path(out_dir, rel, used)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest_path)
            cnt += 1
        return cnt

    # 递归查找所有 Languages/lang/Keyed 和 Languages/lang/DefInjected 目录（含嵌套如 1.6/mod/1.6/ModCompatibility/Quirks/Languages/...）
    def _find_lang_dirs(scan_root: Path) -> List[Tuple[Path, Path]]:
        """返回 [(keyed_dir, def_dir)] 列表，def_dir 可能为空 Path"""
        found: List[Tuple[Path, Path]] = []
        for lang_parent in scan_root.rglob("Languages"):
            if not lang_parent.is_dir():
                continue
            lang_dir = lang_parent / lang
            if not lang_dir.is_dir():
                continue
            kd = lang_dir / keyed_name
            dd = lang_dir / def_name
            if kd.is_dir() or dd.is_dir():
                found.append((kd, dd))
        return found

    bases_to_scan: List[Path] = []
    if versions is None:
        versions = get_version_dirs_from_fs(str(root))
    if include_root:
        bases_to_scan.append(root)
    for ver in versions or []:
        ver_dir = root / ver
        if ver_dir.is_dir():
            bases_to_scan.append(ver_dir)
    if not bases_to_scan:
        bases_to_scan = [root]

    seen_keyed: Set[Path] = set()
    seen_def: Set[Path] = set()
    for base in bases_to_scan:
        for kd, dd in _find_lang_dirs(base):
            if kd.is_dir() and kd not in seen_keyed:
                seen_keyed.add(kd)
                keyed_count += _collect_and_copy(kd, out_keyed, used_keyed)
            if dd.is_dir() and dd not in seen_def:
                seen_def.add(dd)
                def_count += _collect_and_copy(dd, out_def, used_def)

    return keyed_count, def_count


def handle_aggregate_chinese_to_root():
    """将各模组 Languages/ChineseSimplified 的 Keyed 和 DefInjected 汇总到根目录"""
    ui.print_section_header("汇总中文翻译到根目录", ui.Icons.BATCH)
    out_raw = safe_input(ui.get_input_prompt("请输入批量导出根目录（即各模组所在父目录）"))
    if not out_raw or not out_raw.strip():
        ui.print_error("未输入根目录，已取消")
        return
    root = Path(out_raw.strip())
    if not root.is_dir():
        ui.print_error(f"目录不存在: {root}")
        return
    detected = get_version_dirs_from_fs(str(root))
    chosen_versions: Optional[List[str]] = None
    include_root = True
    if detected:
        ui.print_info(f"检测到版本目录: {', '.join(detected)}")
        ui.print_header("选择要汇总的版本")
        options = ["仅根目录（不汇总版本子目录）"] + detected + ["全部（根目录 + 所有版本）"]
        opts_str = " / ".join(f"{i + 1}={o}" for i, o in enumerate(options))
        for i, opt in enumerate(options, 1):
            ui.print_menu_item(str(i), opt, "", compact=True)
        ver_choice = safe_input(ui.get_input_prompt("请选择", options=opts_str, default="1"))
        if ver_choice is None:
            return
        idx = (ver_choice or "1").strip()
        if idx.isdigit():
            i = int(idx)
            if 1 <= i <= len(options):
                if i == 1:
                    chosen_versions = []
                    include_root = True
                elif i == len(options):
                    chosen_versions = detected
                    include_root = True
                else:
                    chosen_versions = [detected[i - 2]]
                    include_root = False
        if chosen_versions is None:
            chosen_versions = []
    else:
        ui.print_info("未检测到版本目录，仅扫描根目录下 Languages")
        chosen_versions = []

    k_count, d_count = aggregate_chinese_translations_to_root(
        str(root), versions=chosen_versions, include_root=include_root
    )
    ui.print_success(f"汇总完成：Keyed {k_count} 个文件，DefInjected {d_count} 个文件")
    ui.print_info(f"输出目录: {root}/Languages/ChineseSimplified/Keyed 与 DefInjected")


def handle_batch_import_translations():
    """从总 CSV 批量导入翻译到各模组目录，按 mod 列分片，导入时使用 key+file 双校验。"""
    ui.print_section_header("批量导入翻译", ui.Icons.BATCH)
    out_raw = safe_input(ui.get_input_prompt("请输入批量导出根目录（即各模组所在父目录）"))
    if not out_raw or not out_raw.strip():
        ui.print_error("未输入根目录，已取消")
        return
    output_base = Path(out_raw.strip())
    if not output_base.is_dir():
        ui.print_error(f"目录不存在: {output_base}")
        return
    default_total = str(output_base / TOTAL_CSV_NAME)
    csv_raw = safe_input(
        ui.get_input_prompt("总 CSV 路径", default=default_total)
    )
    if csv_raw is None:
        return
    total_csv = (csv_raw or default_total).strip()
    if not Path(total_csv).is_file():
        ui.print_error(f"文件不存在: {total_csv}")
        return
    try:
        with open_csv_reader(total_csv) as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "mod" not in reader.fieldnames:
                ui.print_error("总 CSV 需包含 mod 列，请使用批量提取生成的总 CSV")
                return
            all_fieldnames = list(reader.fieldnames)
            rows_by_mod = {}
            for row in reader:
                mod_name = (row.get("mod") or "").strip()
                if not mod_name:
                    continue
                rows_by_mod.setdefault(mod_name, []).append(row)
    except (OSError, IOError, csv.Error) as e:
        ui.print_error(f"读取总 CSV 失败: {e}")
        return
    if not rows_by_mod:
        ui.print_warning("总 CSV 中无有效 mod 列或数据，已取消")
        return
    fieldnames = [c for c in all_fieldnames if c != "mod"]
    if not fieldnames:
        fieldnames = list(CSV_TRANSLATION_HEADER)
    from import_template.importers import import_translations
    success = 0
    failed: List[str] = []
    for mod_folder, mod_rows in rows_by_mod.items():
        mod_dir = str(output_base / mod_folder)
        if not (output_base / mod_folder).is_dir():
            failed.append(f"{mod_folder}（目录不存在）")
            continue
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".csv",
                delete=False,
                encoding="utf-8",
                newline="",
            ) as tmp:
                w = csv.DictWriter(tmp, fieldnames=fieldnames, extrasaction="ignore")
                w.writeheader()
                for row in mod_rows:
                    w.writerow({k: row.get(k, "") for k in fieldnames})
                tmp_path = tmp.name
            ok = import_translations(
                csv_path=tmp_path,
                mod_dir=mod_dir,
                merge=True,
                auto_create_templates=True,
                language=None,
            )
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            if ok:
                success += 1
                ui.print_info(f"已导入: {mod_folder}")
            else:
                failed.append(mod_folder)
        except Exception as e:  # pylint: disable=broad-except
            failed.append(f"{mod_folder}: {e}")
            ui.print_warning(f"导入失败 {mod_folder}: {e}")
    ui.print_success(f"批量导入完成：成功 {success}，失败 {len(failed)}")
    if failed:
        for x in failed:
            ui.print_warning(f"  · {x}")


def handle_batch():
    """处理批量操作功能"""
    ui.print_section_header("批量处理", ui.Icons.BATCH)
    ui.print_menu_item("1", "批量提取（Vanilla 前缀模组）", "从 Workshop 扫描并导出到 指定目录/模组名/", ui.Icons.SCAN, compact=True)
    ui.print_menu_item("2", "批量导入翻译", "从总 CSV 按 mod 分片导入，key+路径双校验", ui.Icons.FOLDER, compact=True)
    ui.print_menu_item(
        "3",
        "汇总中文翻译到根目录",
        "将各模组 Languages/ChineseSimplified 的 Keyed、DefInjected 汇总到根目录，同名加序号",
        ui.Icons.FOLDER,
        compact=True,
    )
    ui.print_menu_item("q", "返回主菜单", "", ui.Icons.BACK, compact=True)

    choice = safe_input(ui.get_input_prompt("请选择", options="1 / 2 / 3 / q"))
    if choice is None:
        return
    choice = (choice or "").strip().lower()
    if choice == "q":
        return
    if choice == "1":
        handle_batch_vanilla_extract()
        return
    if choice == "2":
        handle_batch_import_translations()
        return
    if choice == "3":
        handle_aggregate_chinese_to_root()
        return
    ui.print_warning("无效选项，请选择 1、2、3 或 q")
