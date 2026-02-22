"""
修补翻译 - 扫描文件夹，检测 Google 翻译错误并重新翻译替换
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from utils.logging_config import get_logger
from utils.ui_style import ui
from utils.utils import XMLProcessor, XMLProcessorConfig, sanitize_xml

logger = get_logger(__name__)

# Google 翻译错误等异常模式（部分匹配即视为异常）
BAD_TRANSLATION_PATTERNS = [
    r"Error\s*\d+",
    r"Server\s*Error",
    r"That'?s\s+an?\s+error",
    r"Please\s+try\s+again\s+later",
    r"That'?s\s+all\s+we\s+know",
    r"Something\s+went\s+wrong",
    r"Translation\s+failed",
]
_BAD_RE = re.compile("|".join(f"({p})" for p in BAD_TRANSLATION_PATTERNS), re.I)


def is_bad_translation(text: str) -> bool:
    """判断文本是否像 Google 翻译错误或异常输出"""
    if not text or not isinstance(text, str):
        return False
    t = text.strip()
    if len(t) < 20:
        return False
    return bool(_BAD_RE.search(t))


@dataclass
class BadEntry:
    """异常翻译条目"""
    xml_path: str
    en_text: str
    bad_text: str
    elem_tag: str
    elem_text_attr: str  # "text" or attr name


def _iter_elements_with_en_and_text(root) -> List[Tuple[any, str, str, bool]]:
    """
    遍历 XML，收集 (elem, en_text, current_text, is_text_attr)。
    兼容 lxml（含 Comment）与标准库。
    """
    result = []
    try:
        import lxml.etree as etree
        has_lxml = True
    except ImportError:
        has_lxml = False

    def _walk(parent, last_en_ref):
        for c in parent:
            if has_lxml and isinstance(c, etree._Comment):
                txt = (c.text or "").strip()
                if txt.startswith("EN:"):
                    last_en_ref[0] = txt[3:].strip()
                continue
            if not hasattr(c, "tag") or c.tag is None or (isinstance(c.tag, str) and c.tag.startswith("{")):
                continue
            tag_local = c.tag.split("}", 1)[-1] if isinstance(c.tag, str) and "}" in c.tag else str(c.tag)
            if tag_local in ("", "?xml"):
                continue
            text = (c.text or "").strip()
            is_attr = False
            if not text and c.attrib:
                for a, v in c.attrib.items():
                    if v and isinstance(v, str) and v.strip():
                        text = v.strip()
                        is_attr = True
                        break
            if text and last_en_ref[0]:
                result.append((c, last_en_ref[0], text, is_attr))
                last_en_ref[0] = None  # 注释只应用于紧接着的下一个元素
            _walk(c, last_en_ref)

    ref = [None]
    _walk(root, ref)
    return result


def scan_and_repair_xml(xml_path: str, translate_func) -> int:
    """
    扫描单个 XML，检测异常翻译并用 translate_func(en_text) 替换。

    Args:
        xml_path: XML 文件路径
        translate_func: 函数 (en_text: str) -> str

    Returns:
        修复的条目数量
    """
    config = XMLProcessorConfig(max_file_size=50 * 1024 * 1024, preserve_comments=True)
    processor = XMLProcessor(config=config)
    tree = processor.parse_xml(xml_path)
    if tree is None:
        return 0
    root = tree.getroot() if hasattr(tree, "getroot") else tree
    repaired = 0
    for elem, en_text, current, is_attr in _iter_elements_with_en_and_text(root):
        if not is_bad_translation(current):
            continue
        if not en_text or not en_text.strip():
            logger.debug("跳过无英文源: %s", xml_path)
            continue
        try:
            new_text = translate_func(en_text.strip())
            if not new_text or new_text == current:
                continue
            if is_attr:
                for a in (elem.attrib or {}):
                    if (elem.get(a) or "").strip() == current:
                        elem.set(a, sanitize_xml(new_text))
                        break
            else:
                elem.text = sanitize_xml(new_text)
            repaired += 1
            logger.info("修复 %s: %r -> %r", xml_path, current[:50], new_text[:50])
        except Exception as e:
            logger.warning("翻译失败 %s: %s", en_text[:30], e)
    if repaired > 0:
        processor.save_xml(tree, xml_path)
    return repaired


def scan_and_repair_folder(
    folder: str,
    translate_func=None,
    language: str = "ChineseSimplified",
) -> int:
    """
    扫描文件夹下 Keyed 与 DefInjected 的 XML，修补异常翻译。

    Args:
        folder: 语言目录或模组根（会查找 Languages/<language>）
        translate_func: 翻译函数 (en: str) -> str，默认用 Google
        language: 语言代码

    Returns:
        修复的条目总数
    """
    base = Path(folder).resolve()
    lang_dirs = []
    if (base / "Keyed").exists() or (base / "DefInjected").exists():
        lang_dirs.append(base)
    elif (base / "Languages" / language).exists():
        lang_dirs.append(base / "Languages" / language)
    elif (base / language).exists():
        lang_dirs.append(base / language)
    else:
        for p in base.rglob("Languages"):
            ld = p / language
            if ld.exists() and ((ld / "Keyed").exists() or (ld / "DefInjected").exists()):
                lang_dirs.append(ld)
    if not lang_dirs:
        ui.print_warning(f"未找到语言目录: {folder}")
        return 0
    if translate_func is None:
        try:
            from translate.core.google_translator import translate_text
            def _tr(t):
                return translate_text(t, target_lang="zh-CN", source_lang="auto")
            translate_func = _tr
        except ImportError:
            ui.print_error("需要 deep-translator 才能使用 Google 翻译修补")
            return 0
    total = 0
    keyed_name = "Keyed"
    def_name = "DefInjected"
    for lang_dir in lang_dirs:
        for sub in [keyed_name, def_name]:
            subdir = Path(lang_dir) / sub
            if not subdir.exists():
                continue
            xml_files = list(subdir.rglob("*.xml"))
            ui.print_info(f"扫描 {subdir} 共 {len(xml_files)} 个文件...")
            for xf in xml_files:
                n = scan_and_repair_xml(str(xf), translate_func)
                total += n
    return total
