#!/usr/bin/env python3
"""
生成核心函数详细调用关系分析
"""

import json
from pathlib import Path


def analyze_core_relationships():
    """分析核心函数的详细调用关系"""

    # 读取分析结果
    with open("system_function_analysis.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    call_relationships = data["call_relationships"]
    function_registry = data["function_registry"]

    # 定义核心函数列表
    core_functions = [
        "extract_keyed_translations",
        "extract_definjected_translations",
        "scan_defs_sync",
        "_extract_translatable_fields_recursive",
        "export_keyed",
        "export_definjected",
        "export_with_smart_merge",
        "import_translations",
        "update_all_xml",
        "load_translations_from_csv",
        "should_translate_field",
        "should_translate_keyed",
        "should_translate_def_field",
        "is_non_text_content",
    ]

    print("# 核心函数详细调用关系分析\n")

    for func_name in core_functions:
        print(f"## {func_name}\n")

        # 函数定义信息
        if func_name in function_registry:
            definitions = function_registry[func_name]
            for defn in definitions:
                print(f"**定义位置**: `{Path(defn['file']).name}:{defn['line']}`")
                if defn["class"]:
                    print(f"**所属类**: `{defn['class']}`")
                print(f"**参数**: {defn['args']}")
                if defn["decorators"]:
                    print(f"**装饰器**: {defn['decorators']}")
                print()

        # 调用的函数 (下级)
        if func_name in call_relationships:
            callees = call_relationships[func_name]
            if callees:
                print("**调用的函数** (下级):")
                for callee in sorted(callees):
                    print(f"- `{callee}`")
                print()

        # 被调用的函数 (上级)
        callers = []
        for caller, callees in call_relationships.items():
            if func_name in callees:
                callers.append(caller)

        if callers:
            print("**被以下函数调用** (上级):")
            for caller in sorted(callers):
                print(f"- `{caller}`")
            print()

        print("---\n")


if __name__ == "__main__":
    analyze_core_relationships()
