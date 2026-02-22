"""
批量处理处理器
批量导入、汇总到根目录（批量提取已迁至 extract.batch_extract，批量完整流程已迁至 full_pipeline）
"""

import csv
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Set, Tuple

from utils.constants import CSV_TRANSLATION_HEADER, TOTAL_CSV_NAME
from utils.csv_utils import open_csv_reader
from utils.interaction import safe_input
from utils.ui_style import ui
from utils.load_folders import get_version_dirs_from_fs

from extract.batch_extract import handle_batch_vanilla_extract
from import_template.importers import import_translations


def batch_import_from_csv(
    output_base_path: Path,
    csv_path: str,
    language: Optional[str] = None,
) -> Tuple[int, int, List[str]]:
    """
    从总 CSV 按 mod 列分片导入到各模组目录。
    Returns: (success_count, total_count, failed_list)
    """
    try:
        with open_csv_reader(csv_path) as f:
            reader = csv.DictReader(f)
            fieldnames_list = reader.fieldnames or []
            if "mod" not in fieldnames_list:
                return 0, 0, []
            all_fieldnames = list(fieldnames_list)
            rows_by_mod = {}
            for row in reader:
                mod_name = (row.get("mod") or "").strip()
                if mod_name:
                    rows_by_mod.setdefault(mod_name, []).append(row)
    except (OSError, IOError, csv.Error):
        raise

    fieldnames = [c for c in all_fieldnames if c != "mod"] or list(CSV_TRANSLATION_HEADER)
    success = 0
    failed: List[str] = []
    for mod_folder, mod_rows in rows_by_mod.items():
        mod_dir = str(output_base_path / mod_folder)
        if not (output_base_path / mod_folder).is_dir():
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
                language=language,
            )
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            if ok:
                success += 1
            else:
                failed.append(mod_folder)
        except Exception as e:  # pylint: disable=broad-except
            failed.append(f"{mod_folder}: {e}")
    return success, len(rows_by_mod), failed


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
    delete_existing: bool = False,
) -> Tuple[int, int]:
    """
    将根目录下各模组的 Languages/ChineseSimplified 的 Keyed 和 DefInjected 汇总到根目录。
    同名文件在扩展名前加序号 1、2、3…，不覆盖。

    Args:
        root_dir: 批量导出根目录（含多个模组子目录）
        versions: 可选，版本目录名列表如 ["1.5","1.6"]；为 None 时自动检测根目录下的版本号子目录
        language: 语言目录名，默认 ChineseSimplified
        include_root: 是否同时扫描根目录；选单个版本时应为 False，避免 root 的 rglob 扫到其他版本
        delete_existing: 为 True 时，汇总前先清空根目录的 Keyed/DefInjected（用于完整流程）

    Returns:
        (keyed_count, definjected_count) 复制的文件数
    """
    from user_config import UserConfigManager
    config = UserConfigManager.get_instance()
    lang = language or config.language_config.get_default_cn_language()
    keyed_name = config.language_config.get_value("keyed_dir", "Keyed")
    def_name = config.language_config.get_value("definjected_dir", "DefInjected")

    root = Path(root_dir)
    if not root.is_dir():
        return 0, 0

    out_keyed = root / "Languages" / lang / keyed_name
    out_def = root / "Languages" / lang / def_name
    if delete_existing:
        for d in (out_keyed, out_def):
            if d.exists() and d.is_dir():
                try:
                    shutil.rmtree(d)
                except OSError as e:
                    ui.print_warning(f"清空 {d} 时出错: {e}")
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
        success, total, failed = batch_import_from_csv(output_base, total_csv, language=None)
    except (OSError, IOError, csv.Error) as e:
        ui.print_error(f"读取总 CSV 失败: {e}")
        return
    if total == 0:
        ui.print_warning("总 CSV 中无有效 mod 列或数据，已取消")
        return
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
