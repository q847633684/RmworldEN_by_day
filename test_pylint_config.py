#!/usr/bin/env python3
"""测试Pylint配置文件"""

# 这些变量名应该会触发C0103 invalid-name错误（如果配置未生效）
A = 1  # 单字母变量名
B = 2  # 单字母变量名
myVarName = "测试"  # camelCase变量名


def testFunction():  # camelCase函数名
    """测试函数"""
    return A + B


class testClass:  # 小写类名
    """测试类"""

    def __init__(self):
        self.X = 10  # 单字母属性名
