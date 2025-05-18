#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
路径解析工具 - 解决打包环境和开发环境中的路径差异问题
"""
import os
import sys
import tempfile
import appdirs
from pathlib import Path

# 全局缓存常用路径，避免重复计算
_APP_ROOT = None
_DATA_DIR = None
_CONFIG_DIR = None
_LOG_DIR = None
_USER_DATA_DIR = None
_APP_NAME = "GameTrad"

def is_frozen():
    """检查应用程序是否已打包（冻结）"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_app_root():
    """
    获取应用程序根目录
    - 在打包环境中，返回PyInstaller的_MEIPASS临时解压目录
    - 在开发环境中，返回项目根目录
    """
    global _APP_ROOT
    if _APP_ROOT is not None:
        return _APP_ROOT
    
    # 如果是打包环境
    if is_frozen():
        _APP_ROOT = getattr(sys, '_MEIPASS')
    else:
        # 开发环境 - 查找项目根目录
        current_file = os.path.abspath(__file__)
        # 向上查找两层目录，从src/utils到项目根目录
        _APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # 确保目录存在
    if not os.path.exists(_APP_ROOT):
        raise FileNotFoundError(f"应用程序根目录不存在: {_APP_ROOT}")
    
    return _APP_ROOT

def get_data_dir():
    """
    获取数据目录
    - 在打包环境中，位于安装目录下的data文件夹
    - 在开发环境中，位于项目根目录下的data文件夹
    """
    global _DATA_DIR
    if _DATA_DIR is not None:
        return _DATA_DIR
    
    _DATA_DIR = os.path.join(get_app_root(), "data")
    
    # 确保目录存在
    if not os.path.exists(_DATA_DIR):
        try:
            os.makedirs(_DATA_DIR, exist_ok=True)
        except OSError:
            # 如果无法创建，使用临时目录
            _DATA_DIR = os.path.join(tempfile.gettempdir(), _APP_NAME, "data")
            os.makedirs(_DATA_DIR, exist_ok=True)
    
    return _DATA_DIR

def get_user_config_dir():
    """
    获取用户配置目录
    - 在任何环境下，都使用系统的标准用户配置目录
    - Windows: %APPDATA%\GameTrad
    - Mac: ~/Library/Application Support/GameTrad
    - Linux: ~/.config/GameTrad
    """
    global _CONFIG_DIR
    if _CONFIG_DIR is not None:
        return _CONFIG_DIR
    
    # 使用appdirs库获取标准配置目录
    _CONFIG_DIR = appdirs.user_config_dir(_APP_NAME)
    
    # 确保目录存在
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    
    return _CONFIG_DIR

def get_log_dir():
    """
    获取日志目录
    - 在任何环境下，都使用系统的标准日志目录
    """
    global _LOG_DIR
    if _LOG_DIR is not None:
        return _LOG_DIR
    
    # 在项目根目录或用户数据目录下创建logs目录
    if is_frozen():
        # 打包环境使用用户数据目录
        _LOG_DIR = os.path.join(appdirs.user_log_dir(_APP_NAME), "logs")
    else:
        # 开发环境使用项目根目录
        _LOG_DIR = os.path.join(get_app_root(), "logs")
    
    # 确保目录存在
    os.makedirs(_LOG_DIR, exist_ok=True)
    
    return _LOG_DIR

def get_user_data_dir():
    """
    获取用户数据目录，用于存储数据库和用户生成的内容
    - 使用系统标准的用户数据目录
    """
    global _USER_DATA_DIR
    if _USER_DATA_DIR is not None:
        return _USER_DATA_DIR
    
    # 使用appdirs库获取标准数据目录
    _USER_DATA_DIR = appdirs.user_data_dir(_APP_NAME)
    
    # 确保目录存在
    os.makedirs(_USER_DATA_DIR, exist_ok=True)
    
    return _USER_DATA_DIR

def resolve_path(relative_path):
    """
    解析相对路径，转换为绝对路径
    - 如果提供的是绝对路径，则直接返回
    - 如果是相对路径，则基于应用根目录解析
    
    Args:
        relative_path: 相对路径或绝对路径
        
    Returns:
        str: 解析后的绝对路径
    """
    if os.path.isabs(relative_path):
        return relative_path
    
    # 将Windows风格的路径分隔符统一转换为当前系统格式
    clean_path = relative_path.replace('\\', os.sep).replace('/', os.sep)
    
    # 基于应用根目录解析路径
    resolved_path = os.path.normpath(os.path.join(get_app_root(), clean_path))
    
    return resolved_path

def get_database_path(db_name="game_trading.db"):
    """
    获取数据库文件路径
    - 在开发环境中，使用data/database目录
    - 在打包环境中，使用用户数据目录
    
    Args:
        db_name: 数据库文件名
        
    Returns:
        str: 数据库文件的绝对路径
    """
    if is_frozen():
        # 打包环境 - 使用用户数据目录
        db_dir = os.path.join(get_user_data_dir(), "database")
    else:
        # 开发环境 - 使用项目数据目录
        db_dir = os.path.join(get_data_dir(), "database")
    
    # 确保目录存在
    os.makedirs(db_dir, exist_ok=True)
    
    return os.path.join(db_dir, db_name)

def get_temp_dir():
    """
    获取临时目录，用于存储临时文件
    
    Returns:
        str: 临时目录的绝对路径
    """
    temp_dir = os.path.join(tempfile.gettempdir(), _APP_NAME)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def migrate_config_to_user_dir():
    """
    将配置文件从旧位置迁移到新的用户配置目录
    - 用于兼容性处理，确保从旧版本升级的用户能继承原有配置
    """
    old_config_path = os.path.join(get_app_root(), "server_chan_config.json")
    new_config_path = os.path.join(get_user_config_dir(), "server_chan_config.json")
    
    # 如果旧配置存在且新配置不存在，则进行迁移
    if os.path.exists(old_config_path) and not os.path.exists(new_config_path):
        try:
            import shutil
            shutil.copy2(old_config_path, new_config_path)
            print(f"成功迁移配置文件: {old_config_path} -> {new_config_path}")
        except Exception as e:
            print(f"迁移配置文件失败: {e}")

def list_resources(directory=None):
    """
    列出指定目录下的所有资源文件，用于调试
    
    Args:
        directory: 相对于应用根目录的路径，如果为None则列出根目录
        
    Returns:
        list: 资源文件路径列表
    """
    base_dir = get_app_root()
    if directory:
        dir_path = os.path.join(base_dir, directory)
    else:
        dir_path = base_dir
    
    if not os.path.exists(dir_path):
        return []
    
    result = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            result.append(rel_path)
    
    return result

def get_config_path(config_name):
    """
    获取配置文件的绝对路径
    
    Args:
        config_name: 配置文件名
        
    Returns:
        str: 配置文件的绝对路径
    """
    return os.path.join(get_user_config_dir(), config_name)

# 在模块初始化时进行配置迁移
migrate_config_to_user_dir() 