# Day_zh 项目架构整理与优化方案

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
  └─ 不依赖 extract / translate / import_template 等业务

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
| 6 | 弱化 utils → user_config | `XMLProcessor` 等如需配置，通过构造函数/参数传入，避免顶层导入 UserConfigManager |

### 阶段三：命名与归属优化

| # | 任务 | 说明 |
|---|------|------|
| 7 | interaction 命名区分 | `extract.workflow.interaction` 可重命名为 `extract.workflow.extraction_flow` 或保持，但在文档中明确为「提取专用交互」 |
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
- `extract/batch_extract.py`：批量提取（从 batch 迁入）
- `utils/version_detection.py` 或 `utils/load_folders.py`（可选，用于解耦 user_config）

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

## 六、风险与回滚

- 移动代码时保持对外接口不变，main 仅改 import 路径
- 依赖解耦可能影响 path_manager 的版本检测逻辑，需回归测试
- 建议按阶段提交，每阶段通过测试后再进行下一阶段
