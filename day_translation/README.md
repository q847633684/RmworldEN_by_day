# Day Translation - RimWorld 模组汉化工具

## 📖 项目简介

Day Translation 是一个专为 RimWorld 模组汉化设计的智能翻译工具。它提供了从模组中提取可翻译文本、生成翻译模板、导入翻译内容到完整的自动化翻译流程的全套解决方案。

## ✨ 核心特性

### 🎯 智能提取系统
- **DefInjected 智能选择**：自动检测模组结构，提供两种提取方式
  - 基于英文 DefInjected：保持原有翻译结构，适合结构稳定的模组
  - 从 Defs 全量提取：确保完整性，适合首次翻译或结构更新的模组
- **Keyed 文本提取**：自动提取 UI 界面文本
- **过滤系统**：智能过滤不需要翻译的内容

### 🏗️ 灵活的输出模式
- **模组内部模式**：直接生成到模组的 Languages 目录，便于开发测试
- **外部目录模式**：独立管理翻译文件，适合团队协作和版本控制

### 🤖 自动化翻译
- **机器翻译集成**：支持阿里云翻译 API
- **Java翻译工具**：提供高性能的批量翻译工具（可选）
- **平行语料生成**：为机器学习模型训练提供数据
- **批量处理**：支持多个模组的批量翻译

### 📊 数据管理
- **CSV 导出导入**：标准化的翻译数据交换格式
- **模板管理**：完善的翻译模板生成和管理系统
- **配置管理**：灵活的配置系统，支持自定义规则

## 🏛️ 项目架构

```
day_translation/
├── core/                    # 核心业务逻辑
│   ├── main.py             # 主入口和用户界面
│   ├── template_manager.py # 模板管理器（核心控制器）
│   ├── extractors.py       # 文本提取器
│   ├── generators.py       # 模板生成器
│   ├── exporters.py        # 导出器（智能选择逻辑）
│   └── importers.py        # 导入器
├── utils/                   # 工具模块
│   ├── config.py           # 配置管理
│   ├── utils.py            # 通用工具
│   ├── filters.py          # 内容过滤器
│   ├── batch_processor.py  # 批量处理器
│   ├── machine_translate.py # 机器翻译
│   ├── parallel_corpus.py  # 平行语料处理
│   ├── path_manager.py     # 路径管理器
│   └── java_translator.py  # Java翻译工具包装器
├── RimWorldBatchTranslate/ # Java翻译工具（可选）
│   ├── RimWorldBatchTranslate.java # 主程序
│   ├── pom.xml             # Maven配置
│   ├── build.bat           # Windows构建脚本
│   ├── build.sh            # Linux/Mac构建脚本
│   └── README.md           # Java工具说明
└── __init__.py
```

## 🚀 使用指南

### 安装依赖

```bash
pip install -r requirements.txt
```

### Java翻译工具（可选）

如果需要使用Java翻译工具进行高性能批量翻译：

1. **安装Java环境**
   - 确保安装了Java 8或更高版本
   - 安装Maven 3.6或更高版本

2. **构建Java工具**
   ```bash
   cd RimWorldBatchTranslate
   # Windows
   build.bat
   # Linux/Mac
   chmod +x build.sh && ./build.sh
   ```

3. **在Python中使用**
   ```python
   from day_translation.utils.java_translator import JavaTranslator
   
   translator = JavaTranslator()
   success = translator.translate_csv_interactive("input.csv", "output.csv")
   ```

### 快速开始

1. **运行主程序**
   ```bash
   python run_day_translation.py
   ```

2. **选择功能模式**
   - 模式1：提取模板 - 从模组提取翻译数据并生成模板
   - 模式2：机器翻译 - 使用 AI 翻译 CSV 文件
   - 模式3：导入模板 - 将翻译后的数据导入模组
   - 模式4：生成语料 - 创建英中平行语料
   - 模式5：完整流程 - 一键完成提取→翻译→导入
   - 模式6：批量处理 - 处理多个模组
   - 模式7：配置管理 - 管理工具配置

### 典型工作流程

#### 📋 单模组翻译流程

1. **提取阶段**
   ```
   选择模式1 → 选择输出位置 → 智能选择提取方式 → 生成模板和CSV
   ```

2. **翻译阶段**
   ```
   选择模式2 → 选择CSV文件 → 机器翻译 → 获得翻译后的CSV
   ```
   
   **或者使用Java工具**
   ```bash
   cd RimWorldBatchTranslate
   java -jar target/rimworld-batch-translate-1.0.0-jar-with-dependencies.jar
   ```

3. **导入阶段**
   ```
   选择模式3 → 选择翻译后的CSV → 导入到模组 → 完成汉化
   ```

#### 🔄 智能选择详解

当工具检测到模组包含英文 DefInjected 目录时，会提供两种选择：

**选项1：以英文 DefInjected 为基础**
- 优势：保持原有翻译结构，兼容性好
- 适用：模组已有完整的英文 DefInjected，结构稳定
- 流程：直接从英文 DefInjected 提取翻译数据

**选项2：从 Defs 目录重新提取**
- 优势：确保所有可翻译内容都被提取，不会遗漏
- 适用：首次翻译、英文 DefInjected 不完整、模组结构有更新
- 流程：扫描 Defs 目录，解析所有定义文件

## ⚙️ 配置说明

### 主要配置项

- `default_language`: 目标语言（默认：ChineseSimplified）
- `source_language`: 源语言（默认：English）
- `keyed_dir`: Keyed 目录名（默认：Keyed）
- `def_injected_dir`: DefInjected 目录名（默认：DefInjected）
- `debug_mode`: 调试模式开关

### 过滤规则

支持自定义过滤规则，可以配置：
- 字段过滤：指定需要翻译的字段类型
- 内容过滤：基于内容特征的过滤规则
- 文件过滤：指定需要处理的文件类型

## 🛠️ 高级功能

### 批量处理

支持批量处理多个模组：
```bash
# 自动处理指定目录下的所有模组
python run_day_translation.py --mode 6
```

### 机器翻译配置

支持阿里云翻译 API：
1. 配置 API 密钥
2. 选择翻译引擎
3. 设置翻译参数

### Java翻译工具特性

- **高性能**：使用阿里云定制翻译模型
- **占位符保护**：自动保护 `[xxx]` 格式的占位符
- **批量处理**：支持大量文本的批量翻译
- **QPS控制**：内置延迟机制，避免API限制

### 平行语料生成

为机器学习模型训练生成高质量的英中平行语料：
- 自动对齐英文和中文文本
- 生成标准格式的训练数据
- 支持多种输出格式

## 🐛 故障排除

### 常见问题

**Q: 提取过程卡住不动？**
A: 可能是在处理大量 Defs 文件，请耐心等待或检查模组结构是否正常。

**Q: 翻译结果不准确？**
A: 可以调整过滤规则，或者使用手工校对功能。

**Q: 导入后模组无法加载？**
A: 检查 XML 文件格式是否正确，确保没有语法错误。

**Q: Java翻译工具无法使用？**
A: 检查Java和Maven是否正确安装，确保JAR文件已正确构建。

### 日志调试

启用调试模式可以获得详细的运行日志：
```python
CONFIG.update_config('debug_mode', True)
```

日志文件位置：`logs/day_translation.log`

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境搭建

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 运行测试：`python -m pytest tests/`

### 代码结构说明

- **core/**: 核心业务逻辑，包含主要的翻译处理功能
- **utils/**: 工具模块，提供配置、过滤、路径管理等支持功能
- **RimWorldBatchTranslate/**: Java翻译工具，提供高性能批量翻译
- **tests/**: 单元测试和集成测试

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🙏 致谢

感谢 RimWorld 模组社区的支持和贡献！

---

**Happy Translating! 🌟**
