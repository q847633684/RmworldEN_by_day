"""
批量清理词典：1) 删除 english 含中文的错误条目 2) chinese 含 | 时只保留第一个 3) 去重（同 english 保留首条）

用法：
    python -m glossary.clean_bad_entries <yaml_path> [选项]
"""

import argparse
import re
from pathlib import Path

import yaml

CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uff00-\uffef]")


def has_cjk(text: str) -> bool:
    """文本是否含中日韩字符"""
    return bool(text and CJK_PATTERN.search(str(text)))


def normalize_chinese_alt(val: str) -> str:
    """chinese 含 | 或 / 的备选译法时只保留第一个。括号内的 / 不拆分（如 命运/零）"""
    s = str(val or "").strip()
    for sep in ("|", "/"):
        if sep not in s:
            continue
        first = s.split(sep, 1)[0].strip()
        if not first:
            return s
        if "（" in first and "）" not in first:
            continue
        return first
    return s


def clean_dictionary(
    yaml_path: str,
    dry_run: bool = False,
    normalize_pipe: bool = True,
    dedupe: bool = True,
) -> dict:
    """
    清理词典：删除 english 含 CJK 的条目；chinese 的 | 取首项；按 english 去重。
    Returns:
        {"removed_bad": int, "normalized_pipe": int, "removed_dup": int, "kept": int}
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(yaml_path)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    stats = {"removed_bad": 0, "normalized_pipe": 0, "removed_dup": 0, "kept": 0}

    for category, cat_data in (data or {}).items():
        if not isinstance(cat_data, dict) or "entries" not in cat_data:
            continue
        entries = cat_data["entries"]
        if not isinstance(entries, list):
            continue
        new_entries = []
        seen_english: set = set()

        for entry in entries:
            if not isinstance(entry, dict) or "english" not in entry:
                new_entries.append(entry)
                stats["kept"] += 1
                continue
            eng = str(entry.get("english", "")).strip()
            if has_cjk(eng):
                stats["removed_bad"] += 1
                continue
            if dedupe:
                eng_key = eng.lower()
                if eng_key in seen_english:
                    stats["removed_dup"] += 1
                    continue
                seen_english.add(eng_key)
            if normalize_pipe and "chinese" in entry:
                old = entry["chinese"]
                new_val = normalize_chinese_alt(old)
                if new_val != old:
                    entry = dict(entry)
                    entry["chinese"] = new_val
                    stats["normalized_pipe"] += 1
            new_entries.append(entry)
            stats["kept"] += 1

        cat_data["entries"] = new_entries

    if not dry_run and (
        stats["removed_bad"] or stats["normalized_pipe"] or stats["removed_dup"]
    ):
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
            )

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="清理词典：删错填、chinese取首项、去重"
    )
    parser.add_argument("yaml_path", help="词典 YAML 路径")
    parser.add_argument("-n", "--dry-run", action="store_true", help="仅统计，不写入")
    parser.add_argument(
        "--no-pipe", action="store_true", help="不处理 chinese 中的 |（默认取首项）"
    )
    parser.add_argument(
        "--no-dedupe", action="store_true", help="不去重（默认按 english 去重）"
    )
    args = parser.parse_args()

    stats = clean_dictionary(
        args.yaml_path,
        dry_run=args.dry_run,
        normalize_pipe=not args.no_pipe,
        dedupe=not args.no_dedupe,
    )
    print(
        f"删除错填 {stats['removed_bad']} 条，"
        f"chinese 取首项 {stats['normalized_pipe']} 条，"
        f"去重删除 {stats['removed_dup']} 条，"
        f"保留 {stats['kept']} 条"
    )
    if args.dry_run and (
        stats["removed_bad"] or stats["normalized_pipe"] or stats["removed_dup"]
    ):
        print("（dry-run 未写入，去掉 -n 执行实际修改）")


if __name__ == "__main__":
    main()
