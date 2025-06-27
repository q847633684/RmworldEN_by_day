#!/usr/bin/env python3
"""
修复 day_translation 目录中的 trailing whitespace 问题
"""
import os
import re

def fix_trailing_whitespace(file_path):
    """修复文件中的 trailing whitespace"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复 trailing whitespace
        lines = content.split('\n')
        fixed_lines = []
        changes = 0
        
        for i, line in enumerate(lines):
            original_line = line
            # 移除行尾空白字符
            line = line.rstrip()
            if line != original_line:
                changes += 1
                print(f"  第 {i+1} 行: 移除了 {len(original_line) - len(line)} 个尾部空白字符")
            fixed_lines.append(line)
        
        # 确保文件以换行符结尾
        if fixed_lines and fixed_lines[-1]:
            fixed_lines.append('')
        
        if changes > 0:
            fixed_content = '\n'.join(fixed_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ 修复了 {changes} 处 trailing whitespace")
            return True
        else:
            print("✅ 无需修复")
            return False
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

def main():
    """主函数"""
    base_dir = "day_translation"
    if not os.path.exists(base_dir):
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    python_files = []
    for root, dirs, files in os.walk(base_dir):
        # 跳过 __pycache__ 目录
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 个 Python 文件")
    
    total_fixed = 0
    for file_path in python_files:
        print(f"\n处理文件: {file_path}")
        if fix_trailing_whitespace(file_path):
            total_fixed += 1
    
    print(f"\n🎉 完成！总共修复了 {total_fixed} 个文件")

if __name__ == "__main__":
    main()
