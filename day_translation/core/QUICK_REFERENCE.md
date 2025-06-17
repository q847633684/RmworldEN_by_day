# Core 模块快速参考

## 📁 文件概览

| 文件 | 主要类/函数 | 职责 |
|------|-------------|------|
| `main.py` | `TranslationFacade`, `main()` | 用户界面、外观模式 |
| `template_manager.py` | `TemplateManager` | 核心控制器、流程管理 |
| `extractors.py` | `extract_*` 函数 | 文本提取、XML解析 |
| `generators.py` | `TemplateGenerator` | 模板生成、XML创建 |
| `exporters.py` | `export_*` 函数 | 数据导出、格式转换 |
| `importers.py` | `import_*` 函数 | 翻译导入、XML更新 |

## 🚀 核心调用路径

### 提取和生成模板
```
用户选择模式1 → TranslationFacade.extract_templates_and_generate_csv() 
→ TemplateManager.extract_and_generate_templates() 
→ extractors.py(提取) + generators.py(生成) + exporters.py(导出)
```

### 导入翻译
```
用户选择模式3 → TranslationFacade.import_translations_to_templates() 
→ TemplateManager.import_translations() 
→ importers.py(加载CSV) + XMLProcessor(更新XML)
```

### DefInjected结构选择
```
_handle_definjected_structure_choice() 
→ 用户选择 → 对应的export_*函数或generate_*方法
```

## 🔧 关键类和方法

### TranslationFacade
- `extract_templates_and_generate_csv()` - 提取模板生成CSV
- `import_translations_to_templates()` - 导入翻译到模板  
- `machine_translate()` - 机器翻译
- `generate_corpus()` - 生成语料库

### TemplateManager  
- `extract_and_generate_templates()` - 核心提取生成方法
- `import_translations()` - 核心导入方法
- `_handle_definjected_structure_choice()` - DefInjected结构选择

### TemplateGenerator
- `generate_keyed_template()` - 生成Keyed模板
- `generate_definjected_template()` - 生成DefInjected模板

## 🔄 数据流
```
模组文件 → extractors.py → [翻译数据] → generators.py → 模板文件
CSV文件 → importers.py → XMLProcessor → 更新后的模板文件
```

## 📝 扩展点

- **新提取器**: 在 `extractors.py` 添加新的 `extract_*` 函数
- **新生成器**: 在 `generators.py` 添加新的生成方法
- **新导出格式**: 在 `exporters.py` 添加新的 `export_*` 函数
- **新导入源**: 在 `importers.py` 添加新的导入函数
