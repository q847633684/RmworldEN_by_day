# 成人内容翻译解决方案

## 🎯 问题描述

在使用机器翻译API时，某些成人内容（如"cum"、"penis"等）会被翻译服务过滤，导致无法正确翻译。

## 🛠️ 解决方案

我们提供了多种解决方案来处理成人内容翻译问题：

### 方案1：自动预处理（推荐）

**特点**：集成到翻译流程中，自动处理成人内容
**优点**：无需手动干预，翻译流程更顺畅

#### 使用方法：
1. 正常使用翻译功能
2. 系统会自动检测并预处理成人内容
3. 然后使用翻译API处理剩余内容

```bash
# 正常使用翻译功能即可
python main.py
# 选择 "Python机翻" 或 "Java机翻"
```

### 方案2：独立成人内容翻译工具

**特点**：独立工具，专门处理成人内容
**优点**：可以单独使用，支持自定义词典

#### 使用方法：

```bash
# 查看帮助
python adult_content_tool.py --help

# 显示词典统计信息
python adult_content_tool.py --stats

# 翻译CSV文件中的成人内容
python adult_content_tool.py input.csv -o output.csv

# 添加自定义翻译
python adult_content_tool.py --add "cum" "精液"

# 重新加载词典
python adult_content_tool.py --reload
```

### 方案3：手动编辑词典

**特点**：直接编辑词典文件，添加更多翻译
**优点**：完全自定义，支持批量添加

#### 编辑词典文件：
文件位置：`user_config/config/translation_dictionary.yaml`

```yaml
# 成人内容翻译词典
adult_content:
  description: "成人内容翻译词典 - 用于处理翻译API无法处理的敏感内容"
  entries:
    - english: "cum"
      chinese: "精液"
      context: "生理描述"
      priority: "high"
      note: "翻译API可能过滤此内容"
    
    - english: "penis"
      chinese: "阴茎"
      context: "生理描述"
      priority: "high"
    
    # 添加更多翻译...
```

## 📚 词典内容

当前词典包含以下类别的成人内容翻译：

### 生理相关
- cum → 精液
- semen → 精液
- sperm → 精子
- penis → 阴茎
- vagina → 阴道
- breast → 乳房
- nipple → 乳头
- clitoris → 阴蒂
- anus → 肛门
- prostate → 前列腺

### 性行为相关
- sex → 性行为
- sexual → 性的
- intercourse → 性交
- masturbation → 手淫
- orgasm → 性高潮
- ejaculation → 射精
- erection → 勃起
- arousal → 性兴奋
- lust → 性欲
- desire → 欲望

### 性取向相关
- homosexual → 同性恋
- heterosexual → 异性恋
- bisexual → 双性恋
- asexual → 无性恋

### 性行为方式
- oral → 口交
- anal → 肛交
- vaginal → 阴道性交
- foreplay → 前戏
- penetration → 插入
- thrust → 抽插

### 性相关疾病
- STD → 性传播疾病
- STI → 性传播感染
- HIV → 艾滋病病毒
- AIDS → 艾滋病

### 性相关物品
- condom → 避孕套
- contraceptive → 避孕药
- lubricant → 润滑剂
- vibrator → 振动器
- dildo → 假阳具

### 性相关状态
- virgin → 处女/处男
- virginity → 童贞
- promiscuous → 滥交的
- fidelity → 忠诚
- infidelity → 不忠

### 性相关情感
- passion → 激情
- intimacy → 亲密
- romance → 浪漫
- seduction → 诱惑
- flirt → 调情

### 性相关动作
- kiss → 接吻
- hug → 拥抱
- caress → 爱抚
- fondle → 抚摸
- touch → 触摸

### 性相关描述词
- naked → 裸体
- nude → 裸体
- bare → 裸露
- exposed → 暴露
- clothed → 穿着衣服
- dressed → 穿着

## 🔧 技术实现

### 工作流程：
1. **检测阶段**：扫描文本中的成人内容词汇
2. **预处理阶段**：使用自定义词典翻译成人内容
3. **机器翻译阶段**：使用翻译API处理剩余内容
4. **后处理阶段**：合并结果并清理临时文件

### 核心特性：
- **精确匹配**：使用正则表达式确保精确匹配
- **优先级处理**：长词汇优先，避免部分匹配
- **临时文件管理**：自动创建和清理临时文件
- **错误处理**：完善的错误处理和日志记录
- **可扩展性**：支持动态添加自定义翻译

## 📝 使用建议

### 1. 推荐使用方案1（自动预处理）
- 集成度高，使用简单
- 适合大多数用户

### 2. 需要自定义翻译时使用方案2
- 添加特定词汇的翻译
- 批量处理特定文件

### 3. 需要大量自定义时使用方案3
- 直接编辑词典文件
- 支持批量添加翻译

## ⚠️ 注意事项

1. **词典文件格式**：必须保持YAML格式正确
2. **编码问题**：确保文件使用UTF-8编码
3. **备份建议**：修改词典前建议备份原文件
4. **测试建议**：添加新翻译后建议先测试

## 🚀 扩展功能

### 添加新翻译：
```bash
# 使用命令行添加
python adult_content_tool.py --add "new_word" "新词汇"

# 或直接编辑词典文件
# 在 user_config/config/translation_dictionary.yaml 中添加
```

### 批量导入：
可以创建包含多个翻译的YAML文件，然后合并到主词典中。

## 📞 技术支持

如果遇到问题，请检查：
1. 词典文件是否存在且格式正确
2. yaml库是否正确安装
3. 文件权限是否正确
4. 日志文件中的错误信息

---

**总结**：这个解决方案提供了完整的成人内容翻译处理能力，既支持自动化处理，也支持手动自定义，能够有效解决翻译API过滤敏感内容的问题。
