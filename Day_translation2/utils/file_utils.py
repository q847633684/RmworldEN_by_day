"""
Day Translation 2 - 文件工具模块

提供文件和路径操作的通用功能。
遵循提示文件标准：PEP 8规范、具体异常处理、用户友好错误信息。
"""

import os
from pathlib import Path
from typing import List, Optional

try:
    from ..models.exceptions import ImportError as TranslationImportError
    from ..models.exceptions import ValidationError
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.exceptions import ImportError as TranslationImportError
    from models.exceptions import ValidationError


def get_language_folder_path(language: str, mod_dir: str) -> str:
    """
    获取模组的语言文件夹路径

    Args:
        language: 语言代码 (如 "English", "ChineseSimplified")
        mod_dir: 模组目录路径

    Returns:
        语言文件夹的完整路径

    Raises:
        ValidationError: 当参数无效时
        TranslationImportError: 当路径不存在时
    """
    if not language:
        raise ValidationError(
            "语言代码不能为空", field_name="language", expected_type="非空字符串"
        )

    if not mod_dir:
        raise ValidationError(
            "模组目录不能为空", field_name="mod_dir", expected_type="有效目录路径"
        )

    try:
        mod_path = Path(mod_dir)
        if not mod_path.exists():
            raise TranslationImportError(
                f"模组目录不存在: {mod_dir}", file_path=mod_dir
            )

        lang_path = mod_path / "Languages" / language
        return str(lang_path)

    except Exception as e:
        if isinstance(e, (ValidationError, TranslationImportError)):
            raise
        raise TranslationImportError(
            f"获取语言文件夹路径失败: {str(e)}", file_path=mod_dir
        )


def ensure_directory_exists(directory_path: str) -> None:
    """
    确保目录存在，不存在则创建

    Args:
        directory_path: 目录路径

    Raises:
        TranslationImportError: 当创建目录失败时
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise TranslationImportError(
            f"创建目录失败: {str(e)}", file_path=directory_path
        )


def get_xml_files(directory: str, recursive: bool = True) -> List[str]:
    """
    获取目录中的所有XML文件

    Args:
        directory: 目录路径
        recursive: 是否递归搜索子目录

    Returns:
        XML文件路径列表

    Raises:
        TranslationImportError: 当目录不存在时
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise TranslationImportError(
                f"目录不存在: {directory}", file_path=directory
            )

        if recursive:
            xml_files = list(dir_path.rglob("*.xml"))
        else:
            xml_files = list(dir_path.glob("*.xml"))

        return [str(f) for f in xml_files]

    except Exception as e:
        if isinstance(e, TranslationImportError):
            raise
        raise TranslationImportError(
            f"获取XML文件列表失败: {str(e)}", file_path=directory
        )


def validate_mod_directory(mod_dir: str) -> bool:
    """
    验证模组目录结构是否有效

    Args:
        mod_dir: 模组目录路径

    Returns:
        是否为有效的模组目录

    Raises:
        ValidationError: 当目录结构无效时
    """
    try:
        mod_path = Path(mod_dir)

        if not mod_path.exists():
            raise ValidationError(
                f"模组目录不存在: {mod_dir}", field_name="mod_dir", actual_value=mod_dir
            )

        if not mod_path.is_dir():
            raise ValidationError(
                f"路径不是目录: {mod_dir}", field_name="mod_dir", actual_value=mod_dir
            )

        # 检查是否包含必要的子目录
        has_defs = (mod_path / "Defs").exists()
        has_languages = (mod_path / "Languages").exists()

        if not (has_defs or has_languages):
            raise ValidationError(
                f"目录不包含Defs或Languages文件夹，可能不是有效的模组目录: {mod_dir}",
                field_name="mod_dir",
                actual_value=mod_dir,
            )

        return True

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            f"验证模组目录失败: {str(e)}", field_name="mod_dir", actual_value=mod_dir
        )
