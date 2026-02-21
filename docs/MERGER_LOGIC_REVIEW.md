# 智能翻译合并器（SmartMerger）合并逻辑审查

## 一、数据约定

- **输入 input_data**：来自 Defs 的「英文源」或既有 Keyed/DefInjected 提取结果  
  - 五元组：`(key, text, tag, rel_path, en_text)`  
  - 在 merge 模式下，input 来自 Defs 时：`text` = 英文原文，`en_text` 同或空。
- **输出 output_data**：现有翻译目录（DefInjected/Keyed）的提取结果  
  - 五元组：`(key, text, tag, rel_path, en_text)`  
  - `text` = 当前译文（如中文），`en_text` = 当前记录的英文源。
- **合并结果**：六元组 `(key, text, tag, rel_path, en_text, history)`，写回 XML 时使用前 5 项，`text` 必须为**译文**，不能是英文。

### 三个提取器返回的元组含义

| 位置 | Defs（六元组） | DefInjected（五元组） | Keyed（五元组） |
|------|----------------|------------------------|-----------------|
| **1 key** | defName.字段路径（如 Ability_Shoot.label） | 元素标签名（如 DefName.label，与 Defs key 一致） | 元素标签名（Keyed 的 key） |
| **2 text** | 英文原文（Defs 里就是英文） | 译文（如中文）或占位 | 译文（如中文）或占位 |
| **3 tag** | 字段标签（label、description 等） | 同上（label、description 等） | 同上 |
| **4 rel_path** | 该 xml 相对 **Defs 目录**的路径（如 MainButton.xml） | 该 xml 相对 **DefInjected 目录**的路径（如 ThingDef/ThingDef.xml） | 该 xml 相对 **Keyed 目录**的路径（如 Keyed.xml） |
| **5 en_text** | 同 text（Defs 里是英文） | EN 注释里的英文或空 | EN 注释里的英文或空 |
| **6 def_type** | Def 类型名（ThingDef、KeyBindingDef 等）；仅 Defs 有 | — | — |

- Defs 多一个 **def_type**，用于合并时 (key, def_type) 区分同 key 不同 Def 类型。
- **DefInjected 五元组里没有 def_type**，但合并时**仍然能区分同 key 不同 Def 类型**：合并器用**输出条目的 rel_path 的第一段**（即 `_scope_from_rel_path(out_item[3])`，如 `ThingDef/ThingDef.xml` → `ThingDef`）作为 scope，与输入的 (key, def_type) 里的 def_type 对齐；因此只要 DefInjected 的目录结构是「Def类型/xxx.xml」（第一段等于 Def 类型名），就能正确匹配。
- Keyed 没有 Def 类型概念，合并时按 key + scope（rel_path 第一段）匹配即可。

## 二、合并流程概览

1. **格式规范化**：四/五/六元组统一成五元组。
2. **映射**  
   - 若存在六元组（含 def_type）：`input_map` 用 `(key, def_type)` 区分同 key 不同 Def；否则用 `key`。  
   - `output_map`：`key -> [所有 output 项]`（同 key 可多文件）。
3. **scope**：`scope = _scope_from_rel_path(out_item[3])`，即 **rel_path 的第一段**（第一个 `/` 之前；若无 `/` 则整段 rel_path）。  
   - 实现：`p.split("/")[0] if "/" in p else p`（先 `replace("\\", "/").strip()`）。  
   - **rel_path 来源**：每条记录的元组第 4 项 `item[3]`。  
     - **Defs 提取**：`rel_path = f"{def_type}/{def_type}.xml"`，如 `"ThingDef/ThingDef.xml"` → scope = **"ThingDef"**（Def 类型名）。  
     - **DefInjected 提取**：xml 相对 DefInjected 目录的相对路径，如 `"ThingDef/ThingDef.xml"` 或 `"Core/Defs/....xml"` → scope = **"ThingDef"** 或 **"Core"**（目录/类型名）。  
     - **Keyed 提取**：xml 相对 Keyed 目录的相对路径，如 `"Keyed.xml"` 或 `"SomeMod/Keyed.xml"` → scope = **"Keyed.xml"** 或 **"SomeMod"**。  
   - **作用**：按「哪个文件/哪类 Def」把同一 key 的多条 output 分组，并与 input 的 (key, def_type) 或 key 对齐。
4. **遍历 output_map**，对每个 `(key, scope)`：
   - **重复 key**：同一 scope 内同一 key 出现多次 → 第 2 个及以后标 `"重复key，需删除"`。
   - **不变**：`normalized(in_item[1]) == normalized(out_item[4])`（新英文 = 原存英文）→ 仅统计，若 `include_unchanged` 则保留 `(key, out_item[1], ..., out_item[4], "")`。  
     - 正确：保留现有译文 `out_item[1]`。
   - **更新**：英文源变化。  
     - **原逻辑 bug**：在「无原英文」时曾把 `text=in_item[1]` 写入译文位，导致写回时用英文覆盖译文（已修正为保留 out_item[1]）。
     - **英文源有更新**（有原英文且新旧英文不同）：旧译文已不对应新英文，故 `text=in_item[1]`（**新英文占位**），`en_text=in_item[1]`，history 记录「英文源已更新，待重新翻译；原译文: ...」。写回后该条显示英文，需人工/机翻重译。
     - **无原英文**：保留现有译文 `text=out_item[1]`，仅更新 `en_text=in_item[1]`。
   - **输出有、输入无**：本轮不处理，留给后面「过时」逻辑。
5. **新增**：input 中有而 output 中该 key（及 scope）无的项，追加 `(key, in_item[1], ..., history="翻译内容: ..., 新增于...")`。  
   - 此处 `in_item[1]` 为英文源，作为占位；后续可由机翻/人工填译文。
6. **过时**：output 中有而 input 中该 key+scope 无的项，标 `"过时key，需删除"` 或 `"未识别字段，谨慎删除"`（由配置的 translation_fields 决定）。

## 三、策略与元数据

- **merge_strategy**（`input_priority` / `output_priority`）：目前仅影响 **tag、rel_path** 取 input 还是 output。译文位：不变/无原英文时保留 output 的译文；**英文源有更新**时用 input 的新英文占位待重翻；新增时用 input 的英文占位。
- **preserve_metadata**：为 True 且 `output_priority` 时，tag、rel_path 取 output，否则取 input。

## 四、Defs 提取中 def_type 与 key 的获取与区别

（逻辑在 `extract/core/extractors/defs.py` 的 `_extract_from_xml_file` 中。）

### def_type 的获取

- **来源**：当前 Def 节点（`def_node`）的 **类型**。
- **规则**：  
  - 若有 `Class` 属性：`def_type = class_attr.split(".")[-1]`，即取 **Class 的最后一段**（如 `Class="Verse.ThingDef"` → `"ThingDef"`；`Class="...OpinionDef_SexPart"` → `"OpinionDef_SexPart"`）。  
  - 若无 `Class`：`def_type = tag_local`，即 **XML 标签本地名**（如 `<BackstoryDef>` → `"BackstoryDef"`，`<HediffDef>` → `"HediffDef"`）。
- **含义**：RimWorld 的 **Def 类型**（ThingDef、AbilityDef、HediffDef、BackstoryDef 等），同一类型通常对应同一 DefInjected 子目录/文件（如 `ThingDef/ThingDef.xml`）。

### key 的获取

- **来源**：每条**可翻译字段**（label、description、stages.0.label 等）需要一条唯一标识。
- **规则**：  
  - 先有 `full_path = f"{def_type}/{def_name}.{clean_path}"`，其中 `def_name` 来自该 Def 的 `<defName>` 文本，`clean_path` 为字段在 Def 内的路径（如 `label`、`stages.0.label`）。  
  - 再 `key = full_path.split("/", 1)[-1]`，即 **去掉第一段**，得到 `defName.field_path`。  
- **示例**：`def_name="Ability_Shoot"`，`clean_path="label"` → key = **"Ability_Shoot.label"**；`clean_path="stages.0.label"` → key = **"Ability_Shoot.stages.0.label"**。
- **含义**：**单条翻译的唯一键**，格式为 `defName.字段路径`，与 DefInjected/Keyed 里使用的 key 一致。

### 区别小结

|        | def_type              | key                          |
|--------|------------------------|------------------------------|
| **层级** | 整个 Def 节点一个值     | 每个可翻译字段一个值          |
| **内容** | Def 类型名（ThingDef 等） | defName + 字段路径（如 MyDef.label） |
| **用途** | 分组、写回路径（如 ThingDef/ThingDef.xml）、合并时 (key, def_type) 区分 | 唯一标识一条翻译，与 DefInjected/Keyed 的 key 对应 |
| **数量** | 同一 XML 内同类型 Def 共用一个 def_type | 每条可翻译内容一条 key        |

同一 def_type 下会有多条不同 key（同一 Def 类型、多个 defName 或同一 defName 下多字段）。

### rel_path 与 def_type 的分工

**当前实现**：Defs 提取里 **rel_path** = 该 xml **相对 Defs 目录的路径**（如 `MainButton.xml`、`SubDir/Other.xml`），用 `rel_path_str(defs_dir, xml_file)` 得到；**def_type** 在六元组第 6 项，合并时用 **(key, def_type)** 与 output（DefInjected）的 (key, scope) 匹配，不依赖 rel_path。  
写回 DefInjected 时由合并结果中的 rel_path 决定写哪条；通常用 output_priority 保留 output 的 rel_path（DefInjected 的 `Def类型/Def类型.xml`），故写回路径仍按 Def 类型分目录。

### 示例：MainButton.xml 提取结果

文件路径示例：`…\Steam\steamapps\workshop\content\294100\2038874626\Defs\MainButton.xml`（根节点 `<Defs>`，内含多个 Def）。  
假设 Defs 目录为 `…\2038874626\Defs`，提取器会扫描该目录下所有 xml，对 **MainButton.xml** 中每个 Def 节点做如下处理（无 `Class` 时 `def_type` = 标签本地名）：

| # | def_type | key | text | tag | rel_path | en_text |
|---|----------|-----|------|-----|----------|---------|
| 1 | KeyBindingCategoryDef | DubsOptimizer.label | Dubs Performance Analyzer | label | KeyBindingCategoryDef/KeyBindingCategoryDef.xml | Dubs Performance Analyzer |
| 2 | KeyBindingCategoryDef | DubsOptimizer.description | Keybinds for Dubs Performance Analyzer. | description | KeyBindingCategoryDef/KeyBindingCategoryDef.xml | Keybinds for Dubs Performance Analyzer. |
| 3 | KeyBindingDef | DubsOptimizerKey.label | Dubs Performance Analyzer | label | KeyBindingDef/KeyBindingDef.xml | Dubs Performance Analyzer |
| 4 | KeyBindingDef | DubsOptimizerRestartKey.label | Restart game | label | KeyBindingDef/KeyBindingDef.xml | Restart game |
| 5 | KeyBindingDef | dpa_ToggleAlertBlock.label | Toggle Alerts | label | KeyBindingDef/KeyBindingDef.xml | Toggle Alerts |
| 6 | MainButtonDef | DubsOptimizer.label | Dubs Performance Analyzer | label | MainButtonDef/MainButtonDef.xml | Dubs Performance Analyzer |
| 7 | MainButtonDef | DubsOptimizer.description | Open Analyzer. | description | MainButtonDef/MainButtonDef.xml | Open Analyzer. |

说明：

- **def_type**：无 `Class` 时取 XML 标签名（KeyBindingCategoryDef、KeyBindingDef、MainButtonDef）。
- **key**：`defName.字段路径`，如 `DubsOptimizer.label`、`DubsOptimizerKey.label`；同一 defName 在不同 Def 类型下会重复（如两条 `DubsOptimizer.label` 分别属于 KeyBindingCategoryDef 和 MainButtonDef），合并时用 (key, def_type) 区分。
- **text / en_text**：Defs 里是英文原文，提取时二者相同。
- **rel_path**：该 **xml 相对 Defs 目录的路径**（如 `MainButton.xml`、`SubDir/Other.xml`），由 `rel_path_str(defs_dir, xml_file)` 得到；def_type 单独在六元组第 6 项，合并时用 (key, def_type) 匹配。

## 五、已修复问题

- **「更新」且「有原英文」时误用英文覆盖译文**（早期 bug，已修）  
  - 原代码：`merged.append((key, in_item[1], ...))` 在**无原英文**分支也曾误用，导致用英文覆盖译文。  
  - 当前逻辑：  
    - **无原英文**：保留现有译文 `text=out_item[1]`，仅更新 `en_text=in_item[1]`。  
    - **有原英文且英文源有更新**：旧译文已不对应新英文，故 `text=in_item[1]`（**新英文占位**），`en_text=in_item[1]`，history 记录「英文源已更新，待重新翻译；原译文: ...」。写回后该条显示英文，需人工/机翻重译。

**举例说明**：

- **输入（Defs 新提取）**：某条 key 的英文源从 "Attack" 改成了 "Attack enemy"。
  - `in_item = (key, "Attack enemy", tag, rel_path, "Attack enemy")`  
  - 即 `in_item[1]` = 新英文 **"Attack enemy"**。
- **输出（现有 DefInjected）**：这条 key 之前已经翻译过。
  - `out_item = (key, "攻击", tag, rel_path, "Attack", history)`  
  - 即 `out_item[1]` = 现有译文 **"攻击"**，`out_item[4]` = 原英文 **"Attack"**。

合并时属于「更新」（新英文 ≠ 原英文），且「有原英文」。

- **错误行为（最早）**：无区分地写 `text=in_item[1]`，导致用英文覆盖译文。  
- **当前行为**：  
  - 合并结果里 `text = in_item[1]` = **"Attack enemy"**（新英文占位），`en_text = in_item[1]`，history =「英文源已更新，待重新翻译；原译文: '攻击', 原英文: 'Attack' -> 新英文: 'Attack enemy'」。  
  - 写回 XML 后该条显示英文 "Attack enemy"，需重新翻译；原译文「攻击」保留在 history 中供参考。

## 六、导出方式可配置；合并用 (key, def_type) 区分

**1. 导出方式可在配置里选**

- **统一导出**：`export_translations` 按每条记录的 rel_path 分组写入。调用方（manager）负责：defs_by_type 时先将 def_type 转为 rel_path = `def_type/def_type.xml`，再传入；其他情况 rel_path 已在 item[3]。
- **当前逻辑**：`template_structure` **不是**用户单独选的，而是根据「数据来源」和「冲突处理」**自动定**的（`extract/workflow/interaction.py` 约 120–127 行）：  
  - 冲突为 merge / incremental → `"merge_logic"`（合并写回按 rel_path，不涉及模板结构）；  
  - 数据来源为 definjected_only → `"original_structure"`；  
  - 数据来源为 defs_only → `"defs_by_type"`。  
  所以**没有**在配置里单独一项「按什么文件结构导出」供用户改。若需要用户可设，可在交互流程里加一步「模板结构：保持原结构 / 按 Def 类型分组」或在 user_config 里增加默认项。

**2. 合并逻辑里用 def 和 key 区分同 key 不同条**

- 当输入为六元组（含 def_type）时，合并用 **(key, def_type)** 做唯一性：同一条 key（如 `DubsOptimizer.label`）在 **KeyBindingCategoryDef** 和 **MainButtonDef** 里算两条，不会互相覆盖。
- 所以可以用 **def（def_type）和 key** 一起分辨「同 key、不同 Def 类型」的 text，合并不会把不同 Def 类型下的同 key 混成一条。

## 七、是否用字面 "def"/"key" 做分支判断？

**不用。** 合并逻辑里**没有**用字符串 `"def"` 或 `"key"`（以及 `"keyed"`）做分支判断。

- **调用方（manager）**：Keyed 和 DefInjected **分开合并**。  
  - `smart_merge_translations(input_keyed, output_keyed)` → 只处理 Keyed；  
  - `smart_merge_translations(input_def, output_def)` → 只处理 DefInjected。  
  因此每次进入合并器的要么全是 Keyed，要么全是 DefInjected，合并器本身不需要区分「这是 key 还是 def」。

- **合并器内部**：  
  - 若输入是**六元组**（来自 Defs 扫描）：用 `(key, def_type)` 建 input_map，其中 `def_type = item[5]` 是 **Def 类型名**（如 `"ThingDef"`、`"AbilityDef"`），用来区分「同 key 不同 Def 类型」的条目，避免互相覆盖。  
  - 用 **scope** 对齐：`scope = _scope_from_rel_path(out_item[3])`，即 `rel_path` 的**第一段**（如 `"ThingDef"`、`"Core"`），用来按「哪个文件/哪种 Def」匹配 input 和 output。  
  所以这里用的是 **Def 类型名**（ThingDef、AbilityDef 等）和 **路径第一段**（scope），不是字面量 `"def"` 或 `"key"`。

- **小结**：  
  - 「Keyed 和 DefInjected 谁是谁」在 **manager 调用两次** 时已经区分好；  
  - 合并器里只按 **key + (def_type/scope)** 做匹配与去重，**不会**根据 `"def"` / `"key"` 做判断。

## 八、导出逻辑是否按 Def 文件格式？

**目录结构**：`definjected.py` 的 **`export_translations`** 统一按 **rel_path** 分组写入。manager 在 `template_structure="defs_by_type"` 时将 def_type 转为 `def_type/def_type.xml` 作为 rel_path，符合 RimWorld 要求。**merge 写回** 用 `_write_merged_translations`，同样按 rel_path 分组写入。

**文件内容**：无论 rel_path 来自原结构还是 def_type，写出的 **内容** 都是 **DefInjected 格式**（根节点 `<LanguageData>`，nested / flat_with_li / flat_all），不是 Defs 的 `<Defs><ThingDef>...</ThingDef></Defs>` 结构。游戏只从 DefInjected 读翻译，故不写成 Defs 树。

## 九、建议（可选）

- **merge_strategy 与「谁赢」**：若未来需要「输入优先」在内容上也覆盖译文，应在「更新」分支显式按策略选择 `text` 取 `in_item[1]` 还是 `out_item[1]`，并写清语义（例如仅 Defs 带译文时才允许覆盖）。
- **路径规范化**：`_scope_from_rel_path` 内仍有 `(r or "").replace("\\", "/").strip()`，可与 `utils.path_utils.normalize_slashes` 统一。
- **单测**：为「更新且有原英文」加一条用例，断言合并结果中 `text` 为新英文占位、`en_text` 为新英文、history 含「待重新翻译」及原译文，防止回归。
