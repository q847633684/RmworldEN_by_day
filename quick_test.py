"""
快速测试脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from test_config import get_valid_test_mod, ensure_test_dirs, TEST_OUTPUT_DIR
from day_translation.core.main import TranslationFacade

def test_mode_1():
    """测试模式 1：提取翻译"""
    print("\n=== 测试模式 1：提取翻译 ===")
    
    mod_dir = get_valid_test_mod()
    ensure_test_dirs()
    
    try:
        facade = TranslationFacade(mod_dir, TEST_OUTPUT_DIR)
        
        print(f"模组目录: {facade.mod_dir}")
        print(f"导出目录: {facade.export_dir}")
        print(f"CSV 路径: {facade.csv_path}")
        
        # 测试提取功能
        translations = facade.extract_all()
        print(f"✅ 提取成功！共 {len(translations)} 条翻译")
        
        # 检查输出文件
        if os.path.exists(facade.csv_path):
            print(f"✅ CSV 文件已生成: {facade.csv_path}")
            
            # 显示前几行内容
            with open(facade.csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:6]  # 读取前5行内容
                print("\n前几行内容预览:")
                for i, line in enumerate(lines):
                    print(f"  {i+1}: {line.strip()}")
        else:
            print("❌ CSV 文件未生成")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_import_modules():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    modules_to_test = [
        "day_translation.core.main",
        "day_translation.core.extractors", 
        "day_translation.core.exporters",
        "day_translation.core.importers",
        "day_translation.core.machine_translate",
        "day_translation.core.parallel_corpus",
        "day_translation.utils.config",
        "day_translation.utils.utils",
        "day_translation.utils.fields",
    ]
    
    success_count = 0
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
        except Exception as e:
            print(f"⚠️ {module_name}: {e}")
    
    print(f"\n导入测试完成: {success_count}/{len(modules_to_test)} 成功")

def test_dependencies():
    """测试依赖项"""
    print("\n=== 测试依赖项 ===")
    
    deps = [
        ("标准库", ["csv", "json", "pathlib", "logging", "os", "sys"]),
        ("可选依赖", ["lxml", "aiofiles"]),
        ("阿里云SDK", ["aliyunsdkcore", "aliyunsdkalimt"]),
    ]
    
    for category, modules in deps:
        print(f"\n{category}:")
        for module in modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except ImportError:
                print(f"  ❌ {module} (未安装)")

def main():
    """主测试函数"""
    print("=== day_translation 快速测试 ===")
    
    while True:
        print("\n请选择测试项目:")
        print("1. 测试模块导入")
        print("2. 测试依赖项") 
        print("3. 测试模式 1 (提取翻译)")
        print("4. 运行完整程序")
        print("0. 退出")
        
        choice = input("\n请选择: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            test_import_modules()
        elif choice == "2":
            test_dependencies()
        elif choice == "3":
            test_mode_1()
        elif choice == "4":
            from day_translation.core.main import main as run_main
            run_main()
            break
        else:
            print("无效选择")
        
        input("\n按回车继续...")
    
    print("测试结束")

if __name__ == "__main__":
    main()
