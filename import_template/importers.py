"""
导入功能模块 - 实现翻译结果导入到模板的功能
"""

import csv
import re
from utils.constants import CSV_TRANSLATION_HEADER
from utils.csv_utils import open_csv_reader
from utils.logging_config import get_logger
from utils.path_utils import key_to_dot_notation
from utils.ui_style import ui
from pathlib import Path
from typing import Dict, Tuple, Any, Optional, Callable, List, Union
from utils.utils import XMLProcessor, XMLProcessorConfig
# 使用新配置系统
from user_config import UserConfigManager

logger = get_logger(__name__)


def _get_config():
    """懒加载配置，避免模块加载时依赖未就绪"""
    return UserConfigManager.get_instance()


def import_translations(
    csv_path: str,
    mod_dir: str,
    merge: bool = True,
    auto_create_templates: bool = True,
    language: Optional[str] = None,
) -> bool:
    """
    将翻译CSV导入到翻译模板

    Args:
        csv_path (str): 翻译CSV文件路径
        mod_dir (str): 模组目录
        merge (bool): 是否合并现有翻译
        auto_create_templates (bool): 是否自动创建模板
        language (str): 目标语言

    Returns:
        bool: 导入是否成功
    """
    if language is None:
        language = _get_config().language_config.get_default_cn_language()
    logger.info("开始导入翻译到模板: %s", csv_path)
    try:
        # 步骤1：解析所有模板目录（含 mod 根下 Languages/<语言> 与子路径如 Common/Languages/<语言>）
        lang_dirs = _find_all_language_dirs(mod_dir, language)
        if not lang_dirs:
            fallback = _get_config().language_config.get_template_dir(mod_dir, language)
            if fallback.exists():
                lang_dirs = [str(fallback)]
        if auto_create_templates:
            if not lang_dirs or not any(Path(d).exists() for d in lang_dirs):
                logger.error("翻译模板目录不存在，请先使用提取功能创建翻译模板")
                ui.print_error("❌ 翻译模板目录不存在，请先使用提取功能创建翻译模板")
                return False
        # 步骤2：验证CSV文件
        if not _validate_csv_file(csv_path):
            return False
        # 步骤3：加载翻译数据并按类型分组（支持 key+file 双校验，避免重复 key 写错文件）
        (
            keyed_translations,
            definjected_translations,
            keyed_by_file,
            definjected_by_file,
        ) = _load_translations_from_csv(csv_path)
        if not keyed_translations and not definjected_translations:
            return False

        # 步骤4：对每个语言目录分别更新 Keyed 与 DefInjected；有 by_file 时按 key+file 双校验
        use_by_file = bool(keyed_by_file or definjected_by_file)
        if use_by_file:
            logger.info("使用 key+file 双校验导入，按路径精确匹配")
        updated_count = 0
        for template_dir in lang_dirs:
            updated_count += _update_xml_in_subdir(
                mod_dir,
                language,
                "keyed",
                keyed_translations,
                merge,
                language_dir_override=template_dir,
                translations_by_file=keyed_by_file if use_by_file else None,
            )
            updated_count += _update_xml_in_subdir(
                mod_dir,
                language,
                "definjected",
                definjected_translations,
                merge,
                language_dir_override=template_dir,
                translations_by_file=definjected_by_file if use_by_file else None,
            )
        # 步骤5：验证导入结果
        had_translations = bool(keyed_translations or definjected_translations)
        if had_translations and updated_count == 0:
            logger.warning(
                "CSV 中有 %s 条 Keyed、%s 条 DefInjected，但未匹配到任何 XML 节点，未写入任何文件",
                len(keyed_translations),
                len(definjected_translations),
            )
            ui.print_warning(
                "⚠️ 未导入任何内容：CSV 的 key 与模板 XML 节点不匹配，请确认 CSV 与当前模板来自同一模组/同一提取。"
            )
            return False
        first_template = Path(lang_dirs[0]) if lang_dirs else None
        success = _verify_import_results(
            mod_dir, language, template_dir=first_template
        )
        if success:
            logger.info("翻译导入到模板完成，更新了 %s 个文件", updated_count)
            ui.print_success("翻译已成功导入到模板")
        else:
            logger.warning("翻译导入可能存在问题")
            ui.print_warning("⚠️ 翻译导入完成，但可能存在问题")
        return success
    except FileNotFoundError as e:
        logger.error("文件未找到: %s", e)
        ui.print_error(f"❌ 文件未找到: {e}")
        return False
    except PermissionError as e:
        logger.error("权限错误: %s", e)
        ui.print_error(f"❌ 权限错误: {e}")
        return False
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        logger.error("导入翻译时发生错误: %s", e, exc_info=True)
        ui.print_error(f"❌ 导入失败: {e}")
        return False


def _validate_csv_file(csv_path: str) -> bool:
    """验证CSV文件"""
    if not Path(csv_path).is_file():
        logger.error("CSV文件不存在: %s", csv_path)
        return False

    try:
        with open_csv_reader(csv_path) as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            required_cols = list(CSV_TRANSLATION_HEADER[:2])  # key, text
            if not header or not all(col in header for col in required_cols):
                logger.error("CSV文件格式无效：缺少必要的列 (key, text)")
                return False

            # 检查是否有type列，如果没有则使用兼容模式
            has_type_column = "type" in header
            if has_type_column:
                logger.info("检测到新格式CSV文件（包含type列）")
            else:
                logger.info("检测到旧格式CSV文件（无type列），将使用兼容模式")

            return True
    except FileNotFoundError:
        logger.error("CSV文件不存在: %s", csv_path)
        return False
    except PermissionError:
        logger.error("无权限访问CSV文件: %s", csv_path)
        return False
    except UnicodeDecodeError:
        logger.error("CSV文件编码错误: %s", csv_path)
        return False
    except (OSError, ValueError, TypeError) as e:
        logger.error("验证CSV文件时发生错误: %s", e)
        return False


def _load_translations_from_csv(
    csv_path: str,
) -> Tuple[
    Dict[str, str],
    Dict[str, str],
    Dict[str, Dict[str, str]],
    Dict[str, Dict[str, str]],
]:
    """从CSV文件加载翻译数据，按类型分组；支持 key+file 双校验（同 key 不同 file 分开）。

    Returns:
        (keyed_translations, definjected_translations, keyed_by_file, definjected_by_file)
        by_file 为 file_rel_path -> {key -> value}，仅当 CSV 含 file 列时填充；用于按文件精确写入。
    """
    keyed_translations: Dict[str, str] = {}
    definjected_translations: Dict[str, str] = {}
    keyed_by_file: Dict[str, Dict[str, str]] = {}
    definjected_by_file: Dict[str, Dict[str, str]] = {}

    try:
        with open_csv_reader(csv_path) as f:
            reader = csv.DictReader(f)
            has_file_col = reader.fieldnames and "file" in reader.fieldnames
            for row in reader:
                key = (row.get("key") or "").strip().strip("\ufeff")
                file_rel = (row.get("file") or "").strip().replace("\\", "/")
                value = (
                    row.get("translated")
                    or row.get("译文")
                    or row.get("中文")
                    or row.get("target")
                )
                if value is None or (isinstance(value, str) and not value.strip()):
                    extra = row.get(None)
                    if isinstance(extra, list) and len(extra) > 0:
                        value = extra[-1]
                    elif isinstance(row, dict) and len(row) >= 6:
                        vals = list(row.values())
                        if len(vals) >= 6:
                            value = vals[-1]
                value = (value or row.get("text") or "").strip()
                translation_type = (row.get("type") or "").strip().lower()

                if not key or not value:
                    continue
                if translation_type == "keyed":
                    keyed_translations[key] = value
                    if has_file_col and file_rel:
                        keyed_by_file.setdefault(file_rel, {})[key] = value
                elif translation_type == "def":
                    if has_file_col and file_rel:
                        # 有 file 列时：仅写入 by_file，严格按 key+file 校验，避免 def/key 不匹配时误导入
                        definjected_by_file.setdefault(file_rel, {})[key] = value
                    elif not has_file_col:
                        definjected_translations[key] = value
                else:
                    if "/" in key:
                        if has_file_col and file_rel:
                            definjected_by_file.setdefault(file_rel, {})[key] = value
                        elif not has_file_col:
                            definjected_translations[key] = value
                    else:
                        keyed_translations[key] = value
                        if has_file_col and file_rel:
                            keyed_by_file.setdefault(file_rel, {})[key] = value

        return (
            keyed_translations,
            definjected_translations,
            keyed_by_file,
            definjected_by_file,
        )
    except FileNotFoundError:
        logger.error("CSV文件不存在: %s", csv_path)
        ui.print_error(f"❌ CSV文件不存在: {csv_path}")
        return {}, {}, {}, {}
    except PermissionError:
        logger.error("无权限访问CSV文件: %s", csv_path)
        ui.print_error(f"❌ 无权限访问CSV文件: {csv_path}")
        return {}, {}, {}, {}
    except (OSError, ValueError, TypeError) as e:
        logger.error("加载CSV文件时发生错误: %s", e)
        ui.print_error(f"❌ 加载CSV文件失败: {e}")
        return {}, {}, {}, {}


def _definjected_get_parent(elem: Any, _root: Any, parent_map: Optional[dict]) -> Any:
    """获取元素的父节点，兼容 lxml（getparent）与标准库（parent_map）。"""
    if parent_map is not None:
        return parent_map.get(elem)
    getparent = getattr(elem, "getparent", None)
    if callable(getparent):
        return getparent()
    return None


def _looks_like_en_placeholder(text: str) -> bool:
    """
    判断文本是否像 DefInjected 中的英文占位（新模板常带 EN 注释格式），
    这类内容在迁移时应视为可覆盖，即使用户选了「仅填充空项」。
    """
    if not text or len(text) < 20:
        return False
    t = text.strip()
    # 常见 EN 占位：tag=... -> 英文句子、或 -&gt; 英文
    if "->" in t or "&gt;" in t or "-&gt;" in t:
        # 大部分为 ASCII 或拉丁字符则视为英文占位
        try:
            ascii_or_latin = sum(1 for c in t if ord(c) < 256)
            if ascii_or_latin >= len(t) * 0.85:
                return True
        except Exception:
            pass
    # 以常见规则前缀开头（RimWorld / AROM 等）
    lower = t.lower()
    for prefix in ("creation(", "episode(", "intro(", "conflict(", "victory(", "setup(", "story(", "lesson", "archist", "animist", "founder"):
        if lower.startswith(prefix) and ("->" in t or "&gt;" in t):
            return True
    return False


def _definjected_tag_local(tag: Any) -> str:
    """取标签的本地名（去掉命名空间），便于与 CSV 的 key 一致。"""
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        return tag.split("}", 1)[-1]
    return tag


def _definjected_li_siblings(parent: Any) -> list:
    """取父节点下所有 <li> 子元素（排除注释等），保证索引与旧版 flat_all 的 .0/.1 一致。"""
    return [
        c
        for c in parent
        if isinstance(getattr(c, "tag", None), str)
        and _definjected_tag_local(getattr(c, "tag", None)) == "li"
    ]


def _definjected_key_func(elem: Any, root: Any, parent_map: Optional[dict]) -> str:
    """
    DefInjected 用「父路径.标签」或「父路径.索引」生成 key，与提取器一致。
    约定：容器下的第 1 个 <li> -> 容器路径.0，第 2 个 -> .1，与旧版 flat_all 的 key 一致。
    支持的格式示例（根为 <LanguageData>）：
      - 平铺标签：<DefName.field>text</...> → key = "DefName.field"
      - 列表容器+<li>：<DefName.xxx.rulesStrings><li>...</li><li>...</li></...>
        → 第 1 个 li 的 key = "DefName.xxx.rulesStrings.0"，第 2 个 = ".1"
    兼容 lxml（parent_map 为 None 时用 elem.getparent()）与标准库 XML。
    带命名空间的标签使用本地名，以便与 CSV 中通常无命名空间的 key 匹配。
    """
    tag = getattr(elem, "tag", None)
    tag_local = _definjected_tag_local(tag)
    if not tag_local:
        return ""
    parent_tags = []
    p = _definjected_get_parent(elem, root, parent_map)
    while p is not None and p is not root:
        pt = getattr(p, "tag", None)
        pt_local = _definjected_tag_local(pt) if isinstance(pt, str) else ""
        if pt_local == "li":
            parent = _definjected_get_parent(p, root, parent_map)
            if parent is not None:
                li_siblings = _definjected_li_siblings(parent)
                try:
                    idx = li_siblings.index(p)
                except ValueError:
                    idx = 0
                parent_tags.append(str(idx))
            else:
                parent_tags.append("0")
        elif pt_local:
            parent_tags.append(pt_local)
        p = _definjected_get_parent(p, root, parent_map)
    parent_tags.reverse()
    if tag_local == "li":
        parent = _definjected_get_parent(elem, root, parent_map)
        if parent is not None:
            li_siblings = _definjected_li_siblings(parent)
            try:
                idx = li_siblings.index(elem)
            except ValueError:
                idx = 0
            return ".".join(parent_tags + [str(idx)])
        return ".".join(parent_tags + ["0"])
    if not parent_tags and "." in tag_local:
        return tag_local
    return ".".join(parent_tags + [tag_local]) if parent_tags else tag_local


def _get_lang_dir_scope(base_dir: str, lang_dir: str) -> str:
    """获取 lang_dir 相对于 base_dir 的 path scope（到 Languages 父级），用于 LoadFolders 路径映射。"""
    base = Path(base_dir).resolve()
    lang = Path(lang_dir).resolve()
    try:
        rel = lang.relative_to(base)
    except ValueError:
        return ""
    # lang_dir 形如 .../Languages/ChineseSimplified，scope 为 Languages 的父路径
    parts = rel.parts
    for i, p in enumerate(parts):
        if p == "Languages" or p == "Language":
            return "/".join(parts[:i]) if i else ""
    return "/".join(parts[:-1]) if len(parts) > 1 else ""


def _find_all_language_dirs_with_scope(
    base_dir: str, language: str
) -> List[Tuple[str, str]]:
    """返回 [(lang_dir, scope), ...]，scope 为 LoadFolders 路径（相对 base_dir）。"""
    lang_dirs = _find_all_language_dirs(base_dir, language)
    return [(d, _get_lang_dir_scope(base_dir, d)) for d in lang_dirs]


def _find_all_language_dirs(base_dir: str, language: str) -> List[str]:
    """
    递归查找 base_dir 下所有「语言目录」（含 Keyed 或 DefInjected），兼容两种结构：
    - 标准：Languages/<language>（智能提取默认）
    - 直接：<language>（部分汉化包仅用语言名）
    """
    base = Path(base_dir)
    if not base.is_dir():
        return []
    keyed_name = _get_config().language_config.get_value("keyed_dir", "Keyed")
    def_name = _get_config().language_config.get_value("definjected_dir", "DefInjected")
    found: List[str] = []
    for p in base.rglob("Languages"):
        if not p.is_dir():
            continue
        lang_dir = p / language
        if lang_dir.exists() and (
            (lang_dir / keyed_name).exists() or (lang_dir / def_name).exists()
        ):
            found.append(str(lang_dir))
    # 兼容「直接 language」结构：base 下或任意子目录下的 base/language 含 Keyed 或 DefInjected 也视为语言目录
    for p in base.rglob(language):
        if not p.is_dir() or p.name != language:
            continue
        if (p / keyed_name).exists() or (p / def_name).exists():
            found.append(str(p))
    # 去重并按路径深度排序（浅层优先）
    seen = set()
    unique = []
    for d in sorted(found, key=lambda x: len(Path(x).parts)):
        n = Path(d).resolve()
        if n not in seen:
            seen.add(n)
            unique.append(d)
    return unique


def _get_language_subdir_path(base_dir: str, language: str, subdir_type: str) -> Path:
    """
    解析语言子目录路径。支持四种情况：
    1) base_dir 下直接有 Keyed/DefInjected -> 视为语言目录
    2) base_dir 下有 language/Keyed（如 Languages2/ChineseSimplified/Keyed）-> 视为 Languages 父目录
    3) base_dir 下递归查找第一个 Keyed/DefInjected 目录（支持补丁目录如 Cumpilation/ould）
    4) 否则按模组根：base_dir/Languages/language/Keyed
    """
    base = Path(base_dir)
    keyed_name = _get_config().language_config.get_value("keyed_dir", "Keyed")
    def_name = _get_config().language_config.get_value("definjected_dir", "DefInjected")
    if (base / keyed_name).exists() or (base / def_name).exists():
        sub = keyed_name if subdir_type.lower() == "keyed" else def_name
        return base / sub
    if (base / language / keyed_name).exists() or (base / language / def_name).exists():
        sub = keyed_name if subdir_type.lower() == "keyed" else def_name
        return base / language / sub
    # 补丁目录：在 base 下递归找 Keyed/DefInjected 目录，优先最浅层
    sub = keyed_name if subdir_type.lower() == "keyed" else def_name
    candidates = [p for p in base.rglob(sub) if p.is_dir()]
    if candidates:
        candidates.sort(key=lambda p: len(p.relative_to(base).parts))
        return candidates[0]
    return _get_config().language_config.get_language_subdir(
        base_dir, language, subdir_type
    )


def _infer_path_versions(old_scopes: List[str], new_scopes: List[str]) -> Tuple[str, str]:
    """从 path scope 推断版本号（如 1.5、1.6），用于旧→新 LoadFolders 路径映射。"""
    import re
    ver_pat = re.compile(r"^v?(\d+\.\d+)$")

    def _first_version(scopes: List[str]) -> str:
        for s in scopes:
            for p in (s or "").replace("\\", "/").strip().split("/"):
                m = ver_pat.match(p.strip())
                if m:
                    return m.group(1)
        return ""

    old_ver = _first_version(old_scopes)
    new_ver = _first_version(new_scopes)
    return old_ver or "1.5", new_ver or "1.6"


def _map_old_scope_to_new(
    old_scope: str, new_scope: str, old_ver: str, new_ver: str
) -> bool:
    """判断 old_scope 是否对应 new_scope（版本替换后路径一致）。"""
    o = old_scope.replace("\\", "/").strip()
    n = new_scope.replace("\\", "/").strip()
    if not o and not n:
        return True
    mapped = o.replace(old_ver, new_ver, 1) if old_ver else o
    return mapped == n or (mapped.rstrip("/") == n.rstrip("/"))


def _collect_old_translations(
    old_base_dir: str,
    language: str,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    扫描旧翻译目录，收集 Keyed 与 DefInjected 中已有翻译。
    递归扫描所有子路径的 Languages/<lang> 目录（如 MajorModIntegrations/Biotech/...）。
    Keyed: key → 非空译文。
    DefInjected: key → 非空译文（扁平，不按 Def 类型分组），以便旧翻译无 Def 类型目录时也能匹配新模板。

    Args:
        old_base_dir: 旧模组根目录、语言目录、或直接 Keyed/DefInjected 文件夹
        language: 语言代码，如 ChineseSimplified

    Returns:
        (keyed_map, definjected_map) 其中 definjected_map 为 key → 译文
    """
    processor = XMLProcessor()
    keyed_map: Dict[str, str] = {}
    definjected_map: Dict[str, str] = {}

    # 递归查找所有 Languages/<lang> 目录（含子路径）
    lang_dirs = _find_all_language_dirs(old_base_dir, language)
    if not lang_dirs:
        # 回退：按原逻辑尝试单一目录
        for subdir_type in ["keyed", "definjected"]:
            subdir = _get_language_subdir_path(old_base_dir, language, subdir_type)
            if subdir.exists():
                parent = subdir.parent
                if parent.name.lower() == language.lower():
                    lang_dirs = [str(parent)]
                    break

    for lang_dir in lang_dirs:
        for subdir_type, use_def_key in [("keyed", False), ("definjected", True)]:
            subdir = Path(lang_dir) / (
                _get_config().language_config.get_value("definjected_dir", "DefInjected")
                if use_def_key
                else _get_config().language_config.get_value("keyed_dir", "Keyed")
            )
            if not subdir.exists():
                continue
            xml_files = list(Path(subdir).rglob("*.xml"))
            for xml_file in xml_files:
                try:
                    tree = processor.parse_xml(str(xml_file))
                    if tree is None:
                        continue
                    root = tree.getroot() if processor.use_lxml else tree
                    parent_map = (
                        {c: p for p in root.iter() for c in p}
                        if not processor.use_lxml
                        else None
                    )
                    for elem in root.xpath(".//*") if processor.use_lxml else root.iter():
                        key = (
                            _definjected_key_func(elem, root, parent_map)
                            if use_def_key
                            else processor._get_element_key(elem)
                        )
                        if not key:
                            continue
                        text = (elem.text or "").strip()
                        if text:
                            if use_def_key:
                                k = key_to_dot_notation(key)
                                definjected_map[k] = text
                            else:
                                keyed_map[key] = text
                except (OSError, ValueError, TypeError) as e:
                    logger.debug("跳过 %s: %s", xml_file, e)

    return keyed_map, definjected_map


def _collect_old_translations_by_path(
    old_base_dirs: List[str],
    language: str,
) -> Tuple[
    Dict[str, Dict[str, str]],
    Dict[str, Dict[str, Dict[str, str]]],
]:
    """
    按 path scope 收集旧翻译。
    Keyed: scope 为 Languages 父路径（LoadFolders）。
    DefInjected: scope 为 Def 类型文件夹名，如 DesignationCategoryDef、ThingDefs。

    Returns:
        keyed_by_path: scope -> {key -> value}
        definjected_by_path_file: def_scope -> (file_rel -> {key -> value})
    """
    keyed_by_path: Dict[str, Dict[str, str]] = {}
    definjected_by_path_file: Dict[str, Dict[str, Dict[str, str]]] = {}

    processor = XMLProcessor()
    keyed_name = _get_config().language_config.get_value("keyed_dir", "Keyed")
    def_name = _get_config().language_config.get_value("definjected_dir", "DefInjected")

    for old_base_dir in old_base_dirs:
        old_base_dir = old_base_dir.strip() if isinstance(old_base_dir, str) else ""
        if not old_base_dir:
            continue
        lang_dirs_with_scope = _find_all_language_dirs_with_scope(old_base_dir, language)
        if not lang_dirs_with_scope:
            for subdir_type in ["keyed", "definjected"]:
                subdir = _get_language_subdir_path(old_base_dir, language, subdir_type)
                if subdir.exists():
                    parent = subdir.parent
                    if parent.name.lower() == language.lower():
                        lang_dirs_with_scope = [(str(parent), _get_lang_dir_scope(old_base_dir, str(parent)))]
                        break

        for lang_dir, scope in lang_dirs_with_scope:
            scope_norm = scope.replace("\\", "/") or ""
            for subdir_type, use_def_key in [("keyed", False), ("definjected", True)]:
                subdir = Path(lang_dir) / (def_name if use_def_key else keyed_name)
                if not subdir.exists():
                    continue
                xml_files = list(subdir.rglob("*.xml"))
                for xml_file in xml_files:
                    try:
                        file_rel = str(xml_file.relative_to(subdir)).replace("\\", "/")
                        # DefInjected: scope = Def 类型文件夹，如 DesignationCategoryDef
                        def_scope = file_rel.split("/")[0] if "/" in file_rel else ""
                        tree = processor.parse_xml(str(xml_file))
                        if tree is None:
                            continue
                        root = tree.getroot() if processor.use_lxml else tree
                        parent_map = (
                            {c: p for p in root.iter() for c in p}
                            if not processor.use_lxml
                            else None
                        )
                        for elem in root.xpath(".//*") if processor.use_lxml else root.iter():
                            key = (
                                _definjected_key_func(elem, root, parent_map)
                                if use_def_key
                                else processor._get_element_key(elem)
                            )
                            if not key:
                                continue
                            text = (elem.text or "").strip()
                            if not text:
                                continue
                            if use_def_key:
                                k = key_to_dot_notation(key)
                                if def_scope not in definjected_by_path_file:
                                    definjected_by_path_file[def_scope] = {}
                                if file_rel not in definjected_by_path_file[def_scope]:
                                    definjected_by_path_file[def_scope][file_rel] = {}
                                definjected_by_path_file[def_scope][file_rel][k] = text
                            else:
                                if scope_norm not in keyed_by_path:
                                    keyed_by_path[scope_norm] = {}
                                keyed_by_path[scope_norm][key] = text
                    except (OSError, ValueError, TypeError) as e:
                        logger.debug("跳过 %s: %s", xml_file, e)

    return keyed_by_path, definjected_by_path_file


def migrate_translations_to_new(
    old_base_dirs: Union[str, List[str]],
    new_base_dir: str,
    language: str,
    only_fill_empty: bool = True,
    use_scope_mapping: bool = True,
) -> int:
    """
    从多个旧翻译目录收集所有 key→译文，合并后按 key 一一对应写入新模板；无需移动文件。

    old_base_dirs 可为单个路径或路径列表；多个目录时从各处收集并合并（同 key 后者覆盖）。
    DefInjected 的 nested / flat_with_li / flat_all 可任意互导，读写时统一按 key 匹配。

    Args:
        old_base_dirs: 旧模组根/语言目录或 Keyed/DefInjected 文件夹；多个用列表，将合并收集
        new_base_dir: 新模组/模板根目录、语言目录、或 Keyed/DefInjected 文件夹
        language: 语言代码
        only_fill_empty: 为 True 时仅填充新文件中空项，不覆盖已有翻译
        use_scope_mapping: 为 True 时按 LoadFolders 路径(scope)映射旧→新；为 False 时
            扁平合并所有旧翻译，直接按 key 写入每个新目录（旧翻译收集不到或路径结构不同时使用）

    Returns:
        更新的文件数量
    """
    if isinstance(old_base_dirs, str):
        old_base_dirs = [old_base_dirs]
    old_base_dirs = [d.strip() for d in old_base_dirs if d and str(d).strip()]
    keyed_by_path, definjected_by_path_file = _collect_old_translations_by_path(
        old_base_dirs, language
    )
    total_keyed = sum(len(m) for m in keyed_by_path.values())
    total_def = sum(len(f) for sc in definjected_by_path_file.values() for f in sc.values())
    keyed_scopes = len(keyed_by_path)
    def_types = list(definjected_by_path_file)
    ui.print_info(
        f"从 {len(old_base_dirs)} 个旧目录收集到 Keyed {total_keyed} 条（{keyed_scopes} 个 path scope）、"
        f"DefInjected {total_def} 条（Def 类型: {', '.join(def_types) or '无'}）。"
    )
    if total_keyed == 0 and total_def == 0:
        logger.warning("未从旧目录收集到任何翻译，请确认旧目录下存在 Keyed/DefInjected 且 XML 中含译文")
        return 0
    new_lang_dirs_with_scope = _find_all_language_dirs_with_scope(new_base_dir, language)
    if not new_lang_dirs_with_scope:
        new_base = Path(new_base_dir)
        if (new_base / "Keyed").exists() or (new_base / "DefInjected").exists():
            new_lang_dirs_with_scope = [(str(new_base), "")]
        elif (new_base / language).exists():
            new_lang_dirs_with_scope = [(str(new_base / language), "")]
        else:
            fallback = _get_config().language_config.get_language_dir(new_base_dir, language)
            if fallback.exists():
                new_lang_dirs_with_scope = [(str(fallback), "")]
    if not new_lang_dirs_with_scope:
        logger.warning("新模组下未找到语言目录: %s", new_base_dir)
        ui.print_warning(f"新模组下未找到 Languages/{language} 目录: {new_base_dir}")
        return 0

    if use_scope_mapping:
        return _migrate_with_scope_mapping(
            keyed_by_path,
            definjected_by_path_file,
            new_base_dir,
            new_lang_dirs_with_scope,
            language,
            only_fill_empty,
        )
    return _migrate_without_scope_mapping(
        keyed_by_path,
        definjected_by_path_file,
        new_base_dir,
        new_lang_dirs_with_scope,
        language,
        only_fill_empty,
    )


def _migrate_with_scope_mapping(
    keyed_by_path: Dict[str, Dict[str, str]],
    definjected_by_path_file: Dict[str, Dict[str, Dict[str, str]]],
    new_base_dir: str,
    new_lang_dirs_with_scope: List[Tuple[str, str]],
    language: str,
    only_fill_empty: bool,
) -> int:
    """
    使用 path scope 映射的迁移。
    Keyed: 按 LoadFolders 路径（1.5→1.6）匹配后写入。
    DefInjected: 按 Def 类型（DesignationCategoryDef 等）匹配，合并所有 def 类型后写入每个语言目录。
    """
    old_keyed_scopes = list(keyed_by_path)
    new_scopes = [s for _, s in new_lang_dirs_with_scope]
    old_ver, new_ver = _infer_path_versions(old_keyed_scopes, new_scopes)
    logger.info("Keyed 路径版本映射: 旧 %s -> 新 %s", old_ver, new_ver)
    def_types = list(definjected_by_path_file)
    ui.print_info(
        f"找到 {len(new_lang_dirs_with_scope)} 个语言目录；Keyed 按路径映射（{old_ver}→{new_ver}）；"
        f"DefInjected 按 Def 类型（{', '.join(def_types) or '无'}）"
    )
    # DefInjected: 合并为 key→value，只按 key 匹配，不按文件路径
    definjected_flat = {
        k: v
        for _def_scope, file_map in definjected_by_path_file.items()
        for f in file_map.values()
        for k, v in f.items()
    }
    updated = 0
    for new_lang_dir, new_scope in new_lang_dirs_with_scope:
        new_scope_norm = (new_scope or "").replace("\\", "/")
        matched_old_scope = None
        for old_scope in old_keyed_scopes:
            if _map_old_scope_to_new(old_scope, new_scope_norm, old_ver, new_ver):
                matched_old_scope = old_scope
                break
        if matched_old_scope is not None:
            keyed_map = keyed_by_path.get(matched_old_scope, {})
            if keyed_map:
                updated += _update_xml_in_subdir(
                    new_base_dir,
                    language,
                    "keyed",
                    keyed_map,
                    merge=True,
                    only_fill_empty=only_fill_empty,
                    language_dir_override=new_lang_dir,
                )
        if definjected_flat:
            updated += _update_xml_in_subdir(
                new_base_dir,
                language,
                "definjected",
                definjected_flat,
                merge=True,
                only_fill_empty=only_fill_empty,
                language_dir_override=new_lang_dir,
                translations_by_file=None,
            )
    return updated


def _migrate_without_scope_mapping(
    keyed_by_path: Dict[str, Dict[str, str]],
    definjected_by_path_file: Dict[str, Dict[str, Dict[str, str]]],
    new_base_dir: str,
    new_lang_dirs_with_scope: List[Tuple[str, str]],
    language: str,
    only_fill_empty: bool,
) -> int:
    """不使用 scope 映射的迁移：扁平合并所有旧翻译，直接按 key 写入每个新目录。"""
    keyed_flat: Dict[str, str] = {}
    for m in keyed_by_path.values():
        keyed_flat.update(m)
    definjected_flat: Dict[str, str] = {}
    for sc in definjected_by_path_file.values():
        for f_map in sc.values():
            definjected_flat.update(f_map)
    ui.print_info(
        f"扁平模式：合并后 Keyed {len(keyed_flat)} 条、DefInjected {len(definjected_flat)} 条，写入 {len(new_lang_dirs_with_scope)} 个语言目录"
    )
    updated = 0
    for new_lang_dir, _ in new_lang_dirs_with_scope:
        if keyed_flat:
            updated += _update_xml_in_subdir(
                new_base_dir,
                language,
                "keyed",
                keyed_flat,
                merge=True,
                only_fill_empty=only_fill_empty,
                language_dir_override=new_lang_dir,
            )
        if definjected_flat:
            updated += _update_xml_in_subdir(
                new_base_dir,
                language,
                "definjected",
                definjected_flat,
                merge=True,
                only_fill_empty=only_fill_empty,
                language_dir_override=new_lang_dir,
                translations_by_file=None,
            )
    return updated


def _update_xml_in_subdir(
    mod_dir: str,
    language: str,
    subdir_type: str,
    translations: Dict[str, str],
    merge: bool = True,
    only_fill_empty: bool = False,
    language_dir_override: Optional[str] = None,
    translations_by_file: Optional[Dict[str, Dict[str, str]]] = None,
) -> int:
    """仅在指定子目录(Keyed/DefInjected)内更新翻译。
    translations_by_file 非空时按 key+file 双校验：仅对每个 xml 文件应用其 file 路径对应的译文。
    """
    if not translations and not translations_by_file:
        return 0
    if language_dir_override:
        subdir = Path(language_dir_override) / subdir_type.lower()
    else:
        subdir = _get_config().language_config.get_language_subdir(
            mod_dir, language, subdir_type
        )
        if not subdir.exists():
            subdir = _get_language_subdir_path(mod_dir, language, subdir_type)
    if language_dir_override and subdir_type.lower() == "definjected":
        def_name = _get_config().language_config.get_value("definjected_dir", "DefInjected")
        subdir = Path(language_dir_override) / def_name
    elif language_dir_override and subdir_type.lower() == "keyed":
        keyed_name = _get_config().language_config.get_value("keyed_dir", "Keyed")
        subdir = Path(language_dir_override) / keyed_name
    if not subdir.exists():
        logger.warning("语言子目录不存在: %s", subdir)
        return 0
    if subdir_type.lower() == "definjected":
        config = XMLProcessorConfig(max_file_size=500 * 1024 * 1024)  # 500MB
        processor = XMLProcessor(config=config)
    else:
        processor = XMLProcessor()
    updated_count = 0
    generate_key_func = (
        _definjected_key_func if subdir_type.lower() == "definjected" else None
    )

    if subdir_type.lower() == "definjected":
        normalized: Dict[str, str] = {}
        for key, value in translations.items():
            k = key_to_dot_notation(key)
            normalized[k] = value
        translations = normalized

    xml_files = list(Path(subdir).rglob("*.xml"))
    total_files = len(xml_files)
    if total_files == 0:
        return 0

    ui.print_info(f"正在更新 {subdir_type} 目录中的 {total_files} 个文件...")

    for i, xml_file in enumerate(xml_files, 1):
        try:
            # key+file 双校验：仅对该文件路径的译文应用
            if translations_by_file:
                try:
                    rel = xml_file.relative_to(subdir)
                    file_key = str(rel).replace("\\", "/")
                except ValueError:
                    file_key = xml_file.name
                file_translations = translations_by_file.get(file_key, {})
                if subdir_type.lower() == "definjected" and file_translations:
                    norm_file: Dict[str, str] = {}
                    for key, value in file_translations.items():
                        k = key_to_dot_notation(key)
                        norm_file[k] = value
                    file_translations = norm_file
            else:
                file_translations = translations
            if not file_translations:
                ui.print_progress_bar(i, total_files, prefix="更新文件")
                continue
            tree = processor.parse_xml(str(xml_file))
            if tree is None:
                logger.warning("跳过（解析失败或文件过大）: %s", xml_file.name)
                ui.print_info(
                    "跳过: %s（可能文件过大超过默认限制或解析失败，DefInjected 已使用 500MB 限制）"
                    % xml_file.name
                )
                ui.print_progress_bar(i, total_files, prefix="更新文件")
                continue
            if update_translations(
                processor,
                tree,
                file_translations,
                generate_key_func=generate_key_func,
                merge=merge,
                include_attributes=True,
                only_fill_empty=only_fill_empty,
            ):
                processor.save_xml(tree, str(xml_file))
                updated_count += 1
            elif subdir_type.lower() == "definjected":
                logger.debug("未修改: %s（key 未匹配 / 仅填充空项且已有内容 / 或 CSV 译文与当前相同）", xml_file.name)
                ui.print_info(
                    "未修改: %s（可能 key 不一致、仅填充空项且节点已有内容、或 CSV 译文与当前相同）"
                    % xml_file.name
                )

            # 显示进度条
            ui.print_progress_bar(i, total_files, prefix="更新文件")

        except FileNotFoundError:
            logger.error("XML文件不存在: %s", xml_file)
        except PermissionError:
            logger.error("无权限访问XML文件: %s", xml_file)
        except (OSError, ValueError, TypeError) as e:
            logger.error("处理XML文件失败: %s: %s", xml_file, e)

    # 完成进度条
    ui.print_info("")  # 换行
    return updated_count


def update_translations(
    processor: XMLProcessor,
    tree: Any,
    translations: Dict[str, str],
    generate_key_func: Optional[Callable] = None,
    merge: bool = True,
    include_attributes: bool = True,
    only_fill_empty: bool = False,
) -> bool:
    """
    更新 XML 中的翻译。当 only_fill_empty=True 时也会处理无文本节点，仅填充空项。
    用于 DefInjected 时，nested / flat_with_li / flat_all 任意格式均可作为目标，按统一 key 写入。

    Args:
        processor (XMLProcessor): XML处理器实例
        tree (Any): XML 树对象
        translations (Dict[str, str]): 翻译字典
        generate_key_func (Optional[Callable]): 生成键的函数（DefInjected 用）
        merge (bool): 是否合并更新
        include_attributes (bool): 是否更新属性
        only_fill_empty (bool): 仅当当前为空时写入（用于旧翻译迁移）

    Returns:
        bool: 是否更新成功
    """
    from utils.utils import sanitize_xml, normalize_xml_entities_in_text

    modified = False
    root = tree.getroot() if processor.use_lxml else tree
    parent_map = (
        {c: p for p in root.iter() for c in p} if not processor.use_lxml else None
    )

    def get_key(elem):
        return (
            generate_key_func(elem, root, parent_map)
            if generate_key_func
            else processor._get_element_key(elem)
        )

    elements = root.xpath(".//*") if processor.use_lxml else root.iter()

    for elem in elements:
        # 更新文本内容（含无文本节点，便于 only_fill_empty 填充）
        key = get_key(elem)
        if not key:
            continue
        # 精确匹配，查找时统一用点号形式（与 collect 时 key_to_dot_notation 一致）
        key_norm = key_to_dot_notation(key)
        value = translations.get(key_norm) or translations.get(key)
        # DefInjected 迁移：支持旧 flat_all / flat_with_li / nested 与任意新格式互导
        if value is None and generate_key_func is not None:
            tag = getattr(elem, "tag", None)
            tag_local = _definjected_tag_local(tag) if isinstance(tag, str) else ""
            # 1) 新模板是 <li> 时：旧 flat_all 可能为 .0、.1，用前缀匹配
            if tag_local == "li":
                prefix = key_norm + "."
                candidates = [k for k in translations if k.startswith(prefix)]
                if len(candidates) == 1:
                    value = translations[candidates[0]]
                elif len(candidates) > 1:
                    value = translations.get(prefix + "RMBLabel") or translations.get(candidates[0])
            # 2) 按后缀匹配：旧翻译 key 可能带不同前缀（如不同 Def 文件夹结构），用路径后缀唯一匹配
            # 注意：多个候选时必须匹配 def 前缀，否则会误用其他 key（如 Hygiene.label）覆盖 SaunaRoom.label
            if value is None and "." in key_norm:
                suffix = key_norm.split(".", 1)[-1]
                candidates = [k for k in translations if k == suffix or k.endswith("." + suffix)]
                if len(candidates) == 1:
                    value = translations[candidates[0]]
                elif len(candidates) > 1:
                    def_name = key_norm.split(".")[0]
                    for c in candidates:
                        if c.startswith(def_name + "."):
                            value = translations[c]
                            break
                    # 无匹配 def 时不再用 candidates[0]，避免误覆盖
            # 3) stages 匹配：新模板 stages.0/stages.1 与旧 stages.moderate/stages.severe 等互导
            if value is None and generate_key_func is not None:
                m = re.match(r"^([^.]+\.stages)\.(\d+)(\..+)$", key_norm)
                if m:
                    prefix, idx_str, suffix = m.group(1), m.group(2), m.group(3)
                    idx = int(idx_str)
                    pattern = re.escape(prefix) + r"\.[^.]+" + re.escape(suffix)
                    raw = [k for k in translations if re.match(pattern + r"$", k)]
                    # 按常见严重程度排序，使 0=最轻 对应 moderate/minor 等
                    _STAGE_ORDER = (
                        "trivial", "minor", "moderate", "major", "severe", "extreme",
                        "need_the_bathroom", "bursting", "cold_water", "cold_shower", "cold_bath",
                    )
                    def _stage_sort_key(k):
                        parts = k[len(prefix) + 1 :].split(".")  # 取 stages.xxx 的 xxx
                        name = parts[0] if parts else ""
                        base = name.split("-")[0]  # extreme-0 -> extreme
                        return (_STAGE_ORDER.index(base) if base in _STAGE_ORDER else 999, name)
                    candidates = sorted(raw, key=_stage_sort_key)
                    if idx < len(candidates):
                        value = translations[candidates[idx]]
        if value is not None:
            value = normalize_xml_entities_in_text(value)
            current = normalize_xml_entities_in_text((elem.text or "").strip())
            # 迁移时：若当前内容像英文占位（如 creation(tag=...)->...），仍用旧翻译覆盖
            if only_fill_empty and current and not _looks_like_en_placeholder(current):
                pass
            elif only_fill_empty:
                elem.text = sanitize_xml(value)
                modified = True
            elif merge and current != value:
                elem.text = sanitize_xml(value)
                modified = True
            elif not merge:
                elem.text = sanitize_xml(value)
                modified = True

        # 更新属性
        if include_attributes:
            for attr_name, attr_value in elem.attrib.items():
                if isinstance(attr_value, str) and attr_value.strip():
                    attr_key = f"{key_norm}.{attr_name}"
                    if attr_key not in translations:
                        continue
                    current_attr = normalize_xml_entities_in_text((attr_value or "").strip())
                    attr_val = normalize_xml_entities_in_text(translations[attr_key])
                    if only_fill_empty and current_attr and not _looks_like_en_placeholder(current_attr):
                        pass
                    elif only_fill_empty:
                        elem.set(attr_name, sanitize_xml(attr_val))
                        modified = True
                    elif merge and current_attr != attr_val:
                        elem.set(attr_name, sanitize_xml(attr_val))
                        modified = True
                    elif not merge:
                        elem.set(attr_name, sanitize_xml(attr_val))
                        modified = True

    return modified


def _verify_import_results(
    mod_dir: str, language: str, template_dir: Optional[Path] = None
) -> bool:
    """验证导入结果（template_dir 未提供时用 get_template_dir 解析，兼容 Languages/<语言> 与直接 <语言>）"""
    if template_dir is None:
        template_dir = _get_config().language_config.get_template_dir(
            mod_dir, language
        )
    template_dir = Path(template_dir)
    if not template_dir.exists():
        logger.error("导入后模板目录不存在")
        return False
    keyed_name = _get_config().language_config.get_value("keyed_dir", "Keyed")
    def_name = _get_config().language_config.get_value("definjected_dir", "DefInjected")
    keyed_subdir = template_dir / keyed_name
    def_subdir = template_dir / def_name
    has_keyed = any(keyed_subdir.rglob("*.xml")) if keyed_subdir.exists() else False
    has_definjected = (
        any(def_subdir.rglob("*.xml")) if def_subdir.exists() else False
    )
    if not has_keyed and not has_definjected:
        logger.warning("导入后未找到翻译文件")
        return False
    logger.info("导入结果验证通过")
    return True
