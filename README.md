# Day Translation Core 模块架构文档

## 📋 概述

`day_translation` 工具是一个专为 RimWorld 模组设计的翻译工具包，采用模块化架构，包含翻译数据的提取、处理、生成、导出和导入功能。该工具支持多种翻译工作流程，提供智能合并、模板生成、占位符保护、成人内容翻译等高级功能。

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

### 🛡️ 占位符保护系统
- 智能识别和保护游戏占位符（如 `{0_labelShort}`, `{VALUE}%`, `r_logentry->` 等）
- 支持RimWorld特定的占位符模式
- 翻译后自动恢复占位符，确保游戏功能正常

### 🔞 成人内容翻译
- 内置成人内容词典翻译功能
- 支持中英文混合文本的成人词汇识别和翻译
- 可配置的成人内容过滤和翻译策略

### 🌐 多API翻译支持
- 支持阿里云、百度、腾讯、谷歌、自定义API
- 统一的翻译接口，自动选择最佳翻译方式
- Java和Python双重翻译引擎支持

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
│   │   ├── placeholders.py          # 占位符保护系统
│   │   ├── java_translator.py       # Java翻译器
│   │   ├── python_translator.py     # Python翻译器
│   │   ├── google_translator.py     # 谷歌翻译器
│   │   └── resume_base.py           # 翻译恢复基类
│   ├── unified_translator.py    # 统一翻译器
│   ├── translator_factory.py   # 翻译器工厂
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

├── user_config/                 # 用户配置系统
│   ├── core/                    # 配置核心
│   │   ├── user_config.py       # 用户配置管理器
│   │   ├── base_config.py       # 配置基类
│   │   └── config_validator.py  # 配置验证器
│   ├── api/                     # API配置
│   │   ├── api_manager.py       # API管理器
│   │   ├── aliyun_api.py        # 阿里云API
│   │   ├── baidu_api.py         # 百度API
│   │   ├── tencent_api.py       # 腾讯API
│   │   ├── google_api.py        # 谷歌API
│   │   └── custom_api.py        # 自定义API
│   ├── config/                  # 配置文件
│   │   ├── adult_dictionary.yaml    # 成人内容词典
│   │   ├── general_dictionary.yaml  # 通用词典
│   │   ├── game_dictionary.yaml     # 游戏词典
│   │   └── artist_dictionary.yaml   # 艺术家词典
│   └── ui/                      # 配置界面
│       ├── main_config_ui.py    # 主配置界面
│       └── api_config_ui.py     # API配置界面
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

### 1. translate/core/placeholders.py - 占位符保护系统

**职责**: 智能识别和保护游戏中的占位符，确保翻译后游戏功能正常

**主要功能**:
- `protect_csv_file()`: 保护CSV文件中的占位符
- `restore_csv_file()`: 恢复CSV文件中的占位符
- `_translate_remaining_adult_words()`: 翻译成人内容词汇
- `_protect_placeholders()`: 保护各种类型的占位符

**支持的占位符类型**:
- 游戏占位符: `{0_labelShort}`, `{VALUE}%`, `{RAPIST_possessive}`
- RimWorld前缀: `r_logentry->`, `sent->`, `name->`
- 通用占位符: `[xxx]`, `(PH_1)`, `(PH_2)`
- 函数调用: `pawn`, `pawn->`

### 2. user_config/ - 用户配置系统

**职责**: 提供完整的配置管理，支持多种API和自定义设置

**主要功能**:
- 多API支持: 阿里云、百度、腾讯、谷歌、自定义API
- 配置验证: 实时验证配置有效性
- 词典管理: 成人内容、通用、游戏、艺术家词典
- 用户界面: 友好的命令行配置界面

### 3. extract/workflow/manager.py - 模板管理器

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

### 4. extract/core/extractors/ - 提取器模块

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

### 5. extract/core/exporters/ - 导出器模块

**KeyedExporter**: 导出Keyed格式的翻译文件
- 生成Keyed模板
- 配备进度条显示

**DefInjectedExporter**: 导出DefInjected格式的翻译文件
- `export_with_original_structure()`: 按原始文件路径结构导出
- `export_with_defs_structure()`: 按DefType分类导出
- `export_with_file_structure()`: 按文件目录结构导出
- 所有方法都配备进度条显示

### 6. utils/ui_style.py - UI样式和进度条

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

### 流程2: 占位符保护和翻译

```python
# 用户操作: 模式2 - 统一翻译
main()
└── TranslationFacade.unified_translate()
    ├── PlaceholderManager.protect_csv_file()      # 保护占位符
    ├── UnifiedTranslator.translate_csv_file()     # 执行翻译
    └── PlaceholderManager.restore_csv_file()      # 恢复占位符
```

### 流程3: 翻译导入

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

### 流程4: 完整翻译流程

```python
# 用户操作: 模式7 - 完整流程
main()
└── FullPipelineHandler.handle_full_pipeline()
    ├── 提取翻译数据
    ├── 生成翻译模板
    ├── 导出CSV文件
    ├── 占位符保护
    ├── 机器翻译
    ├── 占位符恢复
    └── 导入翻译结果
```

### 流程5: 配置管理

```python
# 用户操作: 模式8 - 配置管理
main()
└── ConfigManageHandler.handle_config_manage()
    └── MainConfigUI.show_main_menu()
        ├── API配置管理
        ├── 路径配置管理
        ├── 词典配置管理
        └── 系统配置管理
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

### 占位符保护系统
- **智能识别**: 自动识别游戏中的各种占位符模式
- **保护机制**: 翻译前保护占位符，翻译后自动恢复
- **成人内容翻译**: 内置成人内容词典，支持中英文混合翻译
- **RimWorld特化**: 专门针对RimWorld游戏的占位符模式优化

### 多API翻译支持
- **统一接口**: 通过UnifiedTranslator提供统一的翻译接口
- **自动选择**: 根据配置自动选择最佳翻译方式
- **Java引擎**: 支持Java翻译引擎，处理复杂翻译逻辑
- **Python引擎**: 支持Python翻译引擎，提供灵活的翻译选项

### 智能内容过滤
- **非文本过滤**: 自动过滤数字、布尔值等非文本内容
- **忽略字段**: 可配置忽略特定字段
- **默认字段检查**: DefInjected模式检查默认字段

### 配置管理系统
- **多API支持**: 支持阿里云、百度、腾讯、谷歌、自定义API
- **配置验证**: 实时验证配置有效性
- **词典管理**: 支持多种词典类型和自定义词典
- **用户界面**: 友好的命令行配置界面

### 错误处理
- **目录检查**: 自动检查并提示目录存在性
- **文件格式验证**: 跳过无效文件并提供详细错误信息
- **权限处理**: 提供详细的权限错误信息
- **API错误处理**: 完善的API调用错误处理和重试机制

### 性能优化
- **进度条优化**: 不影响处理性能
- **内存管理**: 优化的内存使用
- **批量处理**: 支持大量文件的高效处理
- **翻译恢复**: 支持翻译中断后的恢复功能

## 📚 相关文档

- [进度条功能指南](PROGRESS_BAR_GUIDE.md) - 详细的进度条使用说明
- [翻译提取指南](EXTRACTION_GUIDE.md) - 提取功能完整指南
- [UI改进记录](UI_IMPROVEMENTS.md) - UI/UX改进历程
- [快速参考](core/QUICK_REFERENCE.md) - 核心功能快速参考
- [API调用](core/API_CALLS.md) - API接口文档
- [迁移指南](translate/MIGRATION_GUIDE.md) - 版本迁移说明
- [用户配置系统](user_config/README.md) - 配置管理完整指南
- [成人内容解决方案](ADULT_CONTENT_SOLUTION.md) - 成人内容翻译解决方案

## 🚀 快速开始

1. **安装依赖**: `pip install -r requirements.txt`
2. **运行主程序**: `python main.py`
3. **配置API**: 选择"配置管理"设置翻译API
4. **选择模式**: 根据需求选择相应的处理模式
5. **查看进度**: 所有操作都配备实时进度条显示

### 主要功能模式

- **模式1**: 生成模板和CSV - 提取翻译数据并生成模板
- **模式2**: 统一翻译 - 执行占位符保护和机器翻译
- **模式3**: 导入翻译 - 将翻译结果导入到模板
- **模式4**: 批量处理 - 批量处理多个模组
- **模式5**: 语料库生成 - 生成英中平行语料
- **模式6**: 完整流程 - 一键完成整个翻译流程
- **模式7**: 配置管理 - 管理API和系统配置

### 占位符保护示例

```python
# 自动保护各种占位符
原文: "The {0_labelShort} is trying to assault {1_labelShort}"
保护后: "The (PH_1) is trying to assault (PH_2)"
翻译后: "(PH_1)正在试图袭击(PH_2)"
恢复后: "The {0_labelShort}正在试图袭击{1_labelShort}"
```

### 成人内容翻译示例

```python
# 自动翻译成人内容
原文: "躺下来接受一切cum."
翻译后: "躺下来接受一切精液."
```

Day Translation Core 模块采用了清晰的分层架构和模块化设计，通过合理的职责分离和接口设计，实现了高内聚、低耦合的代码结构。这种设计不仅便于维护和扩展，还为用户提供了灵活、强大的翻译处理能力，特别是针对RimWorld模组的特殊需求进行了深度优化。