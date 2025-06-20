#!/usr/bin/env python3
"""
移除Python文件中的尾随空格
"""
import glob
import os


def remove_trailing_whitespace():
    """移除所有Python文件的尾随空格"""
    count = 0
    for filepath in glob.glob("**/*.py", recursive=True):
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # 移除尾随空格并确保文件以换行符结尾
                cleaned_content = content.rstrip() + "\n"

                # 只有内容发生变化时才写入
                if cleaned_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(cleaned_content)
                    count += 1
                    print(f"已清理: {filepath}")

            except Exception as e:
                print(f"处理文件 {filepath} 时出错: {e}")

    print(f"共处理了 {count} 个文件")


if __name__ == "__main__":
    remove_trailing_whitespace()
