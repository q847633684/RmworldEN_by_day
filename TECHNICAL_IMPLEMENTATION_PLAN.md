# 技术实现计划

## 🎯 核心功能实现方案

### 1. DLL 配置翻译支持

#### 问题分析
- RimWorld 模组可能包含 DLL 文件
- DLL 中可能包含硬编码的翻译内容
- 需要提取 DLL 中的字符串资源

#### 技术方案
```python
# 新增模块: extract/core/extractors/dll_extractor.py
class DLLExtractor(BaseExtractor):
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.DLLExtractor")
    
    def extract(self, source_path: str, language: str = None):
        """从 DLL 文件中提取翻译内容"""
        # 1. 扫描 DLL 文件
        # 2. 使用 .NET 反编译工具提取字符串
        # 3. 识别翻译相关的字符串
        # 4. 返回翻译数据
        pass
    
    def _scan_dll_files(self, mod_dir: Path) -> List[Path]:
        """扫描模组目录中的 DLL 文件"""
        pass
    
    def _extract_strings_from_dll(self, dll_path: Path) -> List[str]:
        """从 DLL 文件中提取字符串"""
        # 可能需要使用 ildasm 或 dnSpy 等工具
        pass
```

#### 依赖工具
- `pythonnet` - .NET 互操作
- `dnSpy` - .NET 反编译工具
- `ildasm` - IL 反汇编器

### 2. 内嵌 Mod 翻译支持

#### 问题分析
- 模组可能包含子模组
- 需要递归扫描所有层级的翻译文件
- 避免重复处理和冲突

#### 技术方案
```python
# 修改: extract/core/extractors/base.py
class BaseExtractor:
    def _scan_recursive(self, directory: Path, pattern: str = "*.xml") -> List[Path]:
        """递归扫描目录"""
        files = []
        for item in directory.rglob(pattern):
            if item.is_file():
                files.append(item)
        return files
    
    def _detect_nested_mods(self, mod_dir: Path) -> List[Path]:
        """检测内嵌的模组"""
        nested_mods = []
        # 查找包含 About.xml 的子目录
        for about_file in mod_dir.rglob("About.xml"):
            nested_mods.append(about_file.parent)
        return nested_mods
```

### 3. Common 类型模组翻译

#### 问题分析
- Common 目录包含共享的翻译内容
- 需要特殊处理 Common 类型的文件结构
- 可能需要合并多个 Common 目录的内容

#### 技术方案
```python
# 新增: extract/core/extractors/common_extractor.py
class CommonExtractor(BaseExtractor):
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = get_logger(f"{__name__}.CommonExtractor")
    
    def extract(self, source_path: str, language: str = None):
        """提取 Common 类型的翻译内容"""
        common_dirs = self._find_common_directories(source_path)
        translations = []
        
        for common_dir in common_dirs:
            # 处理 Common 目录的特殊结构
            common_translations = self._extract_from_common_dir(common_dir)
            translations.extend(common_translations)
        
        return translations
    
    def _find_common_directories(self, mod_dir: Path) -> List[Path]:
        """查找 Common 目录"""
        return list(mod_dir.rglob("Common"))
```

### 4. 词典系统

#### 技术方案
```python
# 新增: translate/dictionary/enhanced_dictionary_manager.py
class EnhancedDictionaryManager:
    def __init__(self, config=None):
        self.config = config or UserConfigManager()
        self.r18_dictionary = self._load_r18_dictionary()
        self.general_dictionary = self._load_general_dictionary()
    
    def _load_r18_dictionary(self) -> Dict[str, str]:
        """加载 R18 词典"""
        return self._load_dictionary("r18_dictionary.yaml")
    
    def _load_general_dictionary(self) -> Dict[str, str]:
        """加载常规词典"""
        return self._load_dictionary("general_dictionary.yaml")
    
    def translate_with_dictionary(self, text: str, content_type: str = "general") -> str:
        """使用词典翻译文本"""
        if content_type == "r18":
            return self._apply_dictionary(text, self.r18_dictionary)
        else:
            return self._apply_dictionary(text, self.general_dictionary)
```

### 5. 历史记录系统

#### 技术方案
```python
# 新增: user_config/history_manager.py
class HistoryManager:
    def __init__(self, config=None):
        self.config = config or UserConfigManager()
        self.history_file = self._get_history_file_path()
        self.history = self._load_history()
    
    def add_path(self, path: str, mod_name: str = None):
        """添加路径到历史记录"""
        history_entry = {
            "path": path,
            "mod_name": mod_name,
            "timestamp": datetime.now().isoformat(),
            "access_count": 1
        }
        
        # 更新或添加历史记录
        self._update_history(history_entry)
        self._save_history()
    
    def get_recent_paths(self, limit: int = 10) -> List[Dict]:
        """获取最近使用的路径"""
        return sorted(
            self.history.values(),
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
```

### 6. 智能对比系统

#### 技术方案
```python
# 新增: extract/core/comparison/smart_comparator.py
class SmartComparator:
    def __init__(self, config=None):
        self.config = config or UserConfigManager()
        self.logger = get_logger(f"{__name__}.SmartComparator")
    
    def compare_translations(self, existing_csv: Path, new_extraction: List[Tuple]) -> Dict:
        """对比翻译内容，识别新增和缺失的 key"""
        existing_keys = self._load_existing_keys(existing_csv)
        new_keys = self._extract_keys_from_data(new_extraction)
        
        return {
            "missing_keys": new_keys - existing_keys,
            "extra_keys": existing_keys - new_keys,
            "common_keys": existing_keys & new_keys,
            "new_keys_count": len(new_keys - existing_keys),
            "total_keys": len(new_keys)
        }
    
    def generate_addition_report(self, comparison_result: Dict) -> str:
        """生成新增 key 的报告"""
        report = []
        report.append("=== 翻译内容对比报告 ===")
        report.append(f"新增 key 数量: {comparison_result['new_keys_count']}")
        report.append(f"总 key 数量: {comparison_result['total_keys']}")
        
        if comparison_result["missing_keys"]:
            report.append("\n新增的 key:")
            for key in sorted(comparison_result["missing_keys"]):
                report.append(f"  - {key}")
        
        return "\n".join(report)
```

## 🏗️ 架构调整

### 1. 提取器注册系统
```python
# 修改: extract/core/extractors/registry.py
class ExtractorRegistry:
    def __init__(self):
        self.extractors = {
            "defs": DefsScanner,
            "keyed": KeyedExtractor,
            "definjected": DefInjectedExtractor,
            "dll": DLLExtractor,  # 新增
            "common": CommonExtractor,  # 新增
        }
    
    def get_extractor(self, extractor_type: str, config=None):
        """获取指定类型的提取器"""
        if extractor_type not in self.extractors:
            raise ValueError(f"Unknown extractor type: {extractor_type}")
        
        return self.extractors[extractor_type](config)
```

### 2. 配置系统扩展
```yaml
# 新增: user_config/config/extraction_rules.yaml
extraction_rules:
  dll_extraction:
    enabled: true
    tools:
      - dnspy
      - ildasm
    patterns:
      - "*.dll"
  
  nested_mods:
    enabled: true
    max_depth: 5
    patterns:
      - "About.xml"
  
  common_extraction:
    enabled: true
    merge_strategy: "append"
    patterns:
      - "Common/**/*.xml"
```

## 🧪 测试策略

### 1. 单元测试
```python
# tests/test_dll_extractor.py
class TestDLLExtractor:
    def test_dll_file_detection(self):
        """测试 DLL 文件检测"""
        pass
    
    def test_string_extraction(self):
        """测试字符串提取"""
        pass
    
    def test_translation_identification(self):
        """测试翻译内容识别"""
        pass
```

### 2. 集成测试
```python
# tests/test_integration.py
class TestIntegration:
    def test_full_extraction_pipeline(self):
        """测试完整的提取流程"""
        pass
    
    def test_nested_mod_handling(self):
        """测试内嵌模组处理"""
        pass
```

## 📊 性能优化

### 1. 并行处理
```python
# 使用多进程处理大量文件
from multiprocessing import Pool

def process_files_parallel(file_list: List[Path], extractor_class, config):
    """并行处理文件列表"""
    with Pool() as pool:
        results = pool.map(
            lambda f: extractor_class(config).extract_from_file(f),
            file_list
        )
    return results
```

### 2. 缓存优化
```python
# 扩展缓存系统
class ExtendedCacheManager:
    def __init__(self):
        self.dll_cache = {}
        self.common_cache = {}
        self.nested_mod_cache = {}
    
    def cache_dll_results(self, dll_path: str, results: List):
        """缓存 DLL 提取结果"""
        self.dll_cache[dll_path] = results
```

## 🔧 部署和配置

### 1. 依赖管理
```bash
# requirements.txt 新增依赖
pythonnet>=3.0.0
dnspy>=6.0.0
```

### 2. 配置文件
```yaml
# config/extraction_settings.yaml
extraction:
  dll:
    enabled: true
    max_file_size: "100MB"
    timeout: 300
  
  nested_mods:
    enabled: true
    max_depth: 5
  
  common:
    enabled: true
    merge_duplicates: true
```

---

这个技术实现计划提供了详细的开发指导，包括代码结构、技术选型、测试策略等。建议按照优先级逐步实现，确保每个功能都经过充分测试。
