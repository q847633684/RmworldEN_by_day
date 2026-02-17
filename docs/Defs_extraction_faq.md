# Defs 提取常见问题

## 某个 Defs 文件能正常提取吗？

可以。只要满足以下条件，`Defs/GolemDefs/Hediffs_Mecha-Golem.xml` 这类文件会被正常扫描并提取：

1. **内容根选对**：运行「提取模板」时，**内容根**必须是**包含 Defs 的那一层目录**。  
   - 例如文件在：`...\1201382956\v1.6\Defs\GolemDefs\Hediffs_Mecha-Golem.xml`  
   - 内容根应选：`...\1201382956\v1.6`（这样 Defs 在 `v1.6/Defs` 下才会被找到）。  
   - 若只选 `...\1201382956`，而 Defs 实际在 `v1.6/Defs` 下，则不会扫描到该文件。

2. **XML 结构**：文件里要有带 `<defName>` 的节点（如 `<HediffDef><defName>XXX</defName>...</HediffDef>`），且节点内有可翻译字段（如 `label`、`description` 等，需在配置的「翻译字段」中）。

3. **输出位置**：提取结果**不是**按源文件名输出，而是**按 Def 类型**输出。  
   - 所有 `HediffDef`（不管来自哪个 xml）会合并到：**DefInjected/HediffDef/HediffDef.xml**  
   - 所以不要到输出里找 `Hediffs_Mecha-Golem.xml`，而应打开 **DefInjected/HediffDef/HediffDef.xml**，用该文件里的 `defName` 搜索对应 key（如 `XXX.label`、`XXX.description`）。

---

## HediffDef/HediffDef.xml 这种命名游戏能正常读吗？

**能。** RimWorld 对 DefInjected 的要求是：

- **子文件夹名**必须与 Def 类型一致（如 `HediffDef`、`ThingDef`），否则会报 "dir XXX 不对应任何 def 类型"。
- **子文件夹里的 XML 文件名**可以任意（官方示例里写的是 `AnyFileName.xml`），游戏只认「文件夹 = Def 类型」和「XML 里节点名 = DefName.字段」（如 `Beer.label`），不依赖具体文件名。

因此用 **HediffDef/HediffDef.xml**（即 DefInjected/Def类型名/Def类型名.xml）完全符合规范，游戏会正常读取。

---

## 为什么找不到某个文件里提取出来的内容？

常见原因：

| 原因 | 说明 |
|------|------|
| **内容根不对** | 内容根没选到「包含 Defs 的目录」（如应选 `v1.6` 却选了模组根），Defs 没被扫描到。 |
| **找错输出文件** | 输出按 **def 类型**分组，不按源文件名。应到 DefInjected/**Def类型名**/Def类型名.xml 里找，并用 defName 搜 key。 |
| **XML 有命名空间** | 根节点带 `xmlns="..."` 时，以前 def 类型可能变成 `{uri}HediffDef`，输出目录名会很长。现已改为自动去掉命名空间，输出目录为 `HediffDef`。 |
| **没有可翻译字段** | 该 def 里没有 label/description 等，或字段不在「翻译字段」配置中，则不会产生任何条目。 |
| **被过滤掉** | 内容被「非文本模式」或「忽略字段」过滤掉，也不会出现在结果里。 |

---

## 如何确认某个文件是否被扫到？

1. 提取时看日志：扫描 Defs 时会列出扫描到的 xml 数量；若内容根正确，该文件应被包含。  
2. 打开 **DefInjected/对应Def类型/对应Def类型.xml**（如 HediffDef），搜索该文件里出现的 **defName**，若有对应 key（如 `defName.label`），说明该文件已被提取。
