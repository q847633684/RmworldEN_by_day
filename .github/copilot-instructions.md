# Day Translation AI 助手指南

## 🏗️ 项目架构

Day Translation 是专为 RimWorld 模组设计的翻译工具包,采用模块化架构:

```
day_translation/
├── core/                 # 核心业务逻辑和外观模式接口
│   └── translation_facade.py  # 统一外观接口
├── extract/             # 翻译提取与导出
│   ├── template_manager.py    # 核心控制器
│   ├── interaction_manager.py # 智能交互
│   └── smart_merger.py        # 智能合并
├── import_template/     # CSV到XML翻译导入
├── utils/              # 工具类和通用功能
│   └── XMLProcessor.py      # XML统一处理
└── batch/             # 批处理功能
```

关键数据流:
1. 用户输入 → main.py → TranslationFacade
2. TranslationFacade → TemplateManager → 提取/生成/导出
3. XMLProcessor 处理所有 XML 操作

## 💡 特有设计模式

### 统一数据格式
所有翻译数据使用五元组格式:
```python
(key, text, tag, file, en_text)
# 示例: ("ThingDef/Apparel_Pants.label", "裤子", "label", "Apparel.xml", "Pants")
```

### 智能工作流
InteractionManager 实现四步智能流程:
1. 检测英文目录状态 (DefInjected/Keyed)
2. 检测输出目录状态
3. 选择数据来源 (DefInjected提取/Defs扫描)
4. 处理输出冲突 (合并/覆盖/重建)

### DefInjected 结构支持
支持三种导出结构:
- original_structure: 保持原英文结构
- defs_by_type: 按定义类型分组
- defs_by_file: 按原始文件结构

## 🔧 关键开发约定

### XML 处理规范
- 必须使用 `XMLProcessor` 进行所有 XML 操作
- 禁止直接使用 lxml.etree 或其他 XML 库
- 保存时必须启用格式化

### 错误处理
- 使用自定义异常类
- 详细记录错误上下文
- 提供用户友好的错误消息

### 路径处理
- 使用 `Path` 对象操作路径
- 通过 `PathManager` 管理路径
- 支持智能路径推荐

## 🚀 常见开发任务

### 添加新翻译处理流程
1. 在 extract/ 或 import_template/ 添加功能
2. 更新 TranslationFacade 接口
3. 在 main.py 添加操作模式
4. 更新交互逻辑

### 扩展 DefInjected 结构
1. exporters.py 添加导出方法
2. 更新结构选择处理
3. 添加用户界面选项
4. 更新文档

## ⚠️ 特殊注意事项

- 保持向后兼容性
- 大文件使用迭代器处理
- 统一使用 UTF-8 编码
- 支持智能合并和历史记录
- 确保跨平台兼容性

## 📚 更多参考
- `core/API_CALLS.md` - API 调用关系
- `extract/merge_flow.md` - 合并流程说明
- `AI_工作记忆/` - 历史经验和最佳实践