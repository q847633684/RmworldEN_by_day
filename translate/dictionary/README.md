# 词典翻译模块

## 概述

词典翻译模块提供了统一的词典翻译功能，支持成人内容和游戏内容两种词典类型。通过自定义词典，可以处理翻译API无法正确处理的敏感内容或特定术语。

## 文件结构

```
translate/dictionary/
├── __init__.py              # 模块初始化
├── dictionary_translator.py  # 通用词典翻译器
├── dictionary_tool.py        # 命令行工具
└── README.md                # 使用说明
```

## 使用方法

### 1. 命令行工具

```bash
# 显示成人内容词典统计
python translate/dictionary/dictionary_tool.py --stats

# 显示游戏内容词典统计
python translate/dictionary/dictionary_tool.py --type game --stats

# 翻译成人内容
python translate/dictionary/dictionary_tool.py input.csv -o output.csv

# 翻译游戏内容
python translate/dictionary/dictionary_tool.py input.csv -o output.csv --type game

# 添加自定义翻译
python translate/dictionary/dictionary_tool.py --add "cum" "精液"
python translate/dictionary/dictionary_tool.py --type game --add "colonist" "殖民者"
```

### 2. Python API

```python
from translate.dictionary import DictionaryTranslator, translate_content_in_csv

# 创建成人内容翻译器
adult_translator = DictionaryTranslator("adult")

# 创建游戏内容翻译器
game_translator = DictionaryTranslator("game")

# 翻译文本
text, used_dict = adult_translator.translate_text("This is a test with cum")
print(f"翻译结果: {text}, 使用了词典: {used_dict}")

# 翻译CSV文件
success = translate_content_in_csv("input.csv", "output.csv", "adult")
```

### 3. 向后兼容API

```python
from translate.dictionary import (
    create_adult_content_translator,
    create_game_content_translator,
    translate_adult_content_in_csv,
    translate_game_content_in_csv
)

# 使用向后兼容的函数
adult_translator = create_adult_content_translator()
game_translator = create_game_content_translator()

# 翻译CSV文件
translate_adult_content_in_csv("input.csv", "output.csv")
translate_game_content_in_csv("input.csv", "output.csv")
```

## 词典文件格式

词典文件采用YAML格式，位于 `user_config/config/` 目录下：

- `adult_dictionary.yaml` - 成人内容词典
- `game_dictionary.yaml` - 游戏内容词典

### 词典文件结构

```yaml
category_name:
  entries:
    - english: "cum"
      chinese: "精液"
    - english: "colonist"
      chinese: "殖民者"
```

## 特性

- ✅ **统一接口**: 一个类支持两种词典类型
- ✅ **精确匹配**: 使用正则表达式进行精确词汇匹配
- ✅ **优先级排序**: 长词汇优先匹配，避免部分匹配问题
- ✅ **向后兼容**: 保持原有API的兼容性
- ✅ **命令行工具**: 提供完整的命令行操作界面
- ✅ **统计信息**: 支持词典统计和状态检查

## 集成到翻译流程

词典翻译已集成到统一翻译器中，在机器翻译之前自动进行预处理：

1. 检查成人内容 → 使用成人内容词典预处理
2. 执行机器翻译 → 使用API进行翻译
3. 清理临时文件 → 删除预处理文件

这样确保了敏感内容能够被正确翻译，而不会被API的内容过滤器拦截。
