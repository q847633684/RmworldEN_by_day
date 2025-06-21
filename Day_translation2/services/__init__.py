"""
Day Translation 2 - 服务层

提供独立的业务服务，支持核心业务逻辑。
包括机器翻译、批量处理、验证、语料生成等服务。
"""

import sys
from pathlib import Path

# 绝对导入项目内服务模块
from services.batch_processor import BatchProcessor
from services.config_service import ConfigService
from services.history_service import HistoryService, history_service
from services.path_service import PathValidationService, path_validation_service

# from services.corpus_generator import generate_parallel_corpus  # 临时注释掉避免循环导入
from services.translation_service import translate_csv
from services.user_interaction_service import (
    UserInteractionService,
    user_interaction_service,
)
from services.validation_service import TranslationValidator, validate_csv_file

# 将项目根目录添加到 sys.path，方便绝对导入
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# 创建配置服务实例
config_service = ConfigService()

__all__ = [
    # 翻译服务
    "translate_csv",
    "BatchProcessor",
    "TranslationValidator",
    "validate_csv_file",
    # "generate_parallel_corpus",  # 临时注释掉避免循环导入
    # 配置服务
    "PathValidationService",
    "ConfigService",
    "HistoryService",
    "UserInteractionService",
    # 服务单例
    "path_validation_service",
    "config_service",
    "history_service",
    "user_interaction_service",
]
