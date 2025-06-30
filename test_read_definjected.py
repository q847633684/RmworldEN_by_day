"""
测试 _read_existing_definjected_files 函数的实现
验证是否正确提取ekey、etest、eEN
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from day_translation.extract.template_manager import TemplateManager
from day_translation.utils.utils import XMLProcessor

def test_read_existing_files():
    """测试读取现有DefInjected文件"""
    
    # 初始化
    manager = TemplateManager()
    
    # 测试目录（使用实际的DefInjected文件）
    test_dir = r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\rjw\1.5\Languages\ChineseSimplified\DefInjected"
    
    if not os.path.exists(test_dir):
        print(f"测试目录不存在: {test_dir}")
        return
    
    # 只测试一个子目录，避免过多输出
    backstory_dir = os.path.join(test_dir, "BackstoryDefDefs")
    
    if not os.path.exists(backstory_dir):
        print(f"BackstoryDefDefs目录不存在: {backstory_dir}")
        return
    
    print(f"测试读取目录: {backstory_dir}")
    
    # 调用函数
    result = manager._read_existing_definjected_files(backstory_dir)
    
    print(f"\n=== 读取结果统计 ===")
    print(f"文件数量: {len(result)}")
    
    for file_path, file_data in result.items():
        relative_path = file_data['relative_path']
        translation_count = len(file_data['translations'])
        print(f"\n文件: {relative_path}")
        print(f"翻译条目数: {translation_count}")
        
        # 显示前几个翻译条目的详细信息
        count = 0
        for ekey, data in file_data['translations'].items():
            if count >= 3:  # 只显示前3个
                break
            
            etest = data['etest'][:50] + "..." if len(data['etest']) > 50 else data['etest']
            eEN = data['eEN'][:50] + "..." if len(data['eEN']) > 50 else data['eEN']
            
            print(f"  键名: {ekey}")
            print(f"  翻译: {etest}")
            print(f"  英文: {eEN}")
            print(f"  ---")
            count += 1
        
        if translation_count > 3:
            print(f"  ... 还有 {translation_count - 3} 个条目")

if __name__ == "__main__":
    test_read_existing_files()
