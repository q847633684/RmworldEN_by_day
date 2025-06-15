"""
测试配置文件
"""
import os
from pathlib import Path

# 测试用的模组目录（请根据实际情况修改）
TEST_MOD_DIRS = [
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\123456789",  # 示例模组路径
    r"D:\Games\RimWorld\Mods\TestMod",  # 本地模组路径示例
]

# 测试输出目录
TEST_OUTPUT_DIR = str(Path(__file__).parent / "test_output")

# 测试用 CSV 文件
TEST_CSV_FILES = [
    str(Path(__file__).parent / "test_output" / "extracted_translations.csv"),
    str(Path(__file__).parent / "test_output" / "translated_zh.csv"),
]

def get_valid_test_mod() -> str:
    """获取一个有效的测试模组目录"""
    for mod_dir in TEST_MOD_DIRS:
        if os.path.exists(mod_dir):
            print(f"找到测试模组: {mod_dir}")
            return mod_dir
    
    # 如果没有预设的模组，让用户手动输入
    print("未找到预设的测试模组目录")
    while True:
        mod_dir = input("请输入一个有效的模组目录进行测试: ").strip()
        if os.path.exists(mod_dir):
            return mod_dir
        print(f"目录不存在: {mod_dir}")

def ensure_test_dirs():
    """确保测试目录存在"""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    print(f"测试输出目录: {TEST_OUTPUT_DIR}")
