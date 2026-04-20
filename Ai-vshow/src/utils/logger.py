# utils/logger.py （建议保存为独立模块）

import logging
import os
from datetime import datetime

def setup_logger(
    name: str = "vshow_auto_test",
    log_file: str = None,
    level: int = logging.INFO,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    配置一个同时输出到控制台和文件的日志记录器。

    Args:
        name (str): Logger 名称，默认为 "vshow_auto_test"
        log_file (str): 日志文件路径。若为 None，则自动生成在 logs/ 目录下
        level (int): 同时设置控制台和文件的日志级别（如果未单独指定）
        console_level (int): 控制台日志级别
        file_level (int): 文件日志级别

    Returns:
        logging.Logger: 配置好的 logger 实例
    """
    # 创建 logs 目录（如果不存在）
    if log_file is None:
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/autotest_{timestamp}.log"

    # 获取或创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置最低级别，由 handler 控制实际输出

    # 避免重复添加 handler（防止多次调用时日志重复）
    if logger.hasHandlers():
        logger.handlers.clear()

    # === 格式化器 ===
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d - %(funcName)s() | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # === 控制台处理器 ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # === 文件处理器 ===
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 全局 logger 实例（可选）
logger = setup_logger()