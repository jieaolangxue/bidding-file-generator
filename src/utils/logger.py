"""
日志模块

提供统一的日志配置与管理
"""

import os
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


class LoggerManager:
    """日志管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._setup_logger()

    def _setup_logger(self, log_level="INFO", log_dir="./data/logs"):
        """
        配置日志系统

        Args:
            log_level (str): 日志级别
            log_dir (str): 日志输出目录
        """
        # 移除默认处理器
        logger.remove()

        # 创建日志目录
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # 日志格式
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

        # 控制台输出
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=True,
        )

        # 文件输出
        log_file = os.path.join(
            log_dir,
            f"bidding_{datetime.now().strftime('%Y%m%d')}.log"
        )
        logger.add(
            log_file,
            format=log_format,
            level=log_level,
            rotation="500 MB",
            retention="30 days",
        )

    def get_logger(self):
        """获取logger实例"""
        return logger


def setup_logger(log_level="INFO", log_dir="./data/logs"):
    """
    初始化日志系统

    Usage:
        from src.utils import setup_logger
        logger = setup_logger()
    """
    manager = LoggerManager()
    manager._setup_logger(log_level, log_dir)
    return manager.get_logger()
