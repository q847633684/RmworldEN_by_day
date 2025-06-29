# Day Translation - RimWorld 模组汉化智能工具

## 📖 项目简介

Day Translation 是专为 RimWorld 模组开发者和汉化团队打造的智能化翻译工具，集成了**智能提取、智能合并、批量处理、交互优化**等现代化特性，极大提升了模组汉化的效率与质量。

---

## 🏗️ 最新目录结构

```
day_translation/
├── batch/                # 批量处理与任务调度
├── config_manage/        # 配置管理与交互
├── core/                 # 核心业务逻辑（门面、异常等）
├── corpus/               # 平行语料生成与管理
├── extract/              # 智能提取、合并、模板管理
├── full_pipeline/        # 一键全流程处理
├── import_template/      # 翻译导入与模板处理
├── interact/             # 交互相关
├── java_translate/       # Java批量翻译工具集成
├── python_translate/     # Python机器翻译
├── utils/                # 工具库（路径、过滤、配置等）
├── main.py               # 主入口
└── README.md
```

---

## ✨ 核心功能

- **智能提取**：自动识别模组结构，支持 DefInjected/Defs/Keyed 多种提取模式，兼容主流 RimWorld 模组。
- **智能合并**：支持增量合并新旧翻译，自动检测并处理冲突，避免重复劳动。
- **交互优化**：历史路径、目录选择、参数记忆、命令行美化，极大提升用户体验。
- **批量处理**：支持多模组批量提取、翻译、导入，适合团队协作。
- **机器翻译集成**：支持阿里云等主流翻译 API，自动生成翻译草稿。
- **平行语料生成**：一键导出英中对照语料，便于训练自定义模型。
- **配置灵活**：支持自定义过滤、输出结构、合并策略等。

---

## 🚀 主要工作流

### 1. 智能提取
- 选择模组目录和输出目录
- 智能检测并推荐提取模式（英文 DefInjected/全量 Defs/Keyed）
- 生成标准化 XML 模板和 CSV 文件

### 2. 机器翻译（可选）
- 支持 Python/Java 两种批量翻译方式
- 机器翻译后可手动校对

### 3. 智能合并
- 支持"重建/覆盖/合并"三种冲突处理策略
- 合并模式下自动对比新旧翻译，增量更新，保留人工校对内容

### 4. 导入翻译
- 一键将翻译 CSV 导入 XML 模板
- 支持合并/覆盖导入

---

## ⚙️ 主要配置项

- `default_language`：目标语言（默认 ChineseSimplified）
- `source_language`：源语言（默认 English）
- `keyed_dir`/`def_injected_dir`：目录名自定义
- `debug_mode`：调试日志开关
- 详见 `utils/config.py`

---

## 🐛 常见问题与故障排除

- **合并后 Keyed 文件变成一行？**  
  目前已统一用 XMLProcessor 格式化，若仍有问题请反馈 issue。
- **合并功能未生效？**  
  请确保输出目录下有现有翻译文件，且选择"合并"模式。
- **导入后模组无法加载？**  
  检查 XML 文件格式，建议用 Notepad++/VSCode 等工具校验。
- **其他问题**  
  详见 [AI_工作记忆/核心记忆/智能合并功能问题记录.md]，或提交 issue。

---

## 🤝 参与开发

1. 克隆仓库并安装依赖  
   `pip install -r requirements.txt`
2. 运行主程序  
   `python day_translation/main.py`
3. 贡献代码请提交 Pull Request，或通过 Issue 反馈问题

---

## 📄 许可证

MIT License

---

**Happy Translating! 🌟**
