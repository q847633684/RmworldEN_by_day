# 智能翻译合并器（SmartMerger）合并逻辑审查

## 一、数据约定

- **输入 input_data**：来自 Defs 的「英文源」或既有 Keyed/DefInjected 提取结果  
  - 五元组：`(key, text, tag, rel_path, en_text)`  
  - 在 merge 模式下，input 来自 Defs 时：`text` = 英文原文，`en_text` 同或空。
- **输出 output_data**：现有翻译目录（DefInjected/Keyed）的提取结果  
  - 五元组：`(key, text, tag, rel_path, en_text)`  
  - `text` = 当前译文（如中文），`en_text` = 当前记录的英文源。
- **合并结果**：六元组 `(key, text, tag, rel_path, en_text, history)`，写回 XML 时使用前 5 项，`text` 必须为**译文**，不能是英文。

## 二、合并流程概览

1. **格式规范化**：四/五/六元组统一成五元组。
2. **映射**  
   - 若存在六元组（含 def_type）：`input_map` 用 `(key, def_type)` 区分同 key 不同 Def；否则用 `key`。  
   - `output_map`：`key -> [所有 output 项]`（同 key 可多文件）。
3. **scope**：`_scope_from_rel_path(rel_path)` 取路径第一段，用于按「文件/Def 类型」对齐 input 与 output。
4. **遍历 output_map**，对每个 `(key, scope)`：
   - **重复 key**：同一 scope 内同一 key 出现多次 → 第 2 个及以后标 `"重复key，需删除"`。
   - **不变**：`normalized(in_item[1]) == normalized(out_item[4])`（新英文 = 原存英文）→ 仅统计，若 `include_unchanged` 则保留 `(key, out_item[1], ..., out_item[4], "")`。  
     - 正确：保留现有译文 `out_item[1]`。
   - **更新**：英文源变化。  
     - **原逻辑 bug**：在「有原英文」分支里曾写 `text=in_item[1]`，即把**英文**写入译文位，导致写回 XML 时用英文覆盖译文。  
     - **修正**：两分支均使用 `text=out_item[1]`（保留现有译文），`en_text=in_item[1]`（新英文），仅更新历史说明。
   - **输出有、输入无**：本轮不处理，留给后面「过时」逻辑。
5. **新增**：input 中有而 output 中该 key（及 scope）无的项，追加 `(key, in_item[1], ..., history="翻译内容: ..., 新增于...")`。  
   - 此处 `in_item[1]` 为英文源，作为占位；后续可由机翻/人工填译文。
6. **过时**：output 中有而 input 中该 key+scope 无的项，标 `"过时key，需删除"` 或 `"未识别字段，谨慎删除"`（由配置的 translation_fields 决定）。

## 三、策略与元数据

- **merge_strategy**（`input_priority` / `output_priority`）：目前仅影响 **tag、rel_path** 取 input 还是 output，不决定「谁覆盖译文」；合并后译文位始终保留 output 的译文（或新增时用 input 的英文占位）。
- **preserve_metadata**：为 True 且 `output_priority` 时，tag、rel_path 取 output，否则取 input。

## 四、已修复问题

- **「更新」且「有原英文」时误用英文覆盖译文**  
  - 位置：`smart_merge_translations` 中 `else` 分支（约 314–323 行）。  
  - 原代码：`merged.append((key, in_item[1], ...))`，把 Defs 的英文写入 `text`。  
  - 修复：改为 `merged.append((key, out_item[1], ..., in_item[1], ...))`，保留 `out_item[1]` 为译文，仅用 `in_item[1]` 更新 `en_text` 与 history。

## 五、建议（可选）

- **merge_strategy 与「谁赢」**：若未来需要「输入优先」在内容上也覆盖译文，应在「更新」分支显式按策略选择 `text` 取 `in_item[1]` 还是 `out_item[1]`，并写清语义（例如仅 Defs 带译文时才允许覆盖）。
- **路径规范化**：`_scope_from_rel_path` 内仍有 `(r or "").replace("\\", "/").strip()`，可与 `utils.path_utils.normalize_slashes` 统一。
- **单测**：为「更新且有原英文」加一条用例，断言合并结果中 `text` 为原译文、`en_text` 为新英文，防止回归。
