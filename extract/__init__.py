"""
RimWorld 翻译提取模块

本模块提供完整的 RimWorld 模组翻译提取功能，包括：
- 从 Defs 目录扫描可翻译内容
- 从 DefInjected/Keyed 目录提取现有翻译
- 智能合并和冲突处理
- 多种模板结构导出
- CSV 格式数据导出

主要组件：
- extractors: 翻译内容提取器
- exporters: 翻译文件导出器
- filters: 内容过滤器
- smart_merger: 智能合并器
- template_manager: 模板管理器
- interaction_manager: 交互管理器
- handler: 主处理流程

注意：为避免循环导入，模块内部采用延迟导入策略
"""
