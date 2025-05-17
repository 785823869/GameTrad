"""
屏幕截图工具 - 用于捕获应用程序界面
"""
import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication, QScreen
from datetime import datetime

def take_screenshot(save_path=None):
    """
    捕获当前屏幕内容并保存
    
    参数:
    save_path (str, optional): 保存路径，默认为当前时间戳命名的文件
    
    返回:
    str: 保存的文件路径
    """
    # 获取当前屏幕
    screen = QGuiApplication.primaryScreen()
    if not screen:
        print("无法获取主屏幕")
        return None
    
    # 捕获屏幕内容
    pixmap = screen.grabWindow(0)
    
    # 生成保存路径
    if not save_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"screenshot_{timestamp}.png"
    
    # 保存截图
    if pixmap.save(save_path):
        print(f"屏幕截图已保存至: {os.path.abspath(save_path)}")
        return os.path.abspath(save_path)
    else:
        print("保存截图失败")
        return None

if __name__ == "__main__":
    # 创建QApplication实例，如果不存在的话
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # 捕获屏幕截图
    take_screenshot() 