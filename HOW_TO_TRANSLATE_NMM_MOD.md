# 如何使用 Day_zh 汉化 nudity-matters-more-opinions mod

现在 Day_zh 已经能够处理具有 `Common/Defs` 结构的 mod 了！本指南将向你展示如何使用它。

## 📋 前置要求

- ✅ Day_zh 已安装并配置完成
- ✅ 已应用 Common/Defs 支持补丁（已在此会话中完成）
- ✅ nudity-matters-more-opinions mod 可访问

## 🚀 使用步骤

### 方式 1: 完整翻译管道 (推荐)

这是最简单的方式，一次性完成提取→翻译→导入。

```bash
# 1. 启动 Day_zh
python main.py

# 2. 选择 "1 - 完整翻译管道"
# 3. 按照提示操作：
#    - 选择英文 mod 目录: c:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\nudity-matters-more-opinions
#    - 选择输出目录
#    - 选择翻译模式（使用 Defs 扫描）
#    - 确认翻译字段
#    - 导出 CSV 并翻译
#    - 导入汉化结果
```

### 方式 2: 逐步处理 (适合细致调整)

#### Step 1: 提取翻译

```bash
python main.py
# 选择 "2 - 提取翻译模板"
```

在交互菜单中：
- **源模组目录**: `c:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\nudity-matters-more-opinions`
- **语言**: `English`
- **输出目录**: 选择一个本地输出文件夹（如 `D:\Translations\NMM\`)
- **目标语言**: `ChineseSimplified`

当提示 "检测到Defs目录" 时，选择 "是" 以包含 Defs 翻译。

**预期结果**：
- ✅ 导出 CSV 文件，包含 11,000+ 条翻译项
- ✅ 日志显示：`成功提取 11021 条翻译（Defs扫描）`

#### Step 2: 翻译内容

```bash
# 使用你喜欢的翻译工具翻译 CSV
# - Google Sheets (推荐，支持批量翻译)
# - ChatGPT / 其他 AI (快速但费用较高)
# - 专业翻译人员 (质量最佳)
```

CSV 列说明：
| 列 | 含义 | 示例 |
|----|------|------|
| A | 翻译键 | `Covering_Observed_Interaction.label` |
| B | 英文文本 | `observed Covering` |
| C | 标签类型 | `label` 或 `li` |
| D | 相对路径 | `LogEntryDefs\NMMFixationObservedInteractionDefs.xml` |
| E | 汉化文本 | **需要你来填写** |

#### Step 3: 导入翻译

```bash
python main.py
# 选择 "4 - 导入翻译模板"
```

配置导入：
- **源 CSV 文件**: 你翻译后的 CSV 文件
- **输出目录**: 生成的 DefInjected 目录位置
- **目标语言**: `ChineseSimplified`

**验证结果**：
```
输出目录结构应该是：
output_dir/
├── Languages/
│   └── ChineseSimplified/
│       └── DefInjected/
│           ├── InteractionDef/
│           │   ├── Covering_Observed_Interaction.xml
│           │   ├── NMMFixationObservedInteractionDefs.xml
│           │   └── ...
│           └── Def/
│               └── ...
```

### 方式 3: 命令行脚本 (高级用户)

对于自动化工作流，可以直接调用 Python API：

```python
from extract.workflow.manager import TemplateManager
from user_config import UserConfigManager

# 初始化
manager = TemplateManager()
config = UserConfigManager()

# 提取翻译
keyed_data, def_data = manager.extract_all_translations(
    import_dir=r"c:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\nudity-matters-more-opinions",
    import_language="English"
)

print(f"✅ 提取完成：{len(keyed_data)} Keyed + {len(def_data)} Def 翻译")

# 生成 DefInjected 文件
manager.export_as_definjected(
    keyed_translations=keyed_data,
    def_translations=def_data,
    output_dir="./output",
    output_language="ChineseSimplified"
)
```

---

## 📊 翻译任务规模

根据测试，nudity-matters-more-opinions mod 的翻译任务规模：

| 指标 | 数量 | 备注 |
|------|------|------|
| **总翻译项** | 11,021 | 需要汉化 |
| **Def 定义** | 9,223 | mod 定义的规则 |
| **标签文本** | 5,342 | 界面显示文本 |
| **规则文本** | 5,679 | 动态生成的对话 |
| **XML 文件** | 426 | 文件数量 |

**工作量估计**：
- 自动翻译（Google/ChatGPT）: **30 分钟**
- 手动翻译: **8-12 小时**（取决于质量要求）
- 人工审核和调整: **2-4 小时**

---

## ⚠️ 注意事项

### 关于 rulesStrings 的翻译

当你看到像这样的翻译项时：
```
Key: Covering_Observed_Interaction.logRulesInitiator.rulesStrings.0
Text: r_logentry->I [saw] [RECIPIENT_nameDef] was [staring] with an [emotion] look at my attempts to cover my [nudity].
```

**重要提示**：
- ❗ **不要翻译方括号内的内容** - 如 `[saw]`、`[RECIPIENT_nameDef]` 等
- ❗ 这些是游戏内的变量占位符，翻译会破坏功能
- ✅ 只翻译括号外的普通英文文本

**正确翻译示例**：
```
原文: r_logentry->I [saw] [RECIPIENT_nameDef] was [staring] with an [emotion] look
翻译: r_logentry->我看到[RECIPIENT_nameDef]用一种[emotion]的眼神看我
```

### 关于自定义字段

如果你发现有需要翻译但没有被提取的字段，可以：

1. **编辑翻译字段配置**
   ```bash
   编辑 user_config/config/translation_fields.yaml
   在 rimworld_specific 部分添加新字段
   ```

2. **重新提取**
   ```bash
   重新运行提取流程
   ```

---

## 🔧 故障排除

### 问题 1: "未找到 Defs 目录"

**原因**: mod 路径不正确

**解决方案**:
```bash
# 确保目录存在
cd "c:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\nudity-matters-more-opinions"
ls Common\Defs\

# 如果看到 XML 文件，说明路径是正确的
```

### 问题 2: 提取的翻译项少于预期

**原因**: 部分字段被过滤器排除

**解决方案**:
- 检查 `user_config/config/translation_fields.yaml`
- 查看日志文件 `logs/` 中的详细信息
- 可能需要添加缺失的字段名

### 问题 3: DefInjected 导出失败

**原因**: 输出目录权限或磁盘空间不足

**解决方案**:
```bash
# 检查输出目录权限
# 检查磁盘可用空间
# 尝试不同的输出路径
```

---

## ✅ 验证翻译是否生效

汉化完成后，验证翻译是否正确安装：

### 1. 复制汉化文件

```bash
# 将输出的 Languages 文件夹复制到 mod 目录
cp -r output/Languages nudity-matters-more-opinions/
```

### 2. 在游戏中验证

```bash
# 在 RimWorld 启动器中：
1. 启用 nudity-matters-more-opinions mod
2. 在 Mods 列表中看到 mod 标题和描述是否显示为中文
3. 在游戏中查看相关信息

# 检查点：
- ✅ Mod 加载提示
- ✅ 选项菜单文本
- ✅ 游戏日志信息
- ✅ 对话气泡内容 (如有)
```

---

## 💡 推荐工作流程

```
1. 使用 Day_zh 完整管道 (最简单)
         ↓
2. 导出 CSV 并预览第一批数据
         ↓
3. 使用 ChatGPT/Google Translate 翻译
         ↓
4. 导入翻译并生成 DefInjected
         ↓
5. 复制到 mod 目录
         ↓
6. 在游戏中测试
         ↓
7. 根据反馈调整（如需要）
```

---

## 📞 需要帮助？

- 📄 查看详细的分析报告: `ANALYSIS_MOD_DEFS_LIMITATION.md`
- 📄 查看实施总结: `EXTENSION_IMPLEMENTATION_SUMMARY.md`
- 🧪 运行测试脚本: `python test_defs_extension.py`
- 📝 查看 Day_zh 日志: `logs/` 目录

祝翻译顺利! 🚀
