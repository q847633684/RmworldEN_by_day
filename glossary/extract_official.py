"""
从 RimWorld-ChineseSimplified 官方汉化仓库抽取术语，输出 game_dictionary 兼容的 YAML。

支持两种 Keyed XML 格式：
1. 带 <!-- EN: 英文 --> 注释：使用注释内容作为 english，下一行元素文本作为 chinese
2. 无注释：使用 tag 名作为 english（如 Cancel、Colony），元素文本作为 chinese

用法：
    python -m glossary.extract_official <RimWorld-ChineseSimplified 仓库路径> [输出路径]
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml

from utils.constants import KEYED_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

# 术语过滤：英文字符数范围
EN_MIN_LEN = 1
EN_MAX_LEN = 80
ZH_MIN_LEN = 1
ZH_MAX_LEN = 100

# 排除含占位符或换行的条目
PLACEHOLDER_PATTERN = re.compile(r"\{[^}]*\}|\[[\w_]+\]|\\n")


def _has_placeholder(text: str) -> bool:
    """文本是否含占位符或换行。"""
    return bool(PLACEHOLDER_PATTERN.search(text))


def _looks_like_term_tag(tag: str) -> bool:
    """
    判断 tag 是否适合作为英文术语（无 EN 注释时的回退）。
    短且无明显代码特征的 tag 可能本身是英文。
    """
    if not tag or len(tag) > 40:
        return False
    if "_" in tag and tag.count("_") >= 2:
        return False
    return True


def extract_pairs_from_keyed_xml(filepath: str) -> List[Tuple[str, str]]:
    """
    从 Keyed XML 提取 (english, chinese) 对。
    优先使用 <!-- EN: xxx -->，否则在 tag 合理时用 tag 名。
    """
    pairs: List[Tuple[str, str]] = []
    try:
        content = Path(filepath).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("读取失败 %s: %s", filepath, e)
        return pairs

    lines = content.splitlines()
    en_from_comment: str | None = None

    for line in lines:
        en_match = re.match(r"\s*<!--\s*EN:\s*(.*?)\s*-->", line)
        tag_match = re.match(r"\s*<([^/>\s]+)>\s*(.*?)\s*</\1>", line, re.DOTALL)

        if en_match:
            en_from_comment = en_match.group(1).strip()
        elif tag_match:
            tag, text = tag_match.group(1), tag_match.group(2).strip()
            zh = text
            if not zh:
                en_from_comment = None
                continue
            if _has_placeholder(zh) or "\n" in zh:
                en_from_comment = None
                continue
            if en_from_comment:
                en = en_from_comment
            elif _looks_like_term_tag(tag):
                en = tag
            else:
                en_from_comment = None
                continue
            if en and zh and en != zh:
                if not _has_placeholder(en) and EN_MIN_LEN <= len(en) <= EN_MAX_LEN:
                    if ZH_MIN_LEN <= len(zh) <= ZH_MAX_LEN:
                        pairs.append((en, zh))
            en_from_comment = None
        else:
            en_from_comment = None

    return pairs


def extract_from_repo(repo_path: str) -> Dict[str, Tuple[str, str]]:
    """
    从 RimWorld-ChineseSimplified 仓库所有 Keyed XML 抽取术语。
    返回 {english: (english, chinese)} 以去重（同英文取首次）。
    """
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise FileNotFoundError(f"仓库路径不存在或非目录: {repo_path}")

    keyed_dirs = list(repo.rglob(KEYED_DIR))
    if not keyed_dirs:
        keyed_dirs = [d for d in repo.rglob("*") if d.name == "Keyed"]
    if not keyed_dirs:
        raise FileNotFoundError(f"未找到 Keyed 目录: {repo_path}")

    seen_en: Set[str] = set()
    result: Dict[str, Tuple[str, str]] = {}
    total_files = 0
    total_pairs = 0

    for keyed_dir in keyed_dirs:
        for xml_file in keyed_dir.rglob("*.xml"):
            total_files += 1
            pairs = extract_pairs_from_keyed_xml(str(xml_file))
            for en, zh in pairs:
                if en not in seen_en:
                    seen_en.add(en)
                    result[en] = (en, zh)
                    total_pairs += 1

    logger.info("扫描 %d 个 XML，抽取 %d 条术语（去重后）", total_files, total_pairs)
    return result


def to_game_dictionary_yaml(pairs: Dict[str, Tuple[str, str]]) -> dict:
    """转换为 game_dictionary 的 YAML 结构。"""
    entries = []
    for en, (_, zh) in sorted(pairs.items(), key=lambda x: x[0].lower()):
        entries.append(
            {
                "chinese": zh,
                "context": "RimWorld 官方汉化",
                "english": en,
                "priority": "high",
            }
        )
    return {
        "official_rimworld": {
            "description": "从 RimWorld-ChineseSimplified 抽取的官方术语",
            "entries": entries,
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从 RimWorld-ChineseSimplified 仓库抽取术语，输出 game_dictionary YAML"
    )
    parser.add_argument(
        "repo_path",
        type=str,
        help="RimWorld-ChineseSimplified 仓库根目录（clone 后的路径）",
    )
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        default=None,
        help="输出 YAML 路径，默认输出到 user_config/config/official_game_terms.yaml",
    )
    args = parser.parse_args()

    try:
        pairs = extract_from_repo(args.repo_path)
    except FileNotFoundError as e:
        logger.error("%s", e)
        print(f"错误: {e}")
        print("请先 clone: git clone https://github.com/Ludeon/RimWorld-ChineseSimplified.git")
        return

    if not pairs:
        logger.warning("未抽取到任何术语，请检查仓库结构")
        print("未抽取到术语，请确认仓库含 Keyed/*.xml")
        return

    data = to_game_dictionary_yaml(pairs)

    out_path = args.output
    if not out_path:
        base = Path(__file__).parent.parent
        out_path = str(base / "user_config" / "config" / "official_game_terms.yaml")

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"已输出 {len(pairs)} 条术语到: {out_file}")


if __name__ == "__main__":
    main()
