# Day_zh 项目架构整理与优化方案

## 〇、完整文件结构（当前）

```
Day_zh/
├── main.py                          # 主入口
├── __init__.py                      # 包入口
├── requirements.txt
├── TODO_TASKS.md
├── pytest.ini
├── .pylintrc
├── README.md
│
├── batch/                           # 批量工具（导入、汇总）
│   ├── __init__.py
│   ├── handler.py                   # 批量导入、汇总到根、handle_batch 子菜单
│   └── batch_processor.py
│
├── corpus/                          # 语料
│   ├── __init__.py
│   ├── handler.py
│   └── parallel_corpus.py
│
├── extract/                         # 提取
│   ├── __init__.py
│   ├── cleanup_outdated_keys.py     # 清理过时/重复 key
│   ├── merge_flow.md
│   ├── core/
│   │   ├── __init__.py
│   │   ├── extractors/              # DefsScanner, DefInjected, Keyed
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── defs.py
│   │   │   ├── definjected.py
│   │   │   └── keyed.py
│   │   ├── exporters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── definjected.py
│   │   │   └── keyed.py
│   │   └── filters/
│   │       ├── __init__.py
│   │       ├── content_filter.py
│   │       └── text_validator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── merger.py                # SmartMerger
│   ├── batch_extract.py             # 批量提取（Vanilla 前缀模组）
│   └── workflow/
│       ├── __init__.py
│       ├── handler.py               # handle_extract
│       ├── interaction.py           # InteractionManager（提取专用）
│       ├── manager.py               # TemplateManager
│       └── rel_path_converter.py
│
├── full_pipeline/                   # 完整流程
│   ├── __init__.py
│   └── handler.py                   # 单次完整流程、批量完整流程
│
├── import_template/                 # 导入
│   ├── __init__.py
│   ├── handler.py
│   └── importers.py                 # import_translations, migrate_translations_to_new
│
├── repair_translation/              # 修补翻译
│   ├── __init__.py
│   ├── handler.py
│   └── repair.py
│
├── translate/                       # 翻译
│   ├── __init__.py
│   ├── handler.py                   # handle_unified_translate, handle_restore_placeholders
│   ├── unified_translator.py
│   ├── translator_factory.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── placeholders.py
│   │   ├── google_translator.py
│   │   ├── java_translator.py
│   │   ├── python_translator.py
│   │   ├── resume_base.py
│   │   └── java_translate/          # Java 翻译 JAR 源码
│   │       └── RimWorldBatchTranslate/
│   │           ├── pom.xml
│   │           ├── build.sh, build.bat
│   │           ├── README.md
│   │           └── src/main/java/...
│   └── ...
│
├── user_config/                     # 配置
│   ├── __init__.py
│   ├── path_manager.py
│   ├── README.md
│   ├── api/                         # 各翻译 API 封装
│   │   ├── __init__.py
│   │   ├── base_api.py
│   │   ├── api_manager.py
│   │   ├── aliyun_api.py
│   │   ├── baidu_api.py
│   │   ├── google_api.py
│   │   ├── tencent_api.py
│   │   └── custom_api.py
│   ├── config/
│   │   ├── README.md
│   │   ├── translation_fields.yaml
│   │   ├── general_dictionary.yaml
│   │   ├── game_dictionary.yaml
│   │   ├── artist_dictionary.yaml
│   │   └── adult_dictionary.yaml
│   ├── core/
│   │   ├── __init__.py
│   │   ├── user_config.py
│   │   ├── system_config.py
│   │   ├── base_config.py
│   │   └── config_validator.py
│   └── ui/
│       ├── __init__.py
│       ├── main_config_ui.py
│       └── api_config_ui.py
│
├── utils/                           # 通用工具
│   ├── __init__.py
│   ├── constants.py
│   ├── load_folders.py              # LoadFolders 版本检测（get_load_folders_versions, get_version_dirs_from_fs）
│   ├── csv_utils.py
│   ├── path_utils.py
│   ├── xml_utils.py
│   ├── ui_style.py
│   ├── interaction.py               # 主菜单、通用交互
│   ├── rimworld_about.py
│   ├── version_utils.py
│   ├── utils.py                     # XMLProcessor, sanitize_xml
│   ├── error_handling.py
│   └── logging_config.py
│
├── docs/
│   ├── ARCHITECTURE_REORGANIZATION.md
│   ├── MERGER_LOGIC_REVIEW.md
│   ├── CODE_AUDIT_REPORT.md
│   ├── Defs_extraction_faq.md
│   └── UI_OPTIMIZATION_PLAN.md
│
├── tests/
│   ├── __init__.py
│   ├── test_smart_merger.py
│   ├── test_config.py
│   └── test_sanitize_xml.py
│
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   └── prompts/
└── logs/                            # 运行时日志
```

---

## 一、现状与目标

### 1.1 设计原则
- **各回各家**：功能归属到对应业务模块
- **职责单一**：每个模块边界清晰
- **依赖下沉**：业务层不反向依赖配置/工具层
- **消除循环**：避免模块间循环导入

### 1.2 当前主要问题
| 问题 | 影响 |
|------|------|
| user_config → extract 反向依赖 | 配置层依赖业务层，违背分层 |
| utils.utils → user_config | 工具层依赖配置，耦合度高 |
| 两个 interaction 模块命名混淆 | extract.workflow.interaction 与 utils.interaction |
| handle_batch 无主菜单入口 | 批量导入、汇总功能无法使用 |
| 完整流程/提取代码混在 batch | 违反「各回各家」 |
| TOTAL_CSV_NAME 多处定义 | 应统一到 utils.constants |
| PathManager 多处实例化 | 可统一从 UserConfigManager 获取 |
| cleanup_outdated_keys 归属模糊 | 在 extract 下但更偏「维护工具」 |

---

## 二、模块职责划分（整理后）

### 2.1 核心业务模块

| 模块 | 职责 | 包含内容 |
|------|------|----------|
| **extract** | 提取翻译模板 | 单次提取、批量提取（Vanilla 前缀）、extractors、exporters、merger、workflow、rel_path_converter、cleanup_outdated_keys |
| **translate** | 翻译与占位符 | 统一翻译入口、各翻译器、placeholders、恢复占位符 |
| **import_template** | 导入与迁移 | CSV 写入 XML、迁移旧翻译 |
| **full_pipeline** | 完整流程 | 单次完整流程、批量完整流程（提取→翻译→导入→汇总） |
| **batch** | 批量工具 | 批量导入、汇总到根目录（供 full_pipeline 或独立调用） |

### 2.2 工具与辅助模块

| 模块 | 职责 | 包含内容 |
|------|------|----------|
| **repair_translation** | 修补翻译 | 修复 Google Error 500 等 |
| **corpus** | 语料生成 | 英中平行语料 |
| **user_config** | 配置与路径 | UserConfigManager、PathManager、API 配置、UI |
| **utils** | 通用工具 | constants、csv_utils、path_utils、xml_utils、ui_style、interaction、logging 等 |

### 2.3 依赖方向（整理后）

```
main.py
  └─ 按需导入各模块 handler

full_pipeline  ← 完整流程
  ├─ extract (单次/批量提取)
  ├─ translate
  ├─ import_template
  └─ batch (aggregate, batch_import)

extract  ← 提取
  ├─ extract.core
  ├─ extract.utils (merger)
  └─ extract.workflow
  └─ utils, user_config (仅读取配置，不反向依赖)

batch  ← 批量工具
  ├─ aggregate_chinese_translations_to_root
  ├─ handle_batch_import_translations
  └─ 供 full_pipeline 或独立调用

user_config  ← 配置
  └─ 不依赖 extract / translate / import_template 等业务（版本检测从 utils.load_folders 获取）

utils  ← 工具
  └─ 尽量不依赖 user_config；必须处通过参数传入
```

---

## 三、整理任务清单

### 阶段一：代码归属调整（各回各家）

| # | 任务 | 说明 |
|---|------|------|
| 1 | 批量提取移至 extract | 创建 `extract/batch_extract.py`，包含 `handle_batch_vanilla_extract`、`scan_vanilla_mods`、`_batch_extract_one` |
| 2 | 批量完整流程移至 full_pipeline | `handle_batch_full_pipeline` 移到 `full_pipeline/handler.py`，调用 extract.batch_extract + translate + batch.aggregate |
| 3 | batch 保留为批量工具 | 只保留 `aggregate_chinese_translations_to_root`、`handle_batch_import_translations`、`handle_batch` 子菜单 |
| 4 | 常量统一 | `TOTAL_CSV_NAME` 移入 `utils.constants`，各模块引用 |

### 阶段二：依赖解耦

| # | 任务 | 说明 |
|---|------|------|
| 5 | 解除 user_config → extract | 将 `get_load_folders_versions`、`get_version_dirs_from_fs`、`get_content_roots_from_load_folders` 等抽到 `utils/version_detection.py` 或 `utils/load_folders.py`，user_config 只依赖 utils |
| 6 | 弱化 utils → user_config | 移除 `utils.utils` 中未使用的 UserConfigManager 依赖 ✅ |

### 阶段三：命名与归属优化

| # | 任务 | 说明 |
|---|------|------|
| 7 | interaction 命名区分 | `extract.workflow.interaction` 为**提取专用交互**（InteractionManager），与 `utils.interaction` 主菜单/通用交互区分 ✅ |
| 8 | cleanup_outdated_keys 归属 | 保留在 extract（与 merger 输出格式强相关），或移至 `tools/` 新建模块；当前建议保留 |
| 9 | PathManager 统一获取 | 从 `UserConfigManager.get_instance().path_manager` 或类似方式获取，减少各 handler 自行实例化 |

### 阶段四：入口与文档

| # | 任务 | 说明 |
|---|------|------|
| 10 | 打通 handle_batch 入口 | 在工具子菜单中增加「批量操作」入口，或合并到现有「提取模板→批量提取」后保留 batch 的导入/汇总为工具项 |
| 11 | 更新 __init__ 与 README | 确保各模块 `__all__`、README 与实际架构一致 |

---

## 四、文件级变更对照

### 4.1 新增文件
- `extract/batch_extract.py`：批量提取（从 batch 迁入）✅
- `utils/load_folders.py`：LoadFolders 版本检测（get_load_folders_versions, get_version_dirs_from_fs），解除 user_config→extract ✅

### 4.2 移动 / 合并
- `handle_batch_full_pipeline`：batch/handler.py → full_pipeline/handler.py
- `handle_batch_vanilla_extract`、`scan_vanilla_mods`、`_batch_extract_one`：batch/handler.py → extract/batch_extract.py
- `TOTAL_CSV_NAME`：batch 内联 → utils.constants

### 4.3 修改
- `main.py`：导入改为 full_pipeline.handle_batch_full_pipeline、extract.handle_batch_vanilla_extract
- `batch/handler.py`：移除已迁出代码，保留 aggregate、batch_import、handle_batch
- `utils.constants`：新增 TOTAL_CSV_NAME
- `user_config.path_manager`：若抽离版本检测，改为依赖 utils
- `extract/__init__.py`：导出 handle_batch_vanilla_extract
- `full_pipeline/__init__.py`：导出 handle_batch_full_pipeline

### 4.4 主菜单与子菜单（现状）
- 1 完整流程 → 1.1 单次 / 1.2 批量
- 2 提取模板 → 2.1 单次 / 2.2 批量
- 3 智能翻译
- 4 导入模板
- 5 工具 → 1 迁移 / 2 恢复占位符 / 3 修补 / 4 清理 / 5 语料
- 6 配置管理

建议在 5 工具 中增加「6 批量操作」入口，调用 `handle_batch`，提供「批量导入」「汇总到根」等子功能。

---

## 五、实施顺序建议

1. **阶段一**（代码归属）：1 → 4，立即执行
2. **阶段二**（依赖解耦）：5、6，需谨慎测试
3. **阶段三**（命名与归属）：7、8、9，可按需执行
4. **阶段四**（入口与文档）：10、11，最后收尾

---

## 六、变更记录与完成摘要

### 已完成的整理（2025-02）

| 阶段 | 任务 | 状态 |
|------|------|------|
| 一 | 批量提取移至 extract.batch_extract | ✅ |
| 一 | 批量完整流程移至 full_pipeline.handler | ✅ |
| 一 | batch 保留汇总、批量导入、handle_batch | ✅ |
| 一 | TOTAL_CSV_NAME 统一到 utils.constants | ✅ |
| 二 | 解除 user_config → extract（utils/load_folders.py） | ✅ |
| 二 | 移除 utils.utils 中未使用的 UserConfigManager | ✅ |
| 三 | 明确 extract.workflow.interaction 为提取专用 | ✅ |
| 四 | 工具子菜单增加「6 批量操作」入口 | ✅ |
| 四 | 更新 README、架构文档 | ✅ |
| 三 | PathManager 统一从 UserConfigManager.path_manager 获取 | ✅ |

### 新增/修改文件

- **新增**：`extract/batch_extract.py`、`utils/load_folders.py`
- **新增测试**：`tests/test_load_folders.py`、`tests/test_batch_extract.py`
- **修改**：`batch/handler.py`、`full_pipeline/handler.py`、`main.py`、`utils/interaction.py`、`extract/__init__.py`、`full_pipeline/__init__.py`、`extract/workflow/manager.py`、`user_config/path_manager.py`、`utils/utils.py`

### 依赖关系（整理后）

```
user_config → utils（无 extract 依赖）
batch       → utils.load_folders, import_template
extract     → utils, user_config（仅读取配置）
full_pipeline → extract.batch_extract, batch, translate, import_template
main        → 各模块 handler
```

### 待选优化（可按需执行）

- utils.logging_config / error_handling 对 UserConfigManager 的进一步解耦
