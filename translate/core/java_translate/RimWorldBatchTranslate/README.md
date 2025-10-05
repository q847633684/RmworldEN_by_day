# RimWorld Batch Translate

RimWorld模组批量翻译工具 - Java版本

## 功能特性

- 使用阿里云定制翻译模型进行批量翻译
- 支持占位符保护（如 `[待翻译]` 等标记）
- 自动处理CSV文件格式
- 支持中文翻译

## 环境要求

- Java 8 或更高版本
- Maven 3.6 或更高版本

## 安装和构建

### Windows
```bash
# 运行构建脚本
build.bat
```

### Linux/Mac
```bash
# 给脚本执行权限
chmod +x build.sh

# 运行构建脚本
./build.sh
```

### 手动构建
```bash
# 清理项目
mvn clean

# 编译项目
mvn compile

# 打包项目
mvn package
```

## 使用方法

### 1. 直接运行JAR文件
```bash
java -jar target/rimworld-batch-translate-1.0.0-jar-with-dependencies.jar
```

### 2. 交互式输入
程序会提示输入以下信息：
- 输入CSV文件名（如：translations.csv）
- 输出CSV文件名（如：translations_zh.csv）
- 阿里云 AccessKeyId
- 阿里云 AccessKeySecret

### 3. 示例
```
请输入输入CSV文件名（如 translations.csv）: input.csv
请输入输出CSV文件名（如 translations_zh.csv）: output.csv
请输入阿里云 AccessKeyId: your_access_key_id
请输入阿里云 AccessKeySecret: your_access_key_secret
```

## CSV文件格式

输入CSV文件应包含以下列：
- `key`: 翻译键
- `text`: 待翻译的英文文本
- 其他列：可选，会被保留到输出文件

输出CSV文件会添加一个 `translated` 列，包含翻译后的中文文本。

## 注意事项

1. **阿里云配置**：需要有效的阿里云账号和AccessKey
2. **翻译模型**：使用阿里云定制翻译模型（ModelId: 27345）
3. **占位符保护**：程序会自动保护 `[xxx]` 格式的占位符
4. **QPS限制**：程序内置500ms延迟，避免触发API限制

## 与Python项目集成

这个Java工具可以与主Python项目配合使用：

1. 使用Python项目提取翻译模板并生成CSV
2. 使用Java工具进行批量翻译
3. 将翻译后的CSV导入回Python项目

## 故障排除

### 常见问题

1. **Maven未安装**
   - 下载并安装Maven：https://maven.apache.org/download.cgi
   - 确保Maven在PATH环境变量中

2. **Java版本过低**
   - 确保使用Java 8或更高版本
   - 检查：`java -version`

3. **依赖下载失败**
   - 检查网络连接
   - 尝试使用国内Maven镜像

4. **阿里云API错误**
   - 检查AccessKey是否正确
   - 确认账号有足够的API调用额度
   - 检查网络连接

## 许可证

本项目遵循与主项目相同的许可证。 