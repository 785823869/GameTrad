#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试仪表盘组件
"""
import sys
import os

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QMainWindow
from src_qt.utils.ui_manager import UIManager
from src_qt.gui.tabs.dashboard_tab import DashboardTab

def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建UI管理器
    ui_manager = UIManager()
    ui_manager.setup_fonts()
    ui_manager.setup_colors()
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("仪表盘测试")
    main_window.resize(1200, 800)
    
    # 创建一个模拟的主GUI对象
    class MockMainGUI:
        def __init__(self):
            self.ui_manager = ui_manager
    
    mock_main_gui = MockMainGUI()
    
    # 创建仪表盘标签页
    dashboard = DashboardTab(main_window, mock_main_gui)
    main_window.setCentralWidget(dashboard)
    
    # 显示窗口
    main_window.show()
    
    # 打印一些调试信息
    print(f"Python路径: {sys.path}")
    print(f"当前目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")
    
    # 启动事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    # 打印导入路径
    print(f"Python路径: {sys.path}")
    print(f"当前目录: {os.getcwd()}")
    print(f"脚本位置: {current_dir}")
    print(f"项目根目录: {project_root}")
    
    main() 