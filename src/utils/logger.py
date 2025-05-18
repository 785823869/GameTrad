#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志系统 - 提供全局日志记录功能，支持控制台和文件双重输出
"""
import os
import sys
import logging
import datetime
from logging.handlers import RotatingFileHandler

# 全局日志对象
_logger = None

def setup_logger(name="GameTrad", log_level=logging.INFO, debug=False):
    """
    设置日志系统
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        debug: 是否启用调试模式
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # 如果启用调试模式，覆盖日志级别
    if debug:
        log_level = logging.DEBUG
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除已有的处理器
    logger.handlers = []
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器
    try:
        from src.utils.path_resolver import get_log_dir
        log_dir = get_log_dir()
        
        # 按日期生成日志文件名
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"game_trad_{today}.log")
        
        # 使用RotatingFileHandler，限制文件大小
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # 文件日志格式更详细
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 记录系统环境信息（仅在文件日志中）
        file_handler.setLevel(logging.DEBUG)  # 文件始终记录所有级别的日志
        logger.debug("=== 系统环境信息 ===")
        logger.debug(f"Python版本: {sys.version}")
        logger.debug(f"操作系统: {sys.platform}")
        logger.debug(f"日志目录: {log_dir}")
        logger.debug(f"日志文件: {log_file}")
        logger.debug(f"调试模式: {debug}")
        logger.debug("===================")
        
    except Exception as e:
        # 日志文件创建失败时，仅使用控制台日志
        logger.warning(f"无法创建日志文件: {e}")
    
    _logger = logger
    return logger

def get_logger():
    """
    获取已配置的日志记录器，如果未配置则返回基本日志记录器
    
    Returns:
        logging.Logger: 日志记录器
    """
    global _logger
    
    if _logger is None:
        return setup_logger()
    
    return _logger

class LoggerAdapter(logging.LoggerAdapter):
    """
    日志适配器，用于添加上下文信息
    
    可用于在特定模块中添加前缀或额外信息
    """
    def __init__(self, logger, prefix=""):
        super().__init__(logger, {})
        self.prefix = prefix
    
    def process(self, msg, kwargs):
        if self.prefix:
            return f"[{self.prefix}] {msg}", kwargs
        return msg, kwargs

def get_module_logger(module_name):
    """
    获取带有模块名称前缀的日志记录器
    
    Args:
        module_name: 模块名称，通常使用__name__
        
    Returns:
        LoggerAdapter: 带有模块名称前缀的日志适配器
    """
    logger = get_logger()
    return LoggerAdapter(logger, module_name.split('.')[-1])

def log_exceptions(func):
    """
    装饰器: 捕获并记录函数中的异常
    
    用法:
    @log_exceptions
    def some_function():
        ...
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger()
            import traceback
            logger.error(f"函数 {func.__name__} 执行出错: {e}")
            logger.debug(f"详细错误: {traceback.format_exc()}")
            raise  # 重新抛出异常
    return wrapper 