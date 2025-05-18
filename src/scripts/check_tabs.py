import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QApplication
from src.scripts.migrate_data_gui import MigrationGUI

def check_tabs():
    """检查数据迁移工具中的标签页"""
    app = QApplication(sys.argv)
    window = MigrationGUI()
    
    # 获取标签页数量
    tab_count = window.tabs.count()
    print(f"标签页数量: {tab_count}")
    
    # 获取每个标签页的名称
    tab_names = []
    for i in range(tab_count):
        tab_names.append(window.tabs.tabText(i))
    
    print(f"标签页名称: {tab_names}")
    
    return tab_count, tab_names

if __name__ == "__main__":
    check_tabs() 