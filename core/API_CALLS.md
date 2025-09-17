# Core 模块 API 调用关系详细分析

## 📋 模块导入依赖图

```
main.py
├── 导入 TranslationError, ConfigError, ImportError, ExportError (自定义异常)
├── 导入 TemplateManager (从 template_manager.py)
├── 导入 translate_csv (从 utils.machine_translate)
├── 导入 generate_parallel_corpus (从 utils.parallel_corpus)
├── 导入 BatchProcessor (从 utils.batch_processor)
└── 导入各种工具模块 (config, utils, path_manager 等)

template_manager.py
├── 导入 TemplateGenerator (从 generators.py)
├── 导入 extract_keyed_translations, scan_defs_sync, extract_definjected_translations (从 extractors.py)
├── 导入 handle_extract_translate, export_definjected_with_* (从 exporters.py)
├── 导入 XMLProcessor (从 utils.utils)
└── 导入配置和工具模块

generators.py
├── 导入 XMLProcessor (从 utils.utils)
├── 导入 save_json, sanitize_xml (从 utils.utils)
└── 导入配置模块

extractors.py
├── 导入 XMLProcessor (从 utils.utils)
├── 导入 ContentFilter (从 utils.filters)
├── 导入 get_language_folder_path (从 utils.utils)
└── 导入配置模块

exporters.py
├── 导入 XMLProcessor (从 utils.utils)
├── 导入 save_xml_to_file, sanitize_xcomment, get_language_folder_path (从 utils.utils)
└── 导入配置和多进程模块

importers.py
├── 导入 XMLProcessor (从 utils.utils)
├── 导入 get_language_folder_path (从 utils.utils)
└── 导入配置模块
```

## 🔄 详细调用链路分析

### 1. 程序启动流程

```python
run_day_translation.py
└── main()  # from day_translation.core.main
    ├── 初始化配置和用户界面
    ├── 获取用户输入（模组目录、操作模式等）
    ├── 创建 TranslationFacade 实例
    │   └── TranslationFacade.__init__()
    │       ├── 验证模组目录
    │       ├── 创建 TemplateManager 实例
    │       │   └── TemplateManager.__init__()
    │       │       ├── 创建 TemplateGenerator 实例
    │       │       └── 创建 XMLProcessor 实例
    │       └── 配置验证
    └── 根据模式调用相应方法
```

### 2. 模式1: 提取模板并生成CSV

```python
TranslationFacade.extract_templates_and_generate_csv()
└── TemplateManager.extract_and_generate_templates()
    ├── 步骤1: 提取翻译数据
    │   └── _extract_all_translations()
    │       ├── extract_keyed_translations()  # extractors.py
    │       │   ├── XMLProcessor.parse_xml()
    │       │   └── XMLProcessor.extract_translations()
    │       ├── _handle_definjected_extraction_choice()
    │       │   └── handle_extract_translate()  # exporters.py
    │       │       ├── export_keyed()
    │       │       ├── export_definjected_from_english()
    │       │       └── cleanup_backstories_dir()
    │       └── scan_defs_sync() 或 extract_definjected_translations()  # extractors.py
    │           ├── XMLProcessor.parse_xml()
    │           ├── ContentFilter.should_include()
    │           └── _extract_translatable_fields_recursive()
    ├── 步骤2: 生成模板文件
    │   ├── _generate_all_templates() 或 _generate_templates_to_output_dir()
    │   │   ├── 分离 Keyed 和 DefInjected 翻译
    │   │   ├── 生成 Keyed 模板
    │   │   │   ├── TemplateGenerator.generate_keyed_template()  # generators.py
    │   │   │   │   ├── XMLProcessor.parse_xml()
    │   │   │   │   ├── _create_keyed_xml_from_source()
    │   │   │   │   └── XMLProcessor.save_xml()
    │   │   │   └── TemplateGenerator.generate_keyed_template_from_data()
    │   │   │       ├── _create_keyed_xml_from_data()
    │   │   │       └── XMLProcessor.save_xml()
    │   │   └── 生成 DefInjected 模板
    │   │       └── _handle_definjected_structure_choice()
    │   │           ├── 选择1: export_definjected_with_original_structure()  # exporters.py
    │   │           ├── 选择2: export_definjected_with_defs_structure()       # exporters.py
    │   │           └── 选择3: TemplateGenerator.generate_definjected_template()  # generators.py
    │   │               ├── _group_defs_by_type()
    │   │               ├── _create_definjected_xml_from_data()
    │   │               └── XMLProcessor.save_xml()
    └── 步骤3: 保存CSV文件
        └── _save_translations_to_csv()
```

### 3. 模式2: 机器翻译

```python
TranslationFacade.machine_translate()
└── translate_csv()  # from utils.machine_translate
    ├── 读取源CSV文件
    ├── 调用翻译API（阿里云翻译等）
    └── 保存翻译后的CSV
```

### 4. 模式3: 导入翻译到模板

```python
TranslationFacade.import_translations_to_templates()
└── TemplateManager.import_translations()
    ├── 步骤1: 验证CSV文件
    │   └── _validate_csv_file()
    ├── 步骤2: 加载翻译数据
    │   └── _load_translations_from_csv()
    ├── 步骤3: 更新XML文件
    │   └── _update_all_xml_files()
    │       └── 对每个XML文件:
    │           ├── XMLProcessor.parse_xml()
    │           ├── XMLProcessor.update_translations()
    │           └── XMLProcessor.save_xml()
    ├── 步骤4: 验证导入结果
    │   └── _verify_import_results()
    └── 可选: 自动创建模板
        └── ensure_templates_exist()
```

### 5. DefInjected 导出详细流程

```python
export_definjected()  # exporters.py 核心函数
├── 参数处理和验证
├── 创建输出目录结构
├── 多进程处理Def文件
│   └── process_def_file_wrapper()
│       └── process_def_file()
│           ├── XMLProcessor.parse_xml()
│           ├── 根据翻译数据筛选相关条目
│           ├── 创建DefInjected XML结构
│           ├── 添加翻译条目和注释
│           └── 返回XML内容
├── 收集所有处理结果
└── 保存XML文件
    └── save_xml_to_file()  # utils.utils
        ├── sanitize_xml()
        └── 格式化输出XML
```

### 6. 按原Defs结构导出流程

```python
export_definjected_with_defs_structure()  # exporters.py
├── 扫描源Defs目录结构
├── 按原始目录结构分组翻译数据
├── 为每个目录创建对应的DefInjected文件
│   └── 调用 export_definjected() 生成具体文件
└── 保持与原Defs目录相同的层次结构
```

### 7. 按原英文DefInjected结构导出流程

```python
export_definjected_with_original_structure()  # exporters.py
├── 扫描英文DefInjected目录
├── 复制英文目录结构
├── 为每个英文DefInjected文件创建对应的中文文件
│   ├── 解析英文文件获取defName列表
│   ├── 从翻译数据中筛选匹配的条目
│   └── 生成对应的中文DefInjected文件
└── 保持与英文DefInjected完全相同的文件结构
```

## 🔧 关键接口和数据流

### 翻译数据格式

```python
# 标准翻译数据格式: Tuple[str, str, str, str]
TranslationData = (key, text, tag, file)
# 示例:
# ("ThingDef/Apparel_Pants.label", "裤子", "label", "Apparel.xml")
```

### XMLProcessor 核心接口

```python
XMLProcessor
├── parse_xml(file_path) -> Optional[ElementTree]
├── save_xml(tree, file_path, pretty_print=True) -> bool
├── extract_translations(tree, context="") -> List[TranslationData]
├── update_translations(tree, translations, merge=True) -> bool
└── validate_against_schema(tree, schema_path) -> bool
```

### TemplateManager 主要接口

```python
TemplateManager
├── extract_and_generate_templates() -> List[TranslationData]
├── import_translations(csv_path, merge=True) -> bool
├── ensure_templates_exist() -> bool
└── 私有方法 (_extract_all_translations, _generate_all_templates 等)
```

### TemplateGenerator 核心接口

```python
TemplateGenerator
├── generate_keyed_template(en_keyed_dir)
├── generate_keyed_template_from_data(keyed_translations)
├── generate_definjected_template(defs_translations)
└── 私有方法 (_create_*_xml_from_*, _group_* 等)
```

## 🌊 数据流向图

```
[用户输入] 
    ↓
[main.py 处理用户交互]
    ↓
[TranslationFacade 外观接口]
    ↓
[TemplateManager 核心控制器]
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│  extractors.py  │  generators.py  │  exporters.py   │
│  (数据提取)     │  (模板生成)     │  (格式导出)     │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
[XMLProcessor 统一XML处理]
    ↓
[文件系统输出]
    ↓
[CSV/XML 模板文件]
```

## 📚 关键设计决策

### 1. 为什么使用 TemplateManager 作为中心控制器？

- **职责集中**: 所有模板相关操作都通过统一入口
- **流程控制**: 确保操作按正确顺序执行
- **状态管理**: 维护模板生成过程中的状态信息
- **错误处理**: 统一的错误处理和回滚机制

### 2. 为什么分离 extractors, generators, exporters？

- **单一职责**: 每个模块专注特定功能
- **可测试性**: 独立模块易于单元测试
- **可扩展性**: 新功能可以独立添加
- **可重用性**: 模块可以在不同场景下重用

### 3. 为什么使用 XMLProcessor 统一XML处理？

- **一致性**: 确保所有XML操作使用相同标准
- **可配置性**: 支持不同的XML处理策略（lxml vs ElementTree）
- **错误处理**: 统一的XML解析错误处理
- **性能优化**: 集中式的优化和缓存策略

### 4. DefInjected 多结构支持的设计理念

- **用户选择**: 不同用户有不同的组织偏好
- **兼容性**: 支持与现有翻译项目的结构兼容
- **灵活性**: 根据模组特点选择最适合的结构
- **可扩展性**: 未来可以轻松添加新的结构方式

这种架构设计确保了代码的模块化、可维护性和扩展性，同时为用户提供了强大而灵活的翻译处理能力。
