"""
GameTrad交易系统 - PyQt6版本启动脚本
"""
import sys
import os

# 确保可以导入src_qt模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from PyQt6.QtWidgets import QApplication
from src_qt.utils.ui_manager import UIManager
from src_qt.gui.main_window import GameTradingSystemGUI

if __name__ == "__main__":
    print("启动GameTrad应用程序...")
    app = QApplication(sys.argv)
    
    print("创建UI管理器...")
    # 创建UI管理器并应用样式
    ui_manager = UIManager()
    
    print("应用现代样式...")
    ui_manager.apply_modern_style(app)
    
    print("应用全局字体设置...")
    ui_manager.apply_global_font(app)  # 应用全局字体设置
    
    print("创建主窗口...")
    # 创建主窗口
    main_window = GameTradingSystemGUI()
    main_window.show()
    
    print("开始事件循环...")
    sys.exit(app.exec()) 