# DefInjected 智能选择逻辑详解

## 📋 整体流程图

```
用户开始提取模板
        ↓
   检查auto_choose参数
        ↓
┌──── True ────┐        ┌──── False ────┐
│  自动选择模式   │        │   智能选择模式   │
│  返回"defs"   │        │      ↓       │
└─────────────┘        │  检查输出目录   │
        ↓              │      ↓       │
   执行defs提取         │ ┌─有─┐  ┌─无─┐ │
                      │ │   │  │   │ │
                      │ ↓   │  ↓   │ │
                      │检测英文│返回│ │
                      │DefInjected│"defs"│
                      │    ↓   │     │ │
                      │ ┌─有─┐ │     │ │
                      │ │   │ │     │ │
                      │ ↓   │ │     │ │
                      │询问用户│     │ │
                      │选择方式│     │ │
                      │ ↓   │ │     │ │
               ┌选择1─┤复制英文├─选择2┐ │
               │     │DefInjected│   │ │
               ↓     │返回"definjected"│ ↓ │
        返回"definjected"└─────────┘返回"defs"
               ↓                     ↓ │
          不额外提取defs          执行defs提取
```

## 🎯 两种提取模式对比

### 模式1：definjected（基于英文DefInjected）

**特点：**
- 使用模组作者整理好的英文DefInjected文件
- 保持原有的翻译结构和组织方式
- 适合增量更新和维护现有翻译

**适用场景：**
- ✅ 模组有完整的英文DefInjected目录
- ✅ 翻译结构稳定，很少变动
- ✅ 需要与原版翻译保持兼容
- ✅ 进行翻译更新而非首次翻译

**工作流程：**
1. 检测到英文DefInjected目录存在
2. 用户选择"以英文DefInjected为基础"
3. 调用`export_definjected_from_english()`复制英文文件到输出目录
4. 在提取阶段跳过defs扫描，避免重复
5. 生成的模板与原版结构一致

### 模式2：defs（全量从Defs提取）

**特点：**
- 直接扫描模组的Defs定义文件
- 提取所有可翻译字段，确保完整性
- 生成标准化的DefInjected结构

**适用场景：**
- ✅ 模组没有英文DefInjected目录
- ✅ 英文DefInjected不完整或过时
- ✅ 首次进行模组翻译
- ✅ 模组定义有重大更新
- ✅ 需要确保100%覆盖所有可翻译内容

**工作流程：**
1. 扫描模组Defs目录下所有XML文件
2. 解析每个定义节点（如ThingDef, PawnKindDef等）
3. 提取可翻译字段（label, description, labelMale等）
4. 生成标准格式的DefInjected条目
5. 按类型组织到对应的DefInjected子目录

## 🔄 实际执行示例

### 情况1：有英文DefInjected + 用户选择基础模式

```
检测到英文 DefInjected 目录: C:\Mods\MyMod\Languages\English\DefInjected
请选择 DefInjected 处理方式：
1. 以英文 DefInjected 为基础（推荐用于已有翻译结构的情况）
2. 直接从 Defs 目录重新提取可翻译字段（推荐用于结构有变动或需全量提取时）
请输入选项编号（1/2，回车默认1）：1

✅ 将以英文 DefInjected 为基础
→ 返回 "definjected"
→ 复制英文DefInjected文件到输出目录
→ 提取时跳过defs扫描
```

### 情况2：有英文DefInjected + 用户选择全量模式

```
检测到英文 DefInjected 目录: C:\Mods\MyMod\Languages\English\DefInjected
请选择 DefInjected 处理方式：
1. 以英文 DefInjected 为基础（推荐用于已有翻译结构的情况）
2. 直接从 Defs 目录重新提取可翻译字段（推荐用于结构有变动或需全量提取时）
请输入选项编号（1/2，回车默认1）：2

✅ 将从 Defs 目录重新提取可翻译字段
→ 返回 "defs"
→ 扫描Defs目录提取所有可翻译内容
```

### 情况3：无英文DefInjected

```
未找到英文 DefInjected 目录，将从 Defs 提取可翻译字段
→ 返回 "defs"
→ 扫描Defs目录提取所有可翻译内容
```

### 情况4：自动选择模式

```
auto_choose_definjected=True
→ 返回 "defs"
→ 扫描Defs目录提取所有可翻译内容
```

## 💡 选择建议

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 首次翻译新模组 | defs | 确保完整性，不遗漏任何内容 |
| 更新现有翻译 | definjected | 保持结构一致，便于维护 |
| 模组大版本更新 | defs | 可能有新增内容，全量提取更安全 |
| 批量处理多个模组 | defs（自动） | 统一处理方式，避免交互 |
| 英文DefInjected不完整 | defs | 补全缺失的翻译项 |
| 需要自定义翻译结构 | defs | 重新组织，不受原结构限制 |
