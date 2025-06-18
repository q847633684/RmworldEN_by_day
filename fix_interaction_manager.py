#!/usr/bin/env python3
"""
修复 interaction_manager.py 中的 path_manager 调用
"""

import re

# 读取文件
file_path = "day_translation/utils/interaction_manager.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有path_manager调用为preferences_manager
content = content.replace("self.path_manager.get_path(", "self.preferences_manager.get_path_with_validation(")
content = content.replace("self.path_manager.get_remembered_path(", "self.preferences_manager.get_remembered_path(")

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成")
