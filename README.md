# Day Translation Core 模块架构文档

## 📋 概述

`day_translation` 工具是一个专为 RimWorld 模组设计的翻译工具包，采用模块化架构，包含翻译数据的提取、处理、生成、导出和导入功能。该工具支持多种翻译工作流程，提供智能合并、模板生成等高级功能。

## ✨ 最新功能

### 🎯 统一进度条系统
- 所有提取和导出操作都配备实时进度条
- 清晰的进度百分比和文件数量显示
- 统一的用户体验和界面风格

### 🔧 代码质量优化
- 统一的导入管理，避免重复导入
- 优化的错误处理和参数解包
- 更清晰的代码结构和维护性

### 📊 智能提取流程
- 自动检测输入目录结构
- 支持Keyed、DefInjected、Defs多种提取模式
- 智能组合提取和导出选项

## 🏗️ 项目架构

```
day_translation/
├── main.py                      # 主入口
├── core/                        # 核心业务逻辑层
│   ├── translation_facade.py    # 翻译门面 - 统一接口
│   ├── exceptions.py            # 异常定义
│   ├── API_CALLS.md             # API接口文档
│   └── QUICK_REFERENCE.md       # 快速参考
├── extract/                     # 提取模块
│   ├── core/                    # 核心提取组件
│   │   ├── extractors/          # 提取器
│   │   │   ├── base.py          # 基础提取器
│   │   │   ├── keyed.py         # Keyed提取器
│   │   │   ├── definjected.py   # DefInjected提取器
│   │   │   └── defs.py          # Defs扫描器
│   │   ├── exporters/           # 导出器
│   │   │   ├── base.py          # 基础导出器
│   │   │   ├── keyed.py         # Keyed导出器
│   │   │   └── definjected.py   # DefInjected导出器
│   │   └── filters/             # 内容过滤器
│   │       ├── content_filter.py    # 内容过滤器
│   │       └── text_validator.py    # 文本验证器
│   ├── workflow/                # 工作流程管理
│   │   ├── manager.py           # 模板管理器 - 核心控制器
│   │   ├── handler.py           # 处理器 - 主要业务流程
│   │   └── interaction.py       # 交互管理器
│   ├── utils/                   # 提取工具
│   │   └── merger.py            # 智能合并器
│   └── docs/                    # 文档
│       └── merge_flow.md        # 合并流程文档
├── import_template/             # 导入模块
│   ├── importers.py             # 导入器 - CSV到XML转换
│   └── handler.py               # 导入处理器
├── translate/                   # 翻译模块
│   ├── core/                    # 翻译核心
│   │   ├── unified_translator.py    # 统一翻译器
│   │   ├── translator_factory.py   # 翻译器工厂
│   │   ├── translation_config.py   # 翻译配置
│   │   ├── java_translator.py      # Java翻译器
│   │   └── python_translator.py    # Python翻译器
│   ├── handler.py               # 翻译处理器
│   └── MIGRATION_GUIDE.md       # 迁移指南
├── batch/                       # 批量处理模块
│   ├── batch_processor.py       # 批量处理器
│   └── handler.py               # 批量处理处理器
├── full_pipeline/               # 完整流程模块
│   └── handler.py               # 完整流程处理器
├── corpus/                      # 语料库模块
│   ├── parallel_corpus.py       # 平行语料库
│   └── handler.py               # 语料库处理器
├── config_manage/               # 配置管理模块
│   └── handler.py               # 配置管理处理器
├── java_translate/              # Java翻译模块
│   └── RimWorldBatchTranslate/  # Java批量翻译工具
├── utils/                       # 工具模块
│   ├── config.py                # 配置管理
│   ├── utils.py                 # 工具函数和XMLProcessor
│   ├── ui_style.py              # UI样式和进度条
│   ├── interaction.py           # 交互工具
│   ├── logging_config.py        # 日志配置
│   └── path_manager.py          # 路径管理
├── logs/                        # 日志目录
├── requirements.txt             # 依赖包
├── pyproject.toml              # 项目配置
└── 文档文件/
    ├── PROGRESS_BAR_GUIDE.md    # 进度条功能指南
    ├── EXTRACTION_GUIDE.md      # 翻译提取指南
    └── UI_IMPROVEMENTS.md       # UI改进记录
```

## 📊 核心模块详解

### 1. extract/workflow/manager.py - 模板管理器

**职责**: 翻译模板的完整生命周期管理，协调各个组件完成复杂的翻译提取和生成流程

**主要功能**:
- `extract_all_translations()`: 智能提取所有翻译数据
- `_generate_templates_to_output_dir_with_structure()`: 生成模板到输出目录
- `_save_translations_to_csv()`: 保存翻译数据到CSV
- `_generate_definjected_with_structure()`: 根据结构生成DefInjected模板

**智能流程决策**:
- 自动检测输入目录结构
- 支持Keyed、DefInjected、Defs多种提取模式
- 智能组合提取和导出选项

### 2. extract/core/extractors/ - 提取器模块

**KeyedExtractor**: 从Keyed目录提取键值对翻译
- 支持自定义标签名
- 不限制default_fields
- 配备进度条显示

**DefInjectedExtractor**: 从DefInjected目录提取翻译结构
- 支持复杂的翻译结构
- 包含DefType信息
- 配备进度条显示

**DefsScanner**: 从Defs目录重新提取翻译
- 直接从游戏Defs文件提取
- 支持所有DefType
- 配备进度条显示

### 3. extract/core/exporters/ - 导出器模块

**KeyedExporter**: 导出Keyed格式的翻译文件
- 生成Keyed模板
- 配备进度条显示

**DefInjectedExporter**: 导出DefInjected格式的翻译文件
- `export_with_original_structure()`: 按原始文件路径结构导出
- `export_with_defs_structure()`: 按DefType分类导出
- `export_with_file_structure()`: 按文件目录结构导出
- 所有方法都配备进度条显示

### 4. utils/ui_style.py - UI样式和进度条

**统一进度条系统**:
- `ui.iter_with_progress()`: 带进度条的迭代器
- `ui.ProgressBar`: 进度条上下文管理器
- `ui.print_progress_bar()`: 手动进度条显示

**特性**:
- 自动显示进度百分比和文件数量
- 支持自定义前缀和描述信息
- 统一的用户体验和界面风格

## 🔄 主要工作流程

### 流程1: 智能提取和模板生成

```python
# 用户操作: 模式1 - 生成模板和CSV
main() 
└── TranslationFacade.extract_templates_and_generate_csv()
    └── TemplateManager.extract_all_translations()
        ├── KeyedExtractor.extract()           # 提取Keyed翻译
        ├── DefInjectedExtractor.extract()     # 提取DefInjected翻译
        └── DefsScanner.extract()              # 扫描Defs文件
        └── TemplateManager._generate_templates_to_output_dir_with_structure()
            ├── KeyedExporter.export_keyed_template()      # 生成Keyed模板
            └── DefInjectedExporter.export_*()             # 生成DefInjected模板
        └── TemplateManager._save_translations_to_csv()    # 导出CSV
```

### 流程2: 翻译导入

```python
# 用户操作: 模式3 - 导入翻译
main()
└── TranslationFacade.import_translations_to_templates()
    └── TemplateManager.import_translations()
        ├── _validate_csv_file()           # 验证CSV文件
        ├── _load_translations_from_csv()  # 加载翻译数据
        ├── _update_all_xml_files()        # 更新XML文件
        └── _verify_import_results()       # 验证导入结果
```

### 流程3: 完整翻译流程

```python
# 用户操作: 模式7 - 完整流程
main()
└── FullPipelineHandler.handle_full_pipeline()
    ├── 提取翻译数据
    ├── 生成翻译模板
    ├── 导出CSV文件
    ├── 机器翻译
    └── 导入翻译结果
```

## 🎯 进度条系统

### 覆盖范围
- ✅ **所有提取器**: Keyed、DefInjected、Defs
- ✅ **所有导出器**: Keyed、DefInjected (所有导出方法)
- ✅ **CSV导出**: 翻译数据导出
- ✅ **文件处理**: 批量文件操作

### 显示效果
```
ℹ️ 正在扫描 Keyed 目录中的 2 个文件...
扫描Keyed: [████████████████████████████████████████] 100.0% (2/2) ℹ️ 
✅ 从Keyed 目录提取到 52 条 Keyed 翻译

ℹ️ 正在生成 DefInjected 模板中的 25 个文件...
生成DefInjected: [████████████████████████████████████████] 100.0% (25/25) ℹ️ 
✅ DefInjected 模板已生成（按文件结构）
```

## 🛠️ 技术特性

### 智能内容过滤
- **非文本过滤**: 自动过滤数字、布尔值等非文本内容
- **忽略字段**: 可配置忽略特定字段
- **默认字段检查**: DefInjected模式检查默认字段

### 错误处理
- **目录检查**: 自动检查并提示目录存在性
- **文件格式验证**: 跳过无效文件并提供详细错误信息
- **权限处理**: 提供详细的权限错误信息

### 性能优化
- **进度条优化**: 不影响处理性能
- **内存管理**: 优化的内存使用
- **批量处理**: 支持大量文件的高效处理

## 📚 相关文档

- [进度条功能指南](PROGRESS_BAR_GUIDE.md) - 详细的进度条使用说明
- [翻译提取指南](EXTRACTION_GUIDE.md) - 提取功能完整指南
- [UI改进记录](UI_IMPROVEMENTS.md) - UI/UX改进历程
- [快速参考](core/QUICK_REFERENCE.md) - 核心功能快速参考
- [API调用](core/API_CALLS.md) - API接口文档
- [迁移指南](translate/MIGRATION_GUIDE.md) - 版本迁移说明

## 🚀 快速开始

1. **安装依赖**: `pip install -r requirements.txt`
2. **运行主程序**: `python main.py`
3. **选择模式**: 根据需求选择相应的处理模式
4. **查看进度**: 所有操作都配备实时进度条显示

Day Translation Core 模块采用了清晰的分层架构和模块化设计，通过合理的职责分离和接口设计，实现了高内聚、低耦合的代码结构。这种设计不仅便于维护和扩展，还为用户提供了灵活、强大的翻译处理能力。