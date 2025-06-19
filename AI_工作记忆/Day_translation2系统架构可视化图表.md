# Day_translation2 系统架构可视化图表

## 🏗️ 系统整体架构图

```mermaid
graph TB
    subgraph "用户交互层 (User Interface Layer)"
        A[main.py 程序入口]
        B[UnifiedInteractionManager 交互管理器]
        C[主菜单系统]
    end
    
    subgraph "业务门面层 (Facade Layer)"
        D[TranslationFacade 翻译门面]
        D1[extract_templates_and_generate_csv]
        D2[import_translations_to_templates]
        D3[batch_process_mods]
    end
    
    subgraph "核心业务层 (Core Business Layer)"
        E[TemplateManager 模板管理器]
        F[DataExtractor 数据提取器]
        G[TemplateGenerator 模板生成器]
        H[ImportManager 导入管理器]
    end
    
    subgraph "数据处理层 (Data Processing Layer)"
        I[AdvancedXMLProcessor XML处理器]
        J[AdvancedFilterRules 过滤规则]
        K[ExportManager 导出管理器]
        L[BatchProcessor 批处理器]
    end
    
    subgraph "工具支持层 (Utility Layer)"
        M[FileUtils 文件工具]
        N[PathManager 路径管理]
        O[ConfigManager 配置管理]
        P[LoggingManager 日志管理]
    end
    
    subgraph "数据模型层 (Data Model Layer)"
        Q[TranslationEntry 翻译条目]
        R[OperationResult 操作结果]
        S[ConfigModels 配置模型]
        T[ExceptionModels 异常模型]
    end
    
    A --> B
    B --> C
    C --> D
    D --> D1
    D --> D2
    D --> D3
    D1 --> E
    D2 --> H
    D3 --> L
    E --> F
    E --> G
    F --> I
    F --> J
    G --> K
    I --> M
    J --> O
    K --> M
    F --> Q
    E --> R
    I --> S
    D --> T
```

## 🔄 主要操作流程图

### 1. 系统启动和主菜单流程

```mermaid
flowchart TD
    A[🚀 程序启动] --> B[📋 加载配置文件]
    B --> C[🔧 初始化日志系统]
    C --> D[💬 创建交互管理器]
    D --> E[📖 显示主菜单]
    
    E --> F{👤 用户选择}
    
    F -->|1| G[📤 提取模式]
    F -->|2| H[📥 导入模式]
    F -->|3| I[🔄 翻译模式]
    F -->|4| J[📚 语料库模式]
    F -->|5| K[⚡ 批处理模式]
    F -->|6| L[⚙️ 配置模式]
    F -->|0| M[👋 退出程序]
    
    G --> N[handle_extraction_mode]
    H --> O[handle_import_mode]
    I --> P[handle_translation_mode]
    J --> Q[handle_corpus_mode]
    K --> R[handle_batch_mode]
    L --> S[handle_config_mode]
    
    N --> E
    O --> E
    P --> E
    Q --> E
    R --> E
    S --> E
    
    M --> T[🔚 程序结束]
```

### 2. 提取模式详细流程

```mermaid
flowchart TD
    A[📤 用户选择提取模式] --> B[📝 获取提取参数]
    B --> B1[Mod目录路径]
    B --> B2[输出目录]
    B --> B3[结构选择]
    B --> B4[合并模式]
    
    B1 --> C[🏗️ 创建TranslationFacade]
    B2 --> C
    B3 --> C
    B4 --> C
    
    C --> D[🎯 调用extract_templates_and_generate_csv]
    D --> E[📋 TemplateManager处理]
    
    E --> F[🤖 智能选择DefInjected提取模式]
    F --> F1{DefInjected文件存在?}
    F1 -->|是| F2[DefInjected模式]
    F1 -->|否| F3[扫描模式]
    
    F2 --> G[🔍 开始提取所有翻译数据]
    F3 --> G
    
    G --> H[📋 Keyed翻译提取]
    G --> I[🎯 DefInjected翻译提取]
    G --> J[🔍 Defs扫描提取]
    
    H --> K[🔗 数据合并与去重]
    I --> K
    J --> K
    
    K --> L[📄 生成翻译模板]
    L --> M[💾 导出CSV文件]
    M --> N[📊 返回操作结果]
    N --> O[✅ 显示结果给用户]
```

### 3. 数据提取核心算法流程

```mermaid
flowchart TD
    A[🎯 DataExtractor.extract_all_translations] --> B{📂 提取模式判断}
    
    B -->|Keyed模式| C[📋 extract_keyed_translations]
    B -->|DefInjected模式| D[🎯 extract_definjected_translations]
    B -->|扫描模式| E[🔍 scan_defs_sync]
    
    subgraph "Keyed提取流程"
        C --> C1[📁 遍历Keyed目录]
        C1 --> C2[📄 解析XML文件]
        C2 --> C3[🏷️ 提取key标签内容]
        C3 --> C4[🔍 应用过滤规则]
        C4 --> C5[📝 创建TranslationEntry]
    end
    
    subgraph "DefInjected提取流程"
        D --> D1[📁 遍历DefInjected目录]
        D1 --> D2[📄 解析XML文件]
        D2 --> D3[🔄 递归提取可翻译字段]
        D3 --> D4[🏷️ 字段类型匹配]
        D4 --> D5[🚫 过滤非文本内容]
        D5 --> D6[📝 创建TranslationEntry]
    end
    
    subgraph "Defs扫描流程"
        E --> E1[📁 遍历Defs目录]
        E1 --> E2[📄 解析XML文件]
        E2 --> E3[🔄 递归字段扫描]
        E3 --> E4[❓ 字段可翻译性判断]
        E4 --> E5[📝 生成翻译条目]
    end
    
    C5 --> F[🔗 合并所有结果]
    D6 --> F
    E5 --> F
    F --> G[📊 返回翻译数据列表]
```

### 4. 递归字段提取算法

```mermaid
flowchart TD
    A[🔄 _extract_translatable_fields_recursive] --> B[📄 当前XML元素]
    
    B --> C{📝 元素有文本内容?}
    C -->|是| D[🔍 检查字段是否可翻译]
    C -->|否| E[👶 处理子元素]
    
    D --> D1{✅ 通过过滤规则?}
    D1 -->|是| D2[🚫 检查是否为非文本内容]
    D1 -->|否| E
    
    D2 --> D3{📝 是有效文本?}
    D3 -->|是| D4[📝 创建TranslationEntry]
    D3 -->|否| E
    
    D4 --> F[📋 添加到结果列表]
    
    E --> E1[🔁 遍历所有子元素]
    E1 --> E2[🔄 递归调用自身]
    E2 --> E3[🔗 合并子元素结果]
    
    F --> G[📊 返回当前层级结果]
    E3 --> G
    
    G --> H{🔚 是否为根元素?}
    H -->|是| I[✅ 返回完整结果]
    H -->|否| J[⬆️ 返回上级调用]
```

### 5. 过滤规则决策树

```mermaid
flowchart TD
    A[🔍 should_translate_field] --> B[📝 输入: 字段名 + 字段值]
    
    B --> C{🏷️ 字段名在翻译列表中?}
    C -->|否| D[❌ 返回False]
    C -->|是| E{📝 字段值非空?}
    
    E -->|否| F[❌ 返回False]
    E -->|是| G[🔍 is_non_text_content检查]
    
    G --> H{🚫 是非文本内容?}
    H -->|是| I[❌ 返回False]
    H -->|否| J{📊 数字检查}
    
    J -->|是数字| K[❌ 返回False]
    J -->|否| L{📁 路径检查}
    
    L -->|是路径| M[❌ 返回False]
    L -->|否| N{🔗 URL检查}
    
    N -->|是URL| O[❌ 返回False]
    N -->|否| P{💻 代码片段检查}
    
    P -->|是代码| Q[❌ 返回False]
    P -->|否| R{🏷️ 特殊标记检查}
    
    R -->|是特殊标记| S[❌ 返回False]
    R -->|否| T[✅ 返回True]
```

## 📊 数据流向图

```mermaid
flowchart LR
    subgraph "数据源"
        A1[📁 Keyed XML文件]
        A2[📁 DefInjected XML文件]
        A3[📁 Defs XML文件]
    end
    
    subgraph "解析层"
        B1[🔧 AdvancedXMLProcessor]
        B2[🔍 递归字段扫描器]
        B3[🏷️ 标签提取器]
    end
    
    subgraph "过滤层"
        C1[🔍 AdvancedFilterRules]
        C2[🚫 非文本内容过滤]
        C3[✅ 可翻译性判断]
    end
    
    subgraph "数据模型"
        D1[📝 TranslationEntry]
        D2[📋 翻译数据列表]
        D3[📊 操作结果]
    end
    
    subgraph "输出层"
        E1[📄 XML模板文件]
        E2[📋 CSV导出文件]
        E3[📊 操作报告]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    
    B1 --> C1
    B2 --> C2
    B3 --> C3
    
    C1 --> D1
    C2 --> D1
    C3 --> D1
    
    D1 --> D2
    D2 --> D3
    
    D2 --> E1
    D2 --> E2
    D3 --> E3
```

## 🔧 核心算法伪代码

### 递归字段提取算法

```python
function extract_translatable_fields_recursive(element, path="", context=""):
    results = []
    
    // 处理当前元素文本
    if element.text and element.text.strip():
        if filter_rules.should_translate_field(element.tag, element.text):
            if not filter_rules.is_non_text_content(element.text):
                entry = create_translation_entry(element, path, context)
                results.append(entry)
    
    // 递归处理子元素
    for child in element.children:
        child_path = build_path(path, child.tag)
        child_context = build_context(context, element)
        child_results = extract_translatable_fields_recursive(
            child, child_path, child_context
        )
        results.extend(child_results)
    
    return results
```

### 智能合并算法

```python
function smart_merge_translations(existing_translations, new_translations):
    merged_results = []
    
    for new_entry in new_translations:
        existing_entry = find_existing_entry(existing_translations, new_entry.key)
        
        if existing_entry is None:
            // 新条目，直接添加
            merged_results.append(new_entry)
        else if existing_entry.is_empty() or existing_entry.is_machine_translated():
            // 现有条目为空或机器翻译，使用新条目
            merged_results.append(new_entry)
        else:
            // 保留现有的人工翻译
            merged_results.append(existing_entry)
    
    return merged_results
```

## 📈 性能特性图

```mermaid
graph TD
    A[⚡ 性能优化特性] --> B[🔄 并发处理]
    A --> C[💾 内存管理]
    A --> D[📦 缓存机制]
    A --> E[📊 进度显示]
    
    B --> B1[ThreadPoolExecutor多线程]
    B --> B2[异步文件处理]
    B --> B3[批量数据处理]
    
    C --> C1[流式处理大文件]
    C --> C2[及时释放内存]
    C --> C3[分块处理数据]
    
    D --> D1[解析结果缓存]
    D --> D2[过滤规则缓存]
    D --> D3[配置信息缓存]
    
    E --> E1[tqdm进度条]
    E --> E2[处理状态反馈]
    E --> E3[时间估算显示]
```

---

这个可视化系统架构图表完整展示了Day_translation2系统从用户交互到数据处理的完整流程，每个层次的职责都很清晰，便于理解和维护。
