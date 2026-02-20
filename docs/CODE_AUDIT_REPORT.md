# Day_zh 代码复用与合并审核报告

> 生成日期：2025-02  
> 范围：全项目（extract / batch / import_template / translate / utils / user_config / corpus / full_pipeline 等）

---

## 一、项目结构概览

| 目录/模块 | 职责 |
|-----------|------|
| **main.py** | 入口；菜单与模式分发（提取、机翻、导入、批量、语料、全流程、配置、清理、迁移） |
| **extract/** | 提取：core/extractors（keyed/definjected/defs）、exporters、workflow（manager/handler/interaction）、utils/merger（SmartMerger） |
| **import_template/** | 导入：CSV → XML（importers.py, handler.py） |
| **translate/** | 机翻：core（placeholders、各翻译器、resume_base）、unified_translator、handler |
| **batch/** | 批量：batch_processor、handler（原版提取、按模组分拆/合并 CSV） |
| **full_pipeline/** | 全流程：extract → translate → import |
| **corpus/** | 平行语料：parallel_corpus、handler |
| **user_config/** | 配置：core、api、path_manager |
| **utils/** | 公共：utils.py、ui_style、interaction、logging_config、error_handling、constants、xml_utils、version_utils、rimworld_about |

---

## 二、可复用与可合并项（按优先级）

### 1. 高优先级：路径处理重复（强烈建议合并）

**现象**：多处手写 `Path(...).resolve()`、`relative_to(base)`、`.replace("\\", "/")`，逻辑一致但分散。

| 位置 | 用途 | 建议 |
|------|------|------|
| `extract/workflow/handler.py` | 计算 `scan_labels_for_roots`、`r_label`、`_short_csv_basename` 内路径分割 | 使用统一路径工具 |
| `extract/workflow/manager.py` | 路径规范化（约 4 处） | 同上 |
| `extract/utils/merger.py` | `(r or "").replace("\\", "/").strip()` | 同上 |
| `import_template/importers.py` | 路径与 key 规范化（约 13+ 处） | 同上 |
| `import_template/handler.py` | CSV 路径、目录列表 resolve | 同上 |
| `batch/handler.py` | 路径 resolve、relative_to、replace（约 4 处） | 同上 |
| `user_config/path_manager.py` | `str(path_obj.resolve())` 等 | 与统一工具对齐 |

**建议新增**：`utils/path_utils.py`（或扩展现有 `utils/utils.py`）

- `normalize_slashes(s: str) -> str`：统一 `s.replace("\\", "/").strip()`
- `rel_path_str(base: Path | str, path: Path | str) -> str`：`str(Path(path).resolve().relative_to(Path(base).resolve())).replace("\\", "/")`，异常时回退为 `Path(path).name` 或 `"?"`
- `resolve_path(p: Path | str) -> Path`：`Path(p).resolve()`

**复用点**：handler 中“根目录 → `/`、否则相对路径”的标签计算可改为调用 `rel_path_str(scan_base_path, r)`，根目录特判为 `"/"`。

---

### 2. 高优先级：按 key 去重逻辑重复（建议合并）

**现象**：同一“按 key 去重、保留首次”逻辑出现两处。

| 位置 | 说明 |
|------|------|
| `extract/workflow/handler.py` | `_dedupe_translations_by_key(keyed_list, def_list)`（约 57–73 行），被 merge / incremental 多根分支调用 |
| `extract/workflow/manager.py` | `extract_and_generate_templates_from_roots` 内联实现（约 458–477 行），与 handler 逻辑一致 |

**建议**：

- 在 **extract/utils/merger.py** 中新增（或从 handler 迁入）一个函数，例如：  
  `dedupe_translations_by_key(keyed_list: List, def_list: List) -> Tuple[List, List]`
- `extract/workflow/handler.py` 改为从 merger 导入并调用该函数。
- `extract/workflow/manager.py` 删除内联去重，改为调用同一函数。

这样“多根合并按 key 去重”只有一处实现，便于维护和测试。

---

### 3. 高优先级：CSV 表头与编码（建议集中）

**现象**：翻译 CSV 的列名与编码在多处硬编码。

| 位置 | 内容 |
|------|------|
| `extract/workflow/manager.py` | `writer.writerow(["key", "text", "tag", "file", "type"])`（约 992 行） |
| `batch/handler.py` | `fieldnames = ["key", "text", "tag", "file", "type"]`（约 477 行） |
| `translate/core/placeholders.py` | 同结构表头（约 104–108 行） |
| `import_template/importers.py` | 校验/读取 CSV 时依赖相同列名 |

**建议**：

- 在 **utils/constants.py**（或新建 **utils/csv_utils.py**）中定义：  
  `CSV_TRANSLATION_HEADER = ("key", "text", "tag", "file", "type")`  
  以及可选：`CSV_ENCODING_READ = "utf-8-sig"`、`CSV_ENCODING_WRITE = "utf-8"`。
- 所有写 CSV 表头、校验表头、DictReader fieldnames 的地方改为使用该常量。
- 若多处存在 `open(..., encoding="utf-8"|"utf-8-sig", newline="")` + csv 读写，可再抽成 `open_csv_reader(path)` / `open_csv_writer(path)` 放在 `utils/csv_utils.py`，内部使用上述常量和统一 newline。

---

### 4. 中优先级：Key 转点号格式（DefInjected 风格）

**现象**：同一段“key 中 `\`/`/` 转 `.`”的逻辑在 importers 中重复 5 次。

| 位置 | 代码 |
|------|------|
| `import_template/importers.py` | 538、615、764、832、856 行：`k = key.replace("\\", "/").replace("/", ".") if "/" in key or "\\" in key else key` |

**建议**：

- 在 **utils/path_utils.py**（或 **utils/utils.py**）中新增：  
  `def key_to_dot_notation(key: str) -> str`
- 实现即上述一行逻辑（或先 `normalize_slashes(key)` 再 `replace("/", ".")`）。
- `import_template/importers.py` 中 5 处均改为调用 `key_to_dot_notation(key)`。

---

### 5. 中优先级：扫描标签计算（“/” vs 相对路径）

**现象**：handler 中两处（多根 merge、多根 rebuild）用相同规则根据 `roots` 和 `scan_base` 计算“扫描标签”列表。

| 位置 | 说明 |
|------|------|
| `extract/workflow/handler.py` | merge/incremental 多根：对每个 `r in roots` 算 `r_label`（根目录 `/`，否则 `relative_to(scan_base_path)`，异常用 `Path(r).name`） |
| `extract/workflow/handler.py` | rebuild 多根：`scan_labels_for_roots` 用同样规则 |

**建议**：

- 在 **extract/workflow/handler.py** 或 **extract/workflow/manager.py** 中新增：  
  `def compute_scan_labels_for_roots(roots: List[str], scan_base: str) -> List[str]`  
  实现现有“根目录 → `/`，否则相对路径字符串（正斜杠），异常 → 目录名”的逻辑。
- 两处多根循环均改为调用该函数得到标签列表或单标签，避免重复实现。

---

### 6. 中优先级：模组名安全文件名

**现象**：将模组名转为安全文件名（非法字符替换、长度截断）仅在 extract handler 中实现。

| 位置 | 说明 |
|------|------|
| `extract/workflow/handler.py` | `_sanitize_mod_name_for_filename(name)`：`re.sub(r'[\\/:*?"<>|]', "_", ...)`，截断 64 字符 |

**建议**：

- 将该函数迁到 **utils/utils.py** 或 **utils/path_utils.py**，命名为如 `sanitize_mod_name_for_filename(name: str) -> str`。
- extract/workflow/handler 改为从 utils 导入；batch、corpus、full_pipeline 等如需“安全文件名”可复用同一函数。

---

### 7. 低优先级：CSV 读写封装

**现象**：多处直接 `open(..., encoding=..., newline="")` + `csv.DictReader`/`writer`，编码与 newline 不统一（如 importers 中 utf-8 vs utf-8-sig）。

| 位置 | 说明 |
|------|------|
| extract/workflow/manager.py | 写 CSV |
| batch/handler.py | 读/写 CSV |
| translate/core（placeholders、python_translator、google_translator、resume_base、java_translator） | 读/写 CSV |
| import_template/importers.py | 读 CSV（含 BOM 场景） |

**建议**：

- 在 **utils/csv_utils.py** 中提供：  
  - `open_csv_reader(path, encoding=CSV_ENCODING_READ)`  
  - `open_csv_writer(path, encoding=CSV_ENCODING_WRITE)`  
  内部统一 `newline=""`，返回文件对象或配合 `csv` 使用。
- 各模块逐步改为使用上述封装 + `CSV_TRANSLATION_HEADER`，便于统一 BOM 与编码。

---

### 8. 低优先级：提取器 rel_path 计算

**现象**：keyed 与 definjected 提取器都用“xml 文件相对某目录的路径字符串”。

| 位置 | 代码 |
|------|------|
| `extract/core/extractors/keyed.py` | `rel_path = str(xml_file.relative_to(keyed_dir))`（约 98 行） |
| `extract/core/extractors/definjected.py` | `rel_path = str(xml_file.relative_to(definjected_dir))`（约 97 行） |

**建议**：

- 若引入 `utils/path_utils.py` 的 `rel_path_str(base, path)`，可在此处统一使用，保证与项目其它地方一致使用正斜杠；否则可保留现状，仅在后续统一路径规范时再收口。

---

### 9. 可选：目录名常量

**现象**：`"Keyed"`、`"DefInjected"`、`"Defs"`、`"LoadFolders.xml"`、`"About"`、`"Languages"` 等散落在 manager、path_manager、extractors、user_config 等处。

**建议**：

- 若希望进一步减少魔法字符串，可在 **utils/constants.py** 中增加例如：  
  `KEYED_DIR = "Keyed"`、`DEFINJECTED_DIR = "DefInjected"`、`LOAD_FOLDERS_FILENAME = "LoadFolders.xml"` 等。
- 与 user_config 中已有配置（如 keyed_dir、definjected_dir）协调：要么常量与配置一致，要么仅配置生效、常量仅作默认值或兼容。

---

## 三、按文件汇总（建议改动一览）

| 文件 | 可复用/合并项 | 建议操作 |
|------|----------------|----------|
| **extract/workflow/handler.py** | 路径计算、去重、扫描标签、安全文件名 | 使用 path_utils；去重改为调用 merger.dedupe_translations_by_key；使用 compute_scan_labels_for_roots；_sanitize_mod_name_for_filename 迁到 utils |
| **extract/workflow/manager.py** | 内联去重、路径 replace、CSV 表头 | 调用 dedupe_translations_by_key；使用 path_utils；使用 CSV_TRANSLATION_HEADER（及可选 csv_utils） |
| **extract/core/extractors/keyed.py** | rel_path 计算 | 可选：使用 path_utils.rel_path_str |
| **extract/core/extractors/definjected.py** | rel_path 计算 | 同上 |
| **extract/utils/merger.py** | 路径 replace、新增去重函数 | 增加 dedupe_translations_by_key；路径处使用 path_utils |
| **import_template/importers.py** | 路径与 key 规范化、CSV 编码/表头 | 使用 path_utils、key_to_dot_notation；使用 CSV 常量和可选 csv_utils |
| **import_template/handler.py** | 路径 resolve | 使用 path_utils |
| **batch/handler.py** | 路径、CSV 表头与读写 | 使用 path_utils；使用 CSV_TRANSLATION_HEADER（及可选 csv_utils） |
| **translate/core/placeholders.py** | CSV 表头与打开方式 | 使用 CSV_TRANSLATION_HEADER 与 csv_utils（若引入） |
| **translate/core/*_translator.py、resume_base.py** | CSV 读写 | 可选：统一走 csv_utils |
| **user_config/path_manager.py** | 路径规范化 | 与 path_utils 对齐或统一用 _normalize_path |
| **utils/constants.py** | 已有模组路径等 | 增加 CSV_TRANSLATION_HEADER、CSV_ENCODING_*；可选增加目录名常量 |

---

## 四、建议实施顺序

1. **第一步**：路径与去重（影响面大、重复明显）  
   - 新增 `utils/path_utils.py`（normalize_slashes、rel_path_str、resolve_path）。  
   - 在 extract/utils/merger.py 中实现并导出 `dedupe_translations_by_key`；handler 与 manager 改为调用并删内联/重复实现。  
   - handler 中实现 `compute_scan_labels_for_roots` 并两处多根逻辑改用。

2. **第二步**：CSV 与 Key 规范  
   - 在 utils/constants.py（或 csv_utils）中定义 CSV_TRANSLATION_HEADER 与编码常量。  
   - 所有写表头/校验表头处改用常量。  
   - 在 utils 中实现 `key_to_dot_notation`，importers 中 5 处改用。

3. **第三步**：可选增强  
   - 将 `_sanitize_mod_name_for_filename` 迁到 utils 并复用。  
   - 视需要增加 csv_utils 的 open_csv_reader/writer，逐步替换各模块 CSV 打开逻辑。  
   - 提取器 rel_path、目录名常量等按需收口。

---

## 五、总结

- **可复用**：路径规范化、rel_path 字符串、key 转点号、安全文件名、CSV 表头与编码、按 key 去重、扫描标签计算。  
- **可合并**：handler 与 manager 的“按 key 去重”合并为 merger 中单一函数；多处路径/CSV/key 逻辑收口到 utils 或 extract/utils。  
- **收益**：减少重复、统一行为（尤其是路径与编码）、后续改表头或路径规则时改一处即可，测试与维护成本更低。

以上为完整审核结论与实施建议，可按优先级分阶段落地。
