#!/usr/bin/env python3
"""
Day Translation 2 安装脚本

使用pip install -e . 进行开发安装
"""

from setuptools import setup, find_packages
import os

# 读取版本信息
version = "2.0.0"

# 读取README
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Day Translation 2 - 游戏本地化翻译工具"

# 读取依赖
requirements = [
    "colorama>=0.4.0",
    "tqdm>=4.60.0",
    "lxml>=4.6.0",
    "requests>=2.25.0",
    "pyyaml>=5.4.0",
]

# 开发依赖
dev_requirements = [
    "pytest>=6.0.0",
    "pytest-cov>=2.10.0",
    "black>=21.0.0",
    "pylint>=2.7.0",
    "mypy>=0.812",
]

setup(
    name="day-translation2",
    version=version,
    author="Day汉化项目组",
    author_email="day-translation@example.com",
    description="游戏本地化翻译工具 - 全新架构版本",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/day-translation/day-translation2",
    
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Localization",
    ],
    
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    
    entry_points={
        "console_scripts": [
            "day-translation2=Day_translation2.main:main",
        ],
    },
    
    include_package_data=True,
    zip_safe=False,
)
