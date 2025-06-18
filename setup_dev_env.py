"""Day汉化项目开发环境配置脚本

按照提示文件标准配置代码质量工具
"""
import subprocess
import sys
from pathlib import Path


def install_dev_tools():
    """安装开发工具"""
    tools = [
        'black',      # 代码格式化
        'pylint',     # 静态检查  
        'mypy',       # 类型检查
        'pytest',     # 测试框架
        'pytest-cov' # 测试覆盖率
    ]
    
    for tool in tools:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', tool], 
                         check=True)
            print(f"✅ {tool} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {tool} 安装失败")


def create_config_files():
    """创建配置文件"""
    project_root = Path(__file__).parent
    
    # black配置
    pyproject_toml = project_root / "pyproject.toml"
    if not pyproject_toml.exists():
        with open(pyproject_toml, 'w', encoding='utf-8') as f:
            f.write("""[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
""")
        print("✅ pyproject.toml 创建成功")
    
    # pytest配置
    pytest_ini = project_root / "pytest.ini"
    if not pytest_ini.exists():
        with open(pytest_ini, 'w', encoding='utf-8') as f:
            f.write("""[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov-report=html --cov-report=term
""")
        print("✅ pytest.ini 创建成功")


if __name__ == "__main__":
    print("🔧 配置Day汉化项目开发环境...")
    install_dev_tools()
    create_config_files()
    print("✅ 开发环境配置完成！")
