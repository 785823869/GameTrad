#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GameTrad - 游戏交易系统主入口文件
这个文件是程序的统一入口点，确保开发环境和打包环境使用相同的启动流程
"""
import os
import sys
import argparse
from tkinter import messagebox

# 添加当前目录到PATH，确保能正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def is_packaged():
    """
    检测是否以打包方式运行，PyInstaller打包后有特殊变量_MEIPASS
    """
    return hasattr(sys, '_MEIPASS')

def setup_environment():
    """
    设置运行环境，包括工作目录和其他必要的环境变量
    """
    # 如果是打包后的运行环境，设置工作目录
    if is_packaged():
        if hasattr(sys, '_MEIPASS'):
            os.chdir(sys._MEIPASS)
            print(f"已设置工作目录为: {sys._MEIPASS}")
        else:
            # 如果是普通打包方式运行，设置为应用程序所在目录
            os.chdir(os.path.dirname(sys.executable))
            print(f"已设置工作目录为: {os.path.dirname(sys.executable)}")
    else:
        # 在开发环境中，保持当前目录作为工作目录
        print(f"开发模式，当前工作目录: {os.getcwd()}")

def main():
    """
    程序主入口函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='GameTrad - 游戏交易系统')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    args = parser.parse_args()
    
    # 设置程序环境
    setup_environment()
    
    # 导入必要的模块
    try:
        # 导入版本信息
        from src import __version__
        
        # 如果只是查看版本信息
        if args.version:
            print(f"GameTrad - 游戏交易系统 v{__version__}")
            return 0
        
        # 初始化日志系统（日志文件位置会根据是否打包而不同）
        from src.utils.logger import setup_logger
        logger = setup_logger(debug=args.debug)
        logger.info(f"启动 GameTrad v{__version__}, 调试模式: {args.debug}")
        logger.info(f"运行环境: {'打包环境' if is_packaged() else '开发环境'}")
        logger.info(f"工作目录: {os.getcwd()}")
        
        # 导入tkinter相关模块
        import tkinter as tk
        import ttkbootstrap as tb
        from src.gui.main_window import GameTradingSystemGUI
        
        # 创建应用程序窗口
        logger.info("创建应用程序窗口")
        root = tb.Window(themename="flatly")  # 使用flatly主题
        root.title("GameTrad交易管理系统")
        root.geometry("1280x800")
        
        # 设置窗口图标
        from src.utils.path_resolver import resolve_path
        icon_path = resolve_path("data/icon.ico")
        if os.path.exists(icon_path):
            logger.info(f"设置窗口图标: {icon_path}")
            root.iconbitmap(icon_path)
        else:
            logger.warning(f"图标文件不存在: {icon_path}")
        
        # 传递调试标志给主窗口
        app = GameTradingSystemGUI(root, debug=args.debug)
        logger.info("应用程序初始化完成，开始主循环")
        root.mainloop()
        logger.info("应用程序正常退出")
        return 0
        
    except Exception as e:
        # 记录异常并显示错误消息
        import traceback
        error_msg = f"应用程序启动时发生错误: {e}\n{traceback.format_exc()}"
        print(error_msg)
        
        # 尝试记录到日志文件
        try:
            from src.utils.logger import get_logger
            logger = get_logger()
            logger.error(error_msg)
        except:
            # 如果日志系统尚未初始化，写入到临时错误日志
            error_log_path = os.path.join(current_dir, "error.log")
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"{error_msg}\n")
        
        # 显示错误消息对话框
        try:
            messagebox.showerror("启动错误", f"应用程序启动失败:\n{str(e)}\n\n详细错误信息已记录到日志文件。")
        except:
            # 如果GUI无法初始化，使用控制台输出
            print("无法显示错误对话框，请查看日志文件。")
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 