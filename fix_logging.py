#!/usr/bin/env python3
"""
批量修复日志格式化问题 - 将所有 f-string 日志替换为 % 格式化
正确处理多个变量的混合格式情况
"""
import os
import re
from pathlib import Path

def fix_logging_in_file(file_path):
    """修复单个文件中的日志格式问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 定义需要修复的模式和替换规则
        fixes = [
            # 处理 f-string 中包含多个变量的情况，包括带额外参数的
            # logging.error(f"text {var}", exc_info=True) -> logging.error("text %s", var, exc_info=True)
            {
                'pattern': r'logging\.(info|debug|warning|error|critical)\(f"([^"]*?)"([^)]*?)\)',
                'handler': fix_f_string_with_variables_and_args
            },
            
            # 处理已经部分修复但仍有问题的混合格式
            # logging.error("text %s: {var}", param) -> logging.error("text %s: %s", param, var)
            {
                'pattern': r'logging\.(info|debug|warning|error|critical)\("([^"]*?)\{([^}]+)\}([^"]*?)"([^)]*?)\)',
                'handler': fix_mixed_format
            },
        ]
        
        changes_made = False
        
        for fix in fixes:
            matches = list(re.finditer(fix['pattern'], content))
            for match in reversed(matches):  # 从后往前替换避免位置偏移
                new_text = fix['handler'](match)
                if new_text != match.group(0):
                    content = content[:match.start()] + new_text + content[match.end():]
                    changes_made = True
        
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 修复: {file_path}")
            return True
        else:
            print(f"- 跳过: {file_path} (无需修复)")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {file_path} - {e}")
        return False

def fix_f_string_with_variables_and_args(match):
    """处理 f-string 中包含变量和额外参数的情况"""
    level = match.group(1)
    f_string = match.group(2)
    extra_args = match.group(3)
    
    # 查找所有的 {variable} 模式
    variables = re.findall(r'\{([^}]*?)\}', f_string)
    
    if not variables:
        # 没有变量，只需要去掉 f
        if extra_args.strip():
            return f'logging.{level}("{f_string}"{extra_args})'
        else:
            return f'logging.{level}("{f_string}")'
    
    # 有变量，转换为 % 格式
    format_string = f_string
    for var in variables:
        # 将 {variable} 替换为 %s
        format_string = format_string.replace(f'{{{var}}}', '%s', 1)
    
    # 构造参数列表
    var_list = ', '.join(variables)
    if extra_args.strip():
        return f'logging.{level}("{format_string}", {var_list}{extra_args})'
    else:
        return f'logging.{level}("{format_string}", {var_list})'

def fix_f_string_with_variables(match):
    """处理 f-string 中包含变量的情况"""
    level = match.group(1)
    f_string = match.group(2)
    
    # 查找所有的 {variable} 模式
    variables = re.findall(r'\{([^}]*?)\}', f_string)
    
    if not variables:
        # 没有变量，只需要去掉 f
        return f'logging.{level}("{f_string}")'
    
    # 有变量，转换为 % 格式
    format_string = f_string
    for var in variables:
        # 将 {variable} 替换为 %s
        format_string = format_string.replace(f'{{{var}}}', '%s', 1)
    
    # 构造参数列表
    var_list = ', '.join(variables)
    return f'logging.{level}("{format_string}", {var_list})'

def fix_mixed_format(match):
    """处理混合格式的情况"""
    level = match.group(1)
    pre_text = match.group(2)
    variable = match.group(3)
    post_text = match.group(4)
    existing_args = match.group(5)
    
    # 构造完整的格式字符串
    format_string = f"{pre_text}%s{post_text}"
    
    # 处理现有参数
    if existing_args.strip():
        # 有现有参数，添加新变量
        args = f"{existing_args.strip()}, {variable}"
    else:
        # 没有现有参数
        args = f", {variable}"
    
    return f'logging.{level}("{format_string}"{args})'

def main():
    """批量修复项目中的所有 Python 文件"""
    project_root = Path(__file__).parent
    
    # 只修复 day_translation 目录
    py_files = list(project_root.glob("day_translation/**/*.py"))
    
    print(f"找到 {len(py_files)} 个 Python 文件")
    print("开始修复日志格式化问题...\n")
    
    fixed_count = 0
    for py_file in py_files:
        if fix_logging_in_file(py_file):
            fixed_count += 1
    
    print(f"\n总结: 修复了 {fixed_count} 个文件")
    
    # 验证修复效果
    print("\n验证修复效果...")
    remaining_issues = check_remaining_issues(py_files)
    if remaining_issues:
        print(f"⚠️  仍有 {len(remaining_issues)} 个问题需要手动修复:")
        for issue in remaining_issues[:5]:  # 只显示前5个
            print(f"  - {issue}")
        if len(remaining_issues) > 5:
            print(f"  ... 还有 {len(remaining_issues) - 5} 个问题")
    else:
        print("✅ 所有日志格式化问题已修复！")

def check_remaining_issues(py_files):
    """检查剩余的问题"""
    issues = []
    
    patterns_to_check = [
        r'logging\.(info|debug|warning|error|critical)\(f"',  # f-string 日志
        r'logging\.(info|debug|warning|error|critical)\("[^"]*?\{[^}]+\}',  # 混合格式
    ]
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in patterns_to_check:
                matches = re.findall(pattern, content)
                if matches:
                    issues.append(f"{py_file}: {len(matches)} 个问题")
        except Exception:
            continue
    
    return issues

if __name__ == "__main__":
    main()
