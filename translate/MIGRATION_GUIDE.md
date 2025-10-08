# 统一翻译接口迁移指南

## 🎯 概述

新的统一翻译接口将多种翻译方式（Java、Python）整合到一个统一的接口中，提供更好的用户体验和更清晰的代码结构。

## 📁 新的模块结构

```
translate/                   # 新的统一翻译模块
├── __init__.py             # 统一入口
├── core/                   # 核心翻译逻辑
│   ├── __init__.py
│   ├── unified_translator.py    # 统一翻译器
│   ├── translator_factory.py     # 翻译器工厂
│   └── translation_config.py    # 翻译配置
└── MIGRATION_GUIDE.md      # 本迁移指南
```

## 🔄 迁移步骤

### 步骤1：更新TranslationFacade

**修改前：**
```python
# core/translation_facade.py
from utils.machine_translate import translate_csv

def machine_translate(self, csv_path: str, output_csv: Optional[str] = None) -> None:
    translate_csv(csv_path, output_csv)
```

**修改后：**
```python
# core/translation_facade.py
from translate import UnifiedTranslator

def machine_translate(self, csv_path: str, output_csv: Optional[str] = None, translator_type: str = "auto") -> None:
    translator = UnifiedTranslator()
    success = translator.translate_csv(csv_path, output_csv, translator_type)
    if not success:
        raise TranslationError("翻译失败")
```

### 步骤2：更新主菜单

**修改前：**
```python
# main.py
from java_translate.handler import handle_java_translate
from python_translate.handler import handle_python_translate

# 分别处理Java和Python翻译
elif mode == "3":
    handle_java_translate()
elif mode == "5":
    handle_python_translate()
```

**修改后：**
```python
# main.py
from translate.handler import handle_unified_translate

# 替换原有的翻译选项
elif mode == "3":
    handle_unified_translate()
```

### 步骤3：删除重复模块

**已迁移的文件：**
- `utils/machine_translate.py` → `translate/core/python_translator.py`（Python翻译实现）
- `java_translate/java_translator_simple.py` → `translate/core/java_translator.py`（Java翻译实现）
- `python_translate/` 整个目录（功能重复，已删除）
- `java_translate/handler.py` 和 `java_translate/__init__.py`（已废弃，已删除）

**保留的文件：**
- `translate/core/java_translate/RimWorldBatchTranslate/`（Java Maven项目，包含构建产物）
- `core/translation_facade.py`（增强功能）

## 🚀 新功能特性

### 1. 自动翻译器选择
```python
translator = UnifiedTranslator()

# 自动选择最佳翻译器（优先Java，回退Python）
success = translator.translate_csv("input.csv", "output.csv")
```

### 2. 强制指定翻译器
```python
# 强制使用Java翻译器
success = translator.translate_csv("input.csv", "output.csv", translator_type="java")

# 强制使用Python翻译器
success = translator.translate_csv("input.csv", "output.csv", translator_type="python")
```

### 3. 恢复翻译功能
```python
# 检查是否可以恢复
resume_file = translator.can_resume_translation("input.csv")
if resume_file:
    # 恢复翻译
    success = translator.resume_translation("input.csv", resume_file)
```

### 4. 翻译器状态检查
```python
# 获取所有翻译器状态
available = translator.get_available_translators()
print(available)
# 输出: {
#   'java': {'available': True, 'jar_path': '...'},
#   'python': {'available': True, 'reason': 'Python翻译器可用'}
# }
```

## ⚙️ 配置管理

### 用户配置集成
统一翻译接口会自动从用户配置中读取API密钥：

```python
# 用户配置示例
user_config = {
    'aliyun_access_key_id': 'your_key',
    'aliyun_access_key_secret': 'your_secret',
    'default_translator': 'auto',  # 默认翻译器选择
    'model_id': 27345,            # 翻译模型ID
    'sleep_sec': 0.5,             # 翻译间隔
}
```

### 运行时配置
```python
# 创建自定义配置
config = TranslationConfig({
    'access_key_id': 'runtime_key',
    'access_key_secret': 'runtime_secret',
    'default_translator': 'java'
})

translator = UnifiedTranslator(config)
```

## 🔧 向后兼容性

### 保持现有接口
现有的 `TranslationFacade.machine_translate()` 接口保持不变，只是内部实现改为使用统一翻译器。

### 渐进式迁移
可以逐步迁移，不需要一次性修改所有代码：

1. **第一阶段**：创建统一翻译接口
2. **第二阶段**：更新核心组件（TranslationFacade）
3. **第三阶段**：更新用户界面（主菜单）
4. **第四阶段**：删除重复模块

## 🐛 故障排除

### 常见问题

1. **Java翻译器不可用**
   - 检查Java环境是否正确安装
   - 检查JAR文件是否已构建
   - 运行：`cd translate/core/java_translate/RimWorldBatchTranslate && mvn package`

2. **Python翻译器不可用**
   - 检查阿里云SDK是否安装：`pip install aliyun-python-sdk-core aliyun-python-sdk-alimt`
   - 检查API密钥是否正确配置

3. **翻译失败**
   - 检查网络连接
   - 检查API密钥有效性
   - 查看日志文件获取详细错误信息

### 调试模式
```python
import logging
logging.getLogger('translate').setLevel(logging.DEBUG)

translator = UnifiedTranslator()
# 现在会显示详细的调试信息
```

## 📈 性能优化

### Java翻译器优势
- 处理大量数据时性能更好
- 支持中断和恢复功能
- 内存使用更高效

### Python翻译器优势
- 部署简单，无需Java环境
- 与现有Python代码集成更好
- 错误处理更灵活

### 自动选择策略
统一翻译接口会根据以下条件自动选择最佳翻译器：
1. Java翻译器可用 → 选择Java
2. Java不可用，Python可用 → 选择Python
3. 都不可用 → 抛出异常

## 🎉 总结

统一翻译接口提供了：
- ✅ **统一的API**：一个接口支持多种翻译方式
- ✅ **自动选择**：智能选择最佳翻译器
- ✅ **完整功能**：支持恢复、进度显示等高级功能
- ✅ **易于扩展**：添加新翻译器只需实现适配器
- ✅ **向后兼容**：现有代码无需大幅修改

通过这个统一接口，用户可以享受更好的翻译体验，开发者可以更容易地维护和扩展翻译功能！
