#!/usr/bin/env python3
"""
修复 Python 文件中的 trailing whitespace 问题
"""
import os
import re
from pathlib import Path

def fix_trailing_whitespace_in_file(file_path: Path) -> bool:
    """修复单个文件的 trailing whitespace"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存原始内容用于比较
        original_content = content
        
        # 修复 trailing whitespace
        lines = content.splitlines()
        fixed_lines = [line.rstrip() for line in lines]
        
        # 确保文件以换行符结尾
        fixed_content = '\n'.join(fixed_lines) + '\n'
        
        # 如果内容有变化，写回文件
        if fixed_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"已修复: {file_path}")
            return True
        else:
            print(f"无需修复: {file_path}")
            return False
    except Exception as e:
        print(f"修复失败 {file_path}: {e}")
        return False

def fix_trailing_whitespace_in_directory(directory: Path) -> int:
    """修复目录中所有 Python 文件的 trailing whitespace"""
    fixed_count = 0
    
    # 查找所有 Python 文件
    python_files = list(directory.rglob("*.py"))
    
    print(f"找到 {len(python_files)} 个 Python 文件")
    
    for file_path in python_files:
        if fix_trailing_whitespace_in_file(file_path):
            fixed_count += 1
    
    return fixed_count

if __name__ == "__main__":
    # 设置工作目录
    base_dir = Path(r"c:\Users\q8476\Documents\我的工作\Day_汉化\day_translation")
    
    print(f"开始修复 {base_dir} 目录中的 trailing whitespace...")
    
    fixed_count = fix_trailing_whitespace_in_directory(base_dir)
    
    print(f"\n修复完成！共修复了 {fixed_count} 个文件")
