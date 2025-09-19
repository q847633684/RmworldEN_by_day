# Day Translation 日志优化指南

## 📋 概述

本文档提供了 Day Translation 项目的统一日志配置和使用指南，确保所有模块的日志记录一致、高效且易于调试。

## 🚀 快速开始

### 1. 自动初始化
项目启动时会自动初始化日志系统，无需手动配置：

```python
# 自动从环境变量读取配置
# DAY_TRANSLATION_LOG_LEVEL=INFO
# DAY_TRANSLATION_LOG_TO_FILE=true
# DAY_TRANSLATION_LOG_TO_CONSOLE=true
```

### 2. 手动配置
如需自定义配置：

```python
from utils.logging_config import LoggingConfig

LoggingConfig.setup_logging(
    level="DEBUG",           # 日志级别
    log_to_file=True,        # 记录到文件
    log_to_console=True,     # 输出到控制台
    log_dir="./custom_logs", # 自定义日志目录
    max_file_size=20*1024*1024,  # 20MB
    backup_count=10          # 保留10个备份文件
)
```

## 📝 日志使用规范

### 1. 获取日志器
```python
from utils.logging_config import get_logger

# 推荐：使用模块名
logger = get_logger(__name__)

# 或者：使用类名
logger = get_logger(f"{__name__}.ClassName")
```

### 2. 日志级别使用指南

#### DEBUG - 调试信息
- 函数调用参数
- 中间计算结果
- 详细的执行流程
- 性能分析数据

```python
logger.debug("处理文件: %s, 参数: %s", file_path, params)
logger.debug("数据验证通过: %d 条记录", count)
```

#### INFO - 一般信息
- 操作开始/结束
- 重要的状态变化
- 用户操作记录
- 系统配置信息

```python
logger.info("开始提取模板: mod_dir=%s", mod_dir)
logger.info("翻译完成: 处理了 %d 条记录", count)
```

#### WARNING - 警告信息
- 非致命错误
- 降级处理
- 配置问题
- 性能警告

```python
logger.warning("模组目录中未找到 Languages 文件夹: %s", mod_dir)
logger.warning("使用默认配置，用户配置无效")
```

#### ERROR - 错误信息
- 操作失败
- 异常情况
- 数据错误
- 系统错误

```python
logger.error("文件读取失败: %s", file_path, exc_info=True)
logger.error("翻译失败: %s", error_message)
```

#### CRITICAL - 严重错误
- 系统崩溃
- 致命错误
- 数据丢失
- 安全威胁

```python
logger.critical("系统初始化失败，无法继续运行")
logger.critical("数据文件损坏，可能导致数据丢失")
```

### 3. 专用日志记录函数

#### 性能监控
```python
from utils.logging_config import log_performance

log_performance("extract_templates", 2.5, 
               files_processed=100, 
               records_extracted=500)
```

#### 用户操作
```python
from utils.logging_config import log_user_action

log_user_action("选择模组", mod_dir=mod_path, language="ChineseSimplified")
log_user_action("开始翻译", csv_file=csv_path, method="java")
```

#### 数据处理
```python
from utils.logging_config import log_data_processing

log_data_processing("智能合并", 1000, 
                   unchanged=800, 
                   updated=150, 
                   new=50)
```

#### 错误上下文
```python
from utils.logging_config import log_error_with_context

try:
    # 一些操作
    pass
except Exception as e:
    log_error_with_context(e, "处理CSV文件", 
                          file_path=csv_path,
                          line_number=123)
```

## 🎯 各模块日志优化建议

### 1. 核心模块 (core/)
- **TranslationFacade**: 记录所有主要操作的开始/结束
- **异常处理**: 使用 `exc_info=True` 记录完整堆栈
- **性能监控**: 记录耗时操作

### 2. 提取模块 (extract/)
- **TemplateManager**: 记录提取进度和统计
- **SmartMerger**: 记录合并策略和结果
- **InteractionManager**: 记录用户交互和选择

### 3. 翻译模块 (java_translate/, python_translate/)
- **翻译开始/结束**: 记录输入输出文件
- **性能统计**: 记录翻译速度和成功率
- **错误处理**: 记录API调用失败

### 4. 工具模块 (utils/)
- **PathManager**: 记录路径操作和验证
- **Config**: 记录配置加载和验证
- **MachineTranslate**: 记录API调用和响应

### 5. 处理器模块 (*/handler.py)
- **用户操作**: 记录所有用户选择
- **错误处理**: 记录异常和降级处理
- **状态变化**: 记录操作状态转换

## 📊 日志文件结构

```
logs/
├── day_translation_20241219_143022.log      # 主日志文件
├── day_translation_error_20241219_143022.log # 错误日志文件
├── day_translation_20241219_143022.log.1    # 轮转备份文件
└── ...
```

## 🔧 环境变量配置

```bash
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export DAY_TRANSLATION_LOG_LEVEL=INFO

# 是否记录到文件 (true/false)
export DAY_TRANSLATION_LOG_TO_FILE=true

# 是否输出到控制台 (true/false)
export DAY_TRANSLATION_LOG_TO_CONSOLE=true

# 自定义日志目录
export DAY_TRANSLATION_LOG_DIR=./custom_logs
```

## 🚫 避免的日志反模式

### 1. 不要使用 print()
```python
# ❌ 错误
print(f"处理文件: {file_path}")

# ✅ 正确
logger.info("处理文件: %s", file_path)
```

### 2. 不要拼接字符串
```python
# ❌ 错误
logger.info("处理文件: " + file_path)

# ✅ 正确
logger.info("处理文件: %s", file_path)
```

### 3. 不要记录敏感信息
```python
# ❌ 错误
logger.info("API密钥: %s", api_key)

# ✅ 正确
logger.info("使用API密钥进行认证")
```

### 4. 不要过度记录
```python
# ❌ 错误 - 在循环中记录太多
for item in items:
    logger.debug("处理项目: %s", item)

# ✅ 正确 - 记录汇总信息
logger.debug("开始处理 %d 个项目", len(items))
# 处理逻辑
logger.debug("完成处理 %d 个项目", len(items))
```

## 📈 性能优化

### 1. 使用延迟格式化
```python
# ✅ 推荐 - 只在需要时格式化
logger.debug("处理结果: %s", expensive_operation())

# ❌ 避免 - 总是执行格式化
logger.debug(f"处理结果: {expensive_operation()}")
```

### 2. 合理设置日志级别
- 生产环境：INFO 或 WARNING
- 开发环境：DEBUG
- 测试环境：INFO

### 3. 控制日志量
- 避免在循环中记录大量日志
- 使用批量操作记录
- 定期清理旧日志文件

## 🔍 调试技巧

### 1. 临时启用调试日志
```python
import logging
logging.getLogger("extract.template_manager").setLevel(logging.DEBUG)
```

### 2. 查看特定模块日志
```python
# 只查看错误日志
grep "ERROR" logs/day_translation_*.log

# 查看特定模块日志
grep "extract.template_manager" logs/day_translation_*.log
```

### 3. 性能分析
```python
# 查看性能日志
grep "性能统计" logs/day_translation_*.log
```

## 📋 检查清单

- [ ] 所有模块都使用统一的日志配置
- [ ] 错误日志包含 `exc_info=True`
- [ ] 性能关键操作有性能监控
- [ ] 用户操作有记录
- [ ] 没有使用 `print()` 语句
- [ ] 日志级别设置合理
- [ ] 敏感信息没有泄露
- [ ] 日志文件定期清理

## 🎉 总结

通过统一的日志系统，我们可以：
- 更好地调试和监控应用
- 追踪用户操作和系统行为
- 分析性能瓶颈
- 快速定位问题
- 提供更好的用户体验

记住：好的日志记录是成功调试的一半！
