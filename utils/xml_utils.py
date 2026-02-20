"""
XML 通用工具

提供与命名空间无关的标签解析等，供 RimWorld Defs、About.xml 等模块复用。
"""


def local_tag(tag) -> str:
    """去掉 XML 命名空间前缀，如 {http://...}HediffDef -> HediffDef。非字符串原样返回。"""
    if not isinstance(tag, str):
        return tag
    if "}" in tag:
        return tag.split("}", 1)[-1]
    return tag
