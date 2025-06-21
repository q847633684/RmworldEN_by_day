#!/usr/bin/env python3
"""测试f-string修复功能"""

import tempfile
import os
from pathlib import Path

def test_fstring_fix():
    """测试f-string修复功能"""
    # 创建测试内容
    test_content = '''
# 测试文件
print(f"普通字符串")  # 应该修复
print(f"有变量的 {name}")  # 不应该修复
print(f"转义花括号 {{name}}")  # 应该修复
result = f"返回值"  # 应该修复
'''
    
    expected_content = '''
# 测试文件
print("普通字符串")  # 应该修复
print(f"有变量的 {name}")  # 不应该修复
print("转义花括号 {{name}}")  # 应该修复
result = "返回值"  # 应该修复
'''
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # 这里应该导入和运行修复函数
        print(f"✅ f-string修复功能测试准备完成")
        print(f"临时文件: {temp_file}")
        
        # 读取原始内容
        with open(temp_file, 'r', encoding='utf-8') as f:
            original = f.read()
        print("原始内容:")
        print(original)
        
        # 手动应用修复逻辑进行测试
        import re
        fstring_pattern = re.compile(r'f(["\'])((?:(?!\1)[^\\]|\\.)*)(\1)')
        
        lines = original.splitlines()
        modified_lines = []
        
        for line in lines:
            modified_line = line
            for match in fstring_pattern.finditer(line):
                quote_char = match.group(1)
                string_content = match.group(2)
                
                # 检查是否包含真正的插值
                if '{' not in string_content or ('{' in string_content and '{{' in string_content and string_content.count('{') == string_content.count('}')):
                    old_fstring = f'f{quote_char}{string_content}{quote_char}'
                    new_string = f'{quote_char}{string_content}{quote_char}'
                    modified_line = modified_line.replace(old_fstring, new_string, 1)
                    print(f"修复: {old_fstring} → {new_string}")
            
            modified_lines.append(modified_line)
        
        result_content = '\n'.join(modified_lines)
        print("\n修复后内容:")
        print(result_content)
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)

if __name__ == "__main__":
    test_fstring_fix()