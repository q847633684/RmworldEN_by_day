# Day_汉化

RimWorld 模组翻译工具，支持 DefInjected 和 Keyed 数据提取、自动/手动翻译、导入、语料集生成等功能。

## 概述

Day_汉化是一个专门为 RimWorld 模组设计的翻译工具链，提供了完整的翻译流程：从原始英文模组文件中提取可翻译文本，生成标准格式的翻译文件，支持机器翻译辅助，最终生成符合 RimWorld 模组标准的中文翻译文件。

## 特性

- 🔧 支持 DefInjected 和 Keyed 两种 RimWorld 翻译模式
- 📝 自动提取可翻译文本，支持复杂嵌套结构
- 🤖 集成机器翻译API（DeepL、Google Translate等）
- 📊 生成双语语料集，支持翻译复用
- 🎯 智能字段过滤，避免翻译不必要的内容
- 📄 自动生成标准模板文件
- 🔍 详细的日志记录和错误处理
- 📈 批量处理多个模组

## 安装

### 环境要求
- Python 3.7+
- lxml 库（用于 XML 处理）
- requests 库（用于 API 调用）

### 安装步骤

```bash
# 克隆项目
git clone <项目地址>
cd Day_汉化

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 基本使用

```bash
# 运行翻译工具
python run_day_translation.py

# 运行原版提取工具
python run_day_en.py
```

### 配置文件

在 `day_translation/utils/config.py` 中配置基本设置：

```python
# 源模组路径
SOURCE_MOD_PATH = "path/to/your/mod"

# 输出路径
OUTPUT_PATH = "path/to/output"

# 机器翻译API配置
DEEPL_API_KEY = "your_deepl_api_key"
GOOGLE_API_KEY = "your_google_api_key"

# 语言设置
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "zh"
```

## 项目架构

```
Day_汉化/
├── day_translation/           # 主翻译工具包
│   ├── core/                 # 核心功能模块
│   │   ├── extractors.py     # 文本提取器
│   │   ├── generators.py     # 翻译生成器
│   │   ├── importers.py      # 翻译导入器
│   │   ├── exporters.py      # 文件导出器
│   │   ├── template_manager.py # 模板管理器
│   │   └── main.py           # 主控制器
│   └── utils/                # 工具模块
│       ├── config.py         # 配置管理
│       ├── filters.py        # 内容过滤器
│       ├── machine_translate.py # 机器翻译
│       ├── parallel_corpus.py # 语料集处理
│       ├── path_manager.py   # 路径管理
│       └── batch_processor.py # 批量处理
├── Day_EN/                   # 原版英文提取工具
├── 提取的翻译/               # 提取结果存储
├── mod/                      # 模组文件
└── docs/                     # 文档
```

## 核心功能模块

### 1. 文本提取器 (extractors.py)

负责从 RimWorld 模组文件中提取可翻译文本：

```python
from day_translation.core.extractors import DefInjectedExtractor, KeyedExtractor

# DefInjected 提取
def_extractor = DefInjectedExtractor()
def_texts = def_extractor.extract_from_directory("path/to/Defs")

# Keyed 提取
keyed_extractor = KeyedExtractor()
keyed_texts = keyed_extractor.extract_from_directory("path/to/Languages/English/Keyed")
```

#### 主要方法：
- `extract_from_directory(directory_path)`: 从目录提取文本
- `extract_from_file(file_path)`: 从单个文件提取文本
- `extract_translatable_text(element, path)`: 提取可翻译文本

### 2. 翻译生成器 (generators.py)

生成翻译文件和处理翻译逻辑：

```python
from day_translation.core.generators import TranslationGenerator

generator = TranslationGenerator()
generator.generate_def_injected_files(extracted_texts, output_path)
generator.generate_keyed_files(extracted_texts, output_path)
```

#### 主要方法：
- `generate_def_injected_files(texts, output_path)`: 生成 DefInjected 翻译文件
- `generate_keyed_files(texts, output_path)`: 生成 Keyed 翻译文件
- `apply_machine_translation(texts, api_key)`: 应用机器翻译

### 3. 模板管理器 (template_manager.py)

管理翻译模板和文件结构：

```python
from day_translation.core.template_manager import TemplateManager

template_manager = TemplateManager()
template_manager.create_language_template("ChineseSimplified")
template_manager.copy_template_structure(source_path, target_path)
```

#### 主要方法：
- `create_language_template(language_code)`: 创建语言模板
- `copy_template_structure(source, target)`: 复制模板结构
- `validate_template_structure(path)`: 验证模板结构

### 4. 内容过滤器 (filters.py)

过滤不需要翻译的内容：

```python
from day_translation.utils.filters import filter_content

# 过滤配置
filter_config = {
    'exclude_fields': ['defName', 'id', 'fileName'],
    'exclude_patterns': [r'^\d+$', r'^[A-Z_]+$'],
    'min_length': 2
}

filtered_texts = filter_content(extracted_texts, filter_config)
```

#### 主要方法：
- `filter_content(texts, config)`: 根据配置过滤内容
- `should_translate_field(field_name, text)`: 判断字段是否需要翻译
- `extract_field_name(xpath)`: 从 xpath 提取字段名

### 5. 机器翻译 (machine_translate.py)

集成多种机器翻译服务：

```python
from day_translation.utils.machine_translate import MachineTranslator

translator = MachineTranslator()
translator.configure_deepl(api_key="your_key")
translator.configure_google(api_key="your_key")

# 翻译文本
translated = translator.translate_text("Hello world", source="en", target="zh")
```

#### 支持的翻译服务：
- DeepL API
- Google Translate API
- Microsoft Translator API
- 自定义API接口

### 6. 语料集处理 (parallel_corpus.py)

处理双语语料集：

```python
from day_translation.utils.parallel_corpus import ParallelCorpus

corpus = ParallelCorpus()
corpus.load_from_csv("translations.csv")
corpus.add_translation_pair("Hello", "你好")
corpus.export_to_tmx("output.tmx")
```

## 配置说明

### 基本配置 (config.py)

```python
# 路径配置
SOURCE_MOD_PATH = "path/to/source/mod"
OUTPUT_PATH = "path/to/output"
TEMPLATE_PATH = "templates"

# 语言配置
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "zh"
LANGUAGE_CODE = "ChineseSimplified"

# 过滤配置
EXCLUDE_FIELDS = [
    'defName', 'id', 'fileName', 'name',
    'uiIconPath', 'iconPath', 'texPath'
]

EXCLUDE_PATTERNS = [
    r'^\d+$',           # 纯数字
    r'^[A-Z_]+$',       # 纯大写字母和下划线
    r'^[a-z]+\d+$',     # 小写字母+数字
]

# API配置
DEEPL_API_KEY = ""
GOOGLE_API_KEY = ""
MICROSOFT_API_KEY = ""

# 日志配置
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_FILE_PATH = "logs"
```

### 过滤配置 (filter_config.py)

```python
# 字段过滤规则
FIELD_FILTERS = {
    # 完全排除的字段
    'exclude_exact': [
        'defName', 'id', 'fileName', 'name',
        'uiIconPath', 'iconPath', 'texPath', 'soundPath'
    ],
    
    # 模式排除
    'exclude_patterns': [
        r'^\d+$',           # 纯数字
        r'^[A-Z_]+$',       # 纯大写常量
        r'^\w+\.(png|jpg|xml)$'  # 文件名
    ],
    
    # 最小长度要求
    'min_length': 2,
    
    # 最大长度限制
    'max_length': 1000
}
```

## 日志系统

### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（仅写入文件）
- **WARNING**: 警告信息（控制台+文件）
- **ERROR**: 错误信息（控制台+文件）

### 日志文件
- 位置: `logs/day_translation_YYYYMMDD_HHMMSS.log`
- 自动创建带时间戳的日志文件
- 历史日志自动保留

### 配置日志

```python
import logging
from day_translation.utils.config import setup_logging

# 设置日志
setup_logging(
    level=logging.INFO,
    log_to_file=True,
    log_file_path="logs"
)
```

## 使用示例

### 完整翻译流程

```python
from day_translation.core.main import DayTranslationMain

# 初始化
translator = DayTranslationMain()

# 配置
translator.configure({
    'source_path': 'path/to/mod',
    'output_path': 'path/to/output',
    'language': 'ChineseSimplified',
    'use_machine_translation': True,
    'deepl_api_key': 'your_key'
})

# 执行翻译
translator.extract_and_translate()
```

### 自定义提取

```python
from day_translation.core.extractors import DefInjectedExtractor
from day_translation.utils.filters import filter_content

# 自定义提取器
extractor = DefInjectedExtractor()
extractor.set_custom_fields(['label', 'description', 'jobString'])

# 提取文本
texts = extractor.extract_from_directory("Defs")

# 自定义过滤
filter_config = {
    'exclude_fields': ['defName', 'id'],
    'min_length': 3
}
filtered_texts = filter_content(texts, filter_config)
```

### 批量处理

```python
from day_translation.utils.batch_processor import BatchProcessor

# 批量处理多个模组
processor = BatchProcessor()
processor.add_mod("path/to/mod1")
processor.add_mod("path/to/mod2")
processor.add_mod("path/to/mod3")

# 执行批量翻译
processor.process_all()
```

## 常见问题

### Q: 提取的文本中包含不需要翻译的内容怎么办？
A: 在 `filter_config.py` 中配置过滤规则，或者在提取时使用自定义过滤器。

### Q: 机器翻译质量不好怎么办？
A: 可以：
1. 使用多个翻译服务对比
2. 建立术语库
3. 手动调整翻译结果
4. 使用语料集改善翻译质量

### Q: 如何处理特殊格式的文本？
A: 在 `extractors.py` 中自定义提取逻辑，或者使用预处理和后处理函数。

### Q: 翻译结果如何导入游戏？
A: 使用 `importers.py` 中的导入功能，或者手动复制生成的文件到模组目录。

## 开发指南

### 代码规范

1. **日志规范**:
   - 使用 `logging` 模块，不使用 `print` 进行调试
   - 错误信息使用 `logging.error()`
   - 调试信息使用 `logging.debug()`
   - 用户交互保留 `print`

2. **异常处理**:
   ```python
   try:
       # 操作代码
   except Exception as e:
       logging.error(f"操作失败: {e}")
       raise
   ```

3. **文件操作**:
   ```python
   import os
   from pathlib import Path
   
   # 使用 Path 对象
   file_path = Path("path/to/file")
   if file_path.exists():
       # 处理文件
   ```

### 扩展功能

1. **添加新的提取器**:
   ```python
   from day_translation.core.extractors import BaseExtractor
   
   class CustomExtractor(BaseExtractor):
       def extract_from_file(self, file_path):
           # 自定义提取逻辑
           pass
   ```

2. **添加新的翻译服务**:
   ```python
   from day_translation.utils.machine_translate import BaseTranslator
   
   class CustomTranslator(BaseTranslator):
       def translate(self, text, source, target):
           # 自定义翻译逻辑
           pass
   ```

### 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
python -m pytest tests/integration/

# 运行性能测试
python -m pytest tests/performance/
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持 DefInjected 和 Keyed 提取
- 集成机器翻译
- 完善的日志系统

## 支持

如有问题或建议，请：
1. 查看文档和常见问题
2. 检查日志文件
3. 创建 Issue
4. 联系开发者
