# 快速开始指南

## 🚀 立即可以开始的任务

### 1. 历史记录功能 (最简单)
**预计时间**: 2-3小时
**难度**: ⭐⭐

```python
# 1. 创建 user_config/history_manager.py
# 2. 修改 main.py 添加历史记录选项
# 3. 在 UI 中显示最近使用的路径
```

**第一步**: 创建历史记录管理器
```python
# user_config/history_manager.py
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class HistoryManager:
    def __init__(self):
        self.history_file = Path("user_config/history.json")
        self.history = self._load_history()
    
    def add_path(self, path: str, mod_name: str = None):
        """添加路径到历史记录"""
        entry = {
            "path": path,
            "mod_name": mod_name,
            "timestamp": datetime.now().isoformat(),
            "access_count": 1
        }
        
        # 更新历史记录
        if path in self.history:
            self.history[path]["access_count"] += 1
            self.history[path]["timestamp"] = entry["timestamp"]
        else:
            self.history[path] = entry
        
        self._save_history()
    
    def get_recent_paths(self, limit: int = 10) -> List[Dict]:
        """获取最近使用的路径"""
        return sorted(
            self.history.values(),
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
    
    def _load_history(self) -> Dict:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
```

### 2. 词典系统扩展 (中等难度)
**预计时间**: 4-6小时
**难度**: ⭐⭐⭐

```python
# 1. 创建 r18_dictionary.yaml 和 general_dictionary.yaml
# 2. 修改 DictionaryTranslator 支持多词典
# 3. 添加内容类型检测
```

**第一步**: 创建词典文件
```yaml
# user_config/config/r18_dictionary.yaml
r18_terms:
  # 生理相关
  cum: "精液"
  semen: "精液"
  orgasm: "高潮"
  
  # 行为相关
  rape: "强奸"
  bestiality: "兽交"
  masturbation: "自慰"
  
  # 身体部位
  penis: "阴茎"
  vagina: "阴道"
  breasts: "乳房"
```

```yaml
# user_config/config/general_dictionary.yaml
general_terms:
  # 游戏术语
  colonist: "殖民者"
  colony: "殖民地"
  raid: "袭击"
  mood: "心情"
  
  # 物品相关
  weapon: "武器"
  armor: "护甲"
  food: "食物"
  medicine: "药品"
```

### 3. 智能对比系统 (中等难度)
**预计时间**: 6-8小时
**难度**: ⭐⭐⭐

```python
# 1. 创建 extract/core/comparison/smart_comparator.py
# 2. 添加对比功能到主界面
# 3. 生成对比报告
```

**第一步**: 创建智能对比器
```python
# extract/core/comparison/smart_comparator.py
import csv
from pathlib import Path
from typing import List, Dict, Set, Tuple

class SmartComparator:
    def __init__(self):
        self.logger = get_logger(f"{__name__}.SmartComparator")
    
    def compare_csv_files(self, existing_csv: Path, new_data: List[Tuple]) -> Dict:
        """对比 CSV 文件和新数据"""
        existing_keys = self._load_csv_keys(existing_csv)
        new_keys = self._extract_keys_from_data(new_data)
        
        return {
            "missing_in_existing": new_keys - existing_keys,
            "missing_in_new": existing_keys - new_keys,
            "common_keys": existing_keys & new_keys,
            "stats": {
                "existing_count": len(existing_keys),
                "new_count": len(new_keys),
                "missing_count": len(new_keys - existing_keys),
                "extra_count": len(existing_keys - new_keys)
            }
        }
    
    def _load_csv_keys(self, csv_path: Path) -> Set[str]:
        """从 CSV 文件加载 key"""
        keys = set()
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                for row in reader:
                    if row:
                        keys.add(row[0])  # 假设第一列是 key
        return keys
    
    def _extract_keys_from_data(self, data: List[Tuple]) -> Set[str]:
        """从数据中提取 key"""
        return {item[0] for item in data if item}
    
    def generate_report(self, comparison_result: Dict) -> str:
        """生成对比报告"""
        stats = comparison_result["stats"]
        report = []
        report.append("=== 翻译内容对比报告 ===")
        report.append(f"现有 key 数量: {stats['existing_count']}")
        report.append(f"新 key 数量: {stats['new_count']}")
        report.append(f"缺失 key 数量: {stats['missing_count']}")
        report.append(f"多余 key 数量: {stats['extra_count']}")
        
        if comparison_result["missing_in_existing"]:
            report.append("\n需要新增的 key:")
            for key in sorted(comparison_result["missing_in_existing"]):
                report.append(f"  - {key}")
        
        return "\n".join(report)
```

## 🎯 本周可以完成的任务

### 第1天: 历史记录功能
- [ ] 创建 `HistoryManager` 类
- [ ] 修改主界面添加历史记录选项
- [ ] 测试历史记录功能

### 第2天: 词典系统
- [ ] 创建 R18 和常规词典文件
- [ ] 修改 `DictionaryTranslator` 支持多词典
- [ ] 测试词典翻译功能

### 第3天: 智能对比系统
- [ ] 创建 `SmartComparator` 类
- [ ] 添加对比功能到主界面
- [ ] 测试对比功能

### 第4天: 内嵌 Mod 支持
- [ ] 修改提取器支持递归扫描
- [ ] 添加内嵌 Mod 检测
- [ ] 测试内嵌 Mod 功能

### 第5天: 测试和优化
- [ ] 全面测试新功能
- [ ] 优化性能和用户体验
- [ ] 修复发现的问题

## 🔧 开发环境设置

### 1. 安装依赖
```bash
pip install pythonnet dnspy
```

### 2. 创建测试目录
```bash
mkdir test_mods
mkdir test_mods/nested_mod
mkdir test_mods/common_mod
```

### 3. 准备测试数据
```bash
# 创建测试用的 XML 文件
# 创建测试用的 DLL 文件
# 创建测试用的 CSV 文件
```

## 📝 开发注意事项

### 1. 代码规范
- 使用类型提示
- 添加详细的文档字符串
- 遵循现有的代码风格

### 2. 错误处理
- 添加适当的异常处理
- 记录详细的错误日志
- 提供用户友好的错误信息

### 3. 性能考虑
- 使用缓存减少重复计算
- 避免内存泄漏
- 优化大文件处理

### 4. 测试策略
- 编写单元测试
- 进行集成测试
- 测试边界情况

## 🚨 常见问题

### Q: DLL 解析失败怎么办？
A: 检查 DLL 文件是否损坏，尝试使用不同的反编译工具

### Q: 内嵌 Mod 扫描太慢？
A: 使用并行处理，添加进度条，优化扫描算法

### Q: 词典翻译不准确？
A: 检查词典文件格式，验证正则表达式，测试翻译结果

### Q: 历史记录丢失？
A: 检查文件权限，验证 JSON 格式，添加备份机制

---

这个快速开始指南提供了立即可行的开发路径，建议从简单的功能开始，逐步实现复杂的功能。
