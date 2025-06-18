#!/usr/bin/env python3
"""
演示 handle_existing_translations_choice 函数的所有处理方式
展示实际使用场景和最佳实践
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from day_translation.utils.utils import handle_existing_translations_choice

def demo_all_modes():
    """演示所有处理模式"""
    
    print("🎯 handle_existing_translations_choice 函数的所有处理方式演示\n")
    
    # 模拟输出目录
    output_dir = "path/to/output/Languages/ChineseSimplified"
    
    print("📋 目前支持的处理方式：\n")
    
    # 1. 基础处理方式
    print("🔧 基础处理方式：")
    print("  1. replace    - 替换模式：删除现有文件，重新生成")
    print("     💡 适用场景：完全重新开始翻译，或确认现有翻译有问题")
    print("     ⚠️  注意：会永久删除现有翻译文件")
    print()
    
    print("  2. merge      - 合并模式：保留现有翻译，仅更新新内容")
    print("     💡 适用场景：在现有翻译基础上添加新内容")
    print("     ✅ 推荐：大多数情况下的默认选择")
    print()
    
    print("  3. backup     - 备份并替换：备份现有文件，然后重新生成")
    print("     💡 适用场景：需要重新生成但要保留备份")
    print("     📦 会自动创建带时间戳的备份目录")
    print()
    
    print("  4. skip       - 跳过：不生成新文件，保持现状")
    print("     💡 适用场景：检查后决定暂不更新")
    print("     🚫 会终止后续的文件生成流程")
    print()
    
    # 2. 高级处理方式
    print("🚀 高级处理方式（需要启用 enable_advanced_options=True）：")
    print("  5. incremental - 增量更新：只更新有变化的文件")
    print("     💡 适用场景：大型项目的快速更新")
    print("     ⚡ 可以显著节省处理时间")
    print("     📊 会分析文件变化情况")
    print()
    
    print("  6. preview    - 预览模式：先预览变化，再确认执行")
    print("     💡 适用场景：需要确认操作安全性")
    print("     👁️  显示详细的影响文件列表和大小")
    print("     🎛️  可以在预览后选择具体执行方式")
    print()

def demo_usage_examples():
    """演示使用示例"""
    
    print("📝 使用示例：\n")
    
    print("🔹 基本用法（交互模式）：")
    print("```python")
    print("choice = handle_existing_translations_choice('/path/to/output')")
    print("if choice == 'skip':")
    print("    return  # 用户选择跳过，终止生成")
    print("# 继续执行文件生成逻辑...")
    print("```\n")
    
    print("🔹 自动模式（脚本化）：")
    print("```python")
    print("# 自动替换模式")
    print("choice = handle_existing_translations_choice(")
    print("    output_dir, auto_mode='replace'")
    print(")")
    print()
    print("# 自动合并模式")
    print("choice = handle_existing_translations_choice(")
    print("    output_dir, auto_mode='merge'")
    print(")")
    print("```\n")
    
    print("🔹 启用高级功能：")
    print("```python")
    print("choice = handle_existing_translations_choice(")
    print("    output_dir,")
    print("    enable_advanced_options=True,")
    print("    backup_enabled=True")
    print(")")
    print("```\n")
    
    print("🔹 配置文件模式匹配：")
    print("```python")
    print("# 只处理 XML 文件")
    print("choice = handle_existing_translations_choice(")
    print("    output_dir, file_pattern='*.xml'")
    print(")")
    print()
    print("# 处理所有文件")
    print("choice = handle_existing_translations_choice(")
    print("    output_dir, file_pattern='*'")
    print(")")
    print("```\n")

def demo_best_practices():
    """演示最佳实践"""
    
    print("💡 最佳实践建议：\n")
    
    print("1. 🎯 根据场景选择模式：")
    print("   - 首次生成翻译：使用 replace 模式")
    print("   - 更新现有翻译：使用 merge 模式（默认）")
    print("   - 重要项目操作：使用 backup 模式")
    print("   - 大型项目更新：使用 incremental 模式")
    print("   - 不确定操作影响：使用 preview 模式")
    print()
    
    print("2. 🔧 自动化脚本建议：")
    print("   - 开发环境：启用 enable_advanced_options")
    print("   - 生产环境：使用 auto_mode 参数")
    print("   - CI/CD 流水线：使用 backup 或 incremental 模式")
    print()
    
    print("3. 📦 备份策略：")
    print("   - 重要项目始终启用 backup_enabled=True")
    print("   - 定期清理旧备份目录")
    print("   - 结合版本控制系统使用")
    print()
    
    print("4. 🚨 注意事项：")
    print("   - replace 模式会永久删除文件，谨慎使用")
    print("   - preview 模式需要用户交互，不适合自动化")
    print("   - incremental 模式的判断逻辑可能需要调整")
    print("   - 确保有足够的磁盘空间进行备份操作")
    print()

def demo_integration_example():
    """演示与 exporters.py 的集成示例"""
    
    print("🔗 与导出函数的集成示例：\n")
    
    print("```python")
    print("def export_translations_with_choice_handling(output_dir, translations):")
    print("    \"\"\"导出翻译文件，带用户选择处理\"\"\"")
    print("    ")
    print("    # 处理现有文件")
    print("    choice = handle_existing_translations_choice(")
    print("        output_dir,")
    print("        file_pattern='*.xml',")
    print("        backup_enabled=True,")
    print("        enable_advanced_options=True")
    print("    )")
    print("    ")
    print("    # 根据用户选择决定是否继续")
    print("    if choice == 'skip':")
    print("        logging.info('用户选择跳过，停止生成翻译文件')")
    print("        return")
    print("    ")
    print("    # 继续执行导出逻辑")
    print("    logging.info(f'使用 {choice} 模式导出翻译文件')")
    print("    ")
    print("    # 根据模式调整导出行为")
    print("    if choice == 'merge':")
    print("        # 合并模式：保留现有翻译")
    print("        export_with_merge(output_dir, translations)")
    print("    else:")
    print("        # 其他模式：正常导出")
    print("        export_normal(output_dir, translations)")
    print("```\n")

def main():
    """主演示函数"""
    
    demo_all_modes()
    demo_usage_examples()
    demo_best_practices()
    demo_integration_example()
    
    print("🎉 演示完成！")
    print("\n📚 总结：")
    print("handle_existing_translations_choice 函数现在提供了 6 种处理方式，")
    print("可以满足从简单到复杂的各种翻译文件管理需求。")
    print("通过合理选择处理模式，可以大大提升翻译工作的效率和安全性。")

if __name__ == "__main__":
    main()
