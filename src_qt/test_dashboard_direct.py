"""
直接测试仪表盘卡片组件
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

# 导入卡片组件
sys.path.insert(0, 'D:/xiaoming/GameTrad')
from src_qt.utils.dashboard_cards import MetricCard, ChartCard, TableCard, UserListCard
from src_qt.utils.matplotlib_chart import LineChart

def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("仪表盘卡片测试")
    main_window.resize(800, 600)
    
    # 创建中心部件
    central_widget = QWidget()
    central_widget.setStyleSheet("background-color: #f8f9fa;")
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(20)
    
    # 创建卡片
    metric_card = MetricCard(central_widget, "总收入", "¥45,678.90", "+20% 月环比", True)
    layout.addWidget(metric_card)
    
    chart_card = ChartCard(central_widget, "销售趋势", LineChart, 
                        {"title": "", "figsize": (5, 3), "toolbar": False})
    layout.addWidget(chart_card)
    
    # 设置中心部件
    main_window.setCentralWidget(central_widget)
    
    # 显示窗口
    main_window.show()
    
    # 启动事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 