#!/usr/bin/env python3
"""
Day Translation 2 - 系统函数关系分析工具

分析整个系统中所有函数的上下级调用关系和依赖关系。
生成完整的函数调用图谱。
"""

import ast
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class FunctionAnalyzer(ast.NodeVisitor):
    """AST节点访问器，用于分析函数定义和调用"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions = []  # 定义的函数
        self.calls = []  # 函数调用
        self.imports = []  # 导入语句
        self.classes = []  # 类定义
        self.current_class = None
        self.current_function = None

    def visit_FunctionDef(self, node):
        """访问函数定义"""
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "decorators": [self.get_decorator_name(d) for d in node.decorator_list],
            "class": self.current_class,
            "docstring": ast.get_docstring(node),
        }
        self.functions.append(func_info)

        # 进入函数作用域
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        """访问异步函数定义"""
        self.visit_FunctionDef(node)  # 处理方式相同

    def visit_ClassDef(self, node):
        """访问类定义"""
        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "bases": [self.get_name(base) for base in node.bases],
            "decorators": [self.get_decorator_name(d) for d in node.decorator_list],
            "docstring": ast.get_docstring(node),
        }
        self.classes.append(class_info)

        # 进入类作用域
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """访问函数调用"""
        call_info = {
            "name": self.get_call_name(node),
            "lineno": node.lineno,
            "in_function": self.current_function,
            "in_class": self.current_class,
            "args_count": len(node.args),
        }
        self.calls.append(call_info)
        self.generic_visit(node)

    def visit_Import(self, node):
        """访问import语句"""
        for alias in node.names:
            import_info = {
                "type": "import",
                "name": alias.name,
                "asname": alias.asname,
                "lineno": node.lineno,
            }
            self.imports.append(import_info)

    def visit_ImportFrom(self, node):
        """访问from...import语句"""
        for alias in node.names:
            import_info = {
                "type": "from_import",
                "module": node.module,
                "name": alias.name,
                "asname": alias.asname,
                "level": node.level,
                "lineno": node.lineno,
            }
            self.imports.append(import_info)

    def get_decorator_name(self, decorator):
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self.get_name(decorator.value)}.{decorator.attr}"
        else:
            return "unknown_decorator"

    def get_name(self, node):
        """获取名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        else:
            return "unknown"

    def get_call_name(self, node):
        """获取函数调用名称"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self.get_name(node.func.value)}.{node.func.attr}"
        else:
            return "unknown_call"


class SystemAnalyzer:
    """系统级函数关系分析器"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.files_data = {}  # 文件路径 -> 分析数据
        self.function_registry = {}  # 函数名 -> 定义位置列表
        self.call_graph = defaultdict(set)  # 调用关系图
        self.import_graph = defaultdict(set)  # 导入关系图

    def analyze_file(self, filepath: Path) -> Optional[Dict]:
        """分析单个Python文件"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = FunctionAnalyzer(str(filepath))
            analyzer.visit(tree)

            return {
                "filepath": str(filepath),
                "functions": analyzer.functions,
                "calls": analyzer.calls,
                "imports": analyzer.imports,
                "classes": analyzer.classes,
            }
        except Exception as e:
            print(f"❌ 分析文件失败 {filepath}: {e}")
            return None

    def analyze_directory(self):
        """分析整个目录"""
        print(f"🔍 分析目录: {self.root_dir}")

        python_files = list(self.root_dir.rglob("*.py"))
        print(f"📝 找到 {len(python_files)} 个Python文件")

        for filepath in python_files:
            if "__pycache__" in str(filepath):
                continue

            file_data = self.analyze_file(filepath)
            if file_data:
                self.files_data[str(filepath)] = file_data
                self._register_functions(file_data)

        # 构建调用关系图
        self._build_call_graph()
        self._build_import_graph()

    def _register_functions(self, file_data: Dict):
        """注册函数定义"""
        for func in file_data["functions"]:
            func_name = func["name"]
            if func["class"]:
                full_name = f"{func['class']}.{func_name}"
            else:
                full_name = func_name

            if full_name not in self.function_registry:
                self.function_registry[full_name] = []

            self.function_registry[full_name].append(
                {
                    "file": file_data["filepath"],
                    "line": func["lineno"],
                    "class": func["class"],
                    "args": func["args"],
                    "decorators": func["decorators"],
                }
            )

    def _build_call_graph(self):
        """构建函数调用关系图"""
        for file_data in self.files_data.values():
            for call in file_data["calls"]:
                caller = call["in_function"]
                if call["in_class"]:
                    caller = f"{call['in_class']}.{caller}" if caller else call["in_class"]

                if caller:
                    self.call_graph[caller].add(call["name"])

    def _build_import_graph(self):
        """构建导入关系图"""
        for file_data in self.files_data.values():
            filepath = file_data["filepath"]
            for imp in file_data["imports"]:
                if imp["type"] == "import":
                    self.import_graph[filepath].add(imp["name"])
                elif imp["type"] == "from_import":
                    module = imp["module"] or "relative"
                    self.import_graph[filepath].add(f"{module}.{imp['name']}")

    def get_function_callers(self, func_name: str) -> List[str]:
        """获取调用指定函数的所有函数"""
        callers = []
        for caller, callees in self.call_graph.items():
            if func_name in callees:
                callers.append(caller)
        return callers

    def get_function_callees(self, func_name: str) -> Set[str]:
        """获取指定函数调用的所有函数"""
        return self.call_graph.get(func_name, set())

    def generate_report(self) -> Dict:
        """生成分析报告"""
        # 统计数据
        total_functions = sum(len(data["functions"]) for data in self.files_data.values())
        total_calls = sum(len(data["calls"]) for data in self.files_data.values())
        total_classes = sum(len(data["classes"]) for data in self.files_data.values())

        # 找出最常被调用的函数
        call_counts = defaultdict(int)
        for callees in self.call_graph.values():
            for callee in callees:
                call_counts[callee] += 1

        most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 找出调用最多函数的函数
        caller_counts = [(caller, len(callees)) for caller, callees in self.call_graph.items()]
        most_callers = sorted(caller_counts, key=lambda x: x[1], reverse=True)[:10]

        # 找出孤立函数（既不调用其他函数，也不被调用）
        all_functions = set(self.function_registry.keys())
        called_functions = set()
        calling_functions = set(self.call_graph.keys())

        for callees in self.call_graph.values():
            called_functions.update(callees)

        isolated_functions = all_functions - called_functions - calling_functions

        return {
            "summary": {
                "total_files": len(self.files_data),
                "total_functions": total_functions,
                "total_calls": total_calls,
                "total_classes": total_classes,
                "unique_functions": len(self.function_registry),
            },
            "most_called_functions": most_called,
            "most_calling_functions": most_callers,
            "isolated_functions": list(isolated_functions),
            "function_registry": dict(self.function_registry),
            "call_relationships": {k: list(v) for k, v in self.call_graph.items()},
            "import_relationships": {k: list(v) for k, v in self.import_graph.items()},
        }


def main():
    """主函数"""
    root_dir = Path(__file__).parent
    analyzer = SystemAnalyzer(str(root_dir))

    print("🚀 开始分析Day_translation2系统...")
    analyzer.analyze_directory()

    print("📊 生成分析报告...")
    report = analyzer.generate_report()

    # 保存报告
    report_file = root_dir / "system_function_analysis.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ 分析完成！报告保存到: {report_file}")

    # 打印摘要
    summary = report["summary"]
    print(f"\n📈 系统摘要:")
    print(f"  - 文件数: {summary['total_files']}")
    print(f"  - 函数数: {summary['total_functions']}")
    print(f"  - 类数: {summary['total_classes']}")
    print(f"  - 函数调用数: {summary['total_calls']}")
    print(f"  - 唯一函数数: {summary['unique_functions']}")

    print(f"\n🔥 最常被调用的函数:")
    for func, count in report["most_called_functions"][:5]:
        print(f"  - {func}: {count}次")

    print(f"\n🧩 调用最多函数的函数:")
    for func, count in report["most_calling_functions"][:5]:
        print(f"  - {func}: 调用{count}个函数")

    if report["isolated_functions"]:
        print(f"\n🏝️ 孤立函数 ({len(report['isolated_functions'])}个):")
        for func in report["isolated_functions"][:10]:
            print(f"  - {func}")


if __name__ == "__main__":
    main()
