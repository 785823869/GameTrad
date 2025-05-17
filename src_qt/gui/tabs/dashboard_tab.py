"""
仪表盘标签页 - 显示系统概览和关键指标
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QGridLayout, QSizePolicy, QComboBox,
                            QPushButton, QSlider, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSplitter, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, QDate, QDateTime, pyqtSlot, QMargins
from PyQt6.QtGui import QColor, QPainter, QPen, QIcon
import random
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# matplotlib相关导入
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

# 配置matplotlib中文支持
try:
    import platform
    if platform.system() == 'Windows':
        matplotlib.rc('font', family='Microsoft YaHei')
    elif platform.system() == 'Darwin':  # macOS
        matplotlib.rc('font', family='PingFang SC')
    else:  # Linux等其他系统
        matplotlib.rc('font', family='WenQuanYi Micro Hei')
except:
    # 如果配置失败，使用通用设置
    matplotlib.rcParams['axes.unicode_minus'] = False

from src_qt.utils.responsive_layout import LayoutMode, WindowSizeThreshold, ResponsiveLayoutManager
from src_qt.utils.matplotlib_chart import LineChart, BarChart, PieChart, ScatterChart
from src_qt.utils.dashboard_cards import MetricCard, ChartCard, TableCard, UserListCard

class DashboardTab(QWidget):
    """仪表盘标签页，显示系统概览和关键指标"""
    
    def __init__(self, parent_frame, main_gui=None):
        """
        初始化仪表盘标签页
        
        参数:
        parent_frame -- 父框架
        main_gui -- 主GUI引用，用于访问全局资源
        """
        super().__init__(parent_frame)
        
        # 保存主窗口引用
        self.main_gui = main_gui
        self.ui_manager = main_gui.ui_manager if main_gui else None
        
        # 当前布局模式
        self.current_layout_mode = LayoutMode.NORMAL
        
        # 初始化UI
        self.init_ui()
        
        # 自动刷新定时器 (5分钟刷新一次)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # 300000毫秒 = 5分钟
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置背景色
        self.setStyleSheet("background-color: #f8f9fa;")
        
        # 确保仪表盘标签页占据所有可用空间
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # 标题区域
        self.init_header()
        
        # 创建主内容区域的网格布局
        self.content_grid = QGridLayout()
        self.content_grid.setSpacing(16)  # 卡片之间的间距
        self.main_layout.addLayout(self.content_grid, 1)  # 添加伸缩因子1，使其占据所有可用垂直空间
        
        # 初始化卡片
        self.init_cards()
        
        # 刷新数据
        self.refresh_data()
    
    def init_header(self):
        """初始化标题区域"""
        header_frame = QWidget()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QLabel("仪表盘")
        title_label.setFont(self.ui_manager.title_font if self.ui_manager else QLabel().font())
        title_label.setStyleSheet("color: #333; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label, 1)  # 1是伸缩系数
        
        # 时间范围选择
        time_range_label = QLabel("时间范围:")
        time_range_label.setStyleSheet("color: #555;")
        header_layout.addWidget(time_range_label)
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["今日", "昨日", "近7天", "近30天", "近90天"])
        self.time_range_combo.setCurrentIndex(2)  # 默认选择近7天
        self.time_range_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 8px;
                background: white;
            }
        """)
        self.time_range_combo.currentIndexChanged.connect(self.on_time_range_changed)
        header_layout.addWidget(self.time_range_combo)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(refresh_button, "small")
        else:
            refresh_button.setFixedWidth(80)
        refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_button)
        
        self.main_layout.addWidget(header_frame)
        
        # 存储要在紧凑模式下隐藏的组件
        self.compact_hide_widgets = {
            "time_range_label": time_range_label
        }
    
    def init_cards(self):
        """初始化所有仪表盘卡片，使用网格布局进行排列"""
        # 第一行：三个指标卡片，均匀排列
        self.revenue_card = MetricCard(self, "总收入", "¥0.00", "0% 月环比", True)
        self.content_grid.addWidget(self.revenue_card, 0, 0)
        
        self.inventory_card = MetricCard(self, "库存价值", "¥0.00", "0% 月环比", True)
        self.content_grid.addWidget(self.inventory_card, 0, 1)
        
        self.users_card = MetricCard(self, "活跃用户", "0", "0% 月环比", True)
        self.content_grid.addWidget(self.users_card, 0, 2)
        
        # 第二行：左侧大图表卡片，右侧用户列表卡片
        self.sales_trend_card = ChartCard(
            self, "销售趋势", 
            chart_type=LineChart,
            chart_options={"title": "", "figsize": (8, 4), "toolbar": False}
        )
        self.content_grid.addWidget(self.sales_trend_card, 1, 0, 1, 2)  # 跨越2列
        
        self.users_list_card = UserListCard(self, "热门用户")
        self.content_grid.addWidget(self.users_list_card, 1, 2)
        
        # 第三行：左侧表格卡片，右侧柱状图卡片
        self.source_table_card = TableCard(self, "流量来源", ["来源", "会话", "变化"])
        self.content_grid.addWidget(self.source_table_card, 2, 0)
        
        self.monthly_sales_card = ChartCard(
            self, "月度销售", 
            chart_type=BarChart,
            chart_options={"title": "", "figsize": (5, 4), "toolbar": False}
        )
        self.content_grid.addWidget(self.monthly_sales_card, 2, 1, 1, 2)  # 跨越2列
        
        # 设置行列伸缩因子，以确保正确的比例
        for i in range(3):  # 3列
            self.content_grid.setColumnStretch(i, 1)
        
        # 第二行和第三行比第一行高
        self.content_grid.setRowStretch(0, 1)
        self.content_grid.setRowStretch(1, 3)
        self.content_grid.setRowStretch(2, 3)
    
    def adjust_layout_for_size(self, width, height, layout_mode):
        """根据窗口大小调整布局"""
        # 清除所有卡片
        for i in reversed(range(self.content_grid.count())):
            item = self.content_grid.itemAt(i)
            if item and item.widget():
                self.content_grid.removeWidget(item.widget())
        
        if layout_mode == LayoutMode.COMPACT:
            # 紧凑模式：所有卡片垂直排列
            self.content_grid.addWidget(self.revenue_card, 0, 0)
            self.content_grid.addWidget(self.inventory_card, 1, 0)
            self.content_grid.addWidget(self.users_card, 2, 0)
            self.content_grid.addWidget(self.sales_trend_card, 3, 0)
            self.content_grid.addWidget(self.users_list_card, 4, 0)
            self.content_grid.addWidget(self.source_table_card, 5, 0)
            self.content_grid.addWidget(self.monthly_sales_card, 6, 0)
            
            # 设置列伸缩因子
            self.content_grid.setColumnStretch(0, 1)
            
            # 设置行伸缩因子
            for i in range(7):
                self.content_grid.setRowStretch(i, 1 if i < 3 else 3)
        elif layout_mode == LayoutMode.NORMAL:
            # 标准模式：二列布局
            # 第一行：指标卡片
            self.content_grid.addWidget(self.revenue_card, 0, 0)
            self.content_grid.addWidget(self.inventory_card, 0, 1)
            self.content_grid.addWidget(self.users_card, 1, 0, 1, 2)
            # 第二行：图表
            self.content_grid.addWidget(self.sales_trend_card, 2, 0, 1, 2)
            # 第三行：其他卡片
            self.content_grid.addWidget(self.users_list_card, 3, 0)
            self.content_grid.addWidget(self.source_table_card, 3, 1)
            # 第四行：月度销售
            self.content_grid.addWidget(self.monthly_sales_card, 4, 0, 1, 2)
            
            # 设置列伸缩因子
            self.content_grid.setColumnStretch(0, 1)
            self.content_grid.setColumnStretch(1, 1)
            
            # 设置行伸缩因子
            self.content_grid.setRowStretch(0, 1)
            self.content_grid.setRowStretch(1, 1)
            self.content_grid.setRowStretch(2, 3)
            self.content_grid.setRowStretch(3, 3)
            self.content_grid.setRowStretch(4, 3)
        else:  # LayoutMode.EXPANDED
            # 扩展模式：完整网格布局
            # 第一行：指标卡片
            self.content_grid.addWidget(self.revenue_card, 0, 0)
            self.content_grid.addWidget(self.inventory_card, 0, 1)
            self.content_grid.addWidget(self.users_card, 0, 2)
            # 第二行：销售趋势和用户列表
            self.content_grid.addWidget(self.sales_trend_card, 1, 0, 1, 2)
            self.content_grid.addWidget(self.users_list_card, 1, 2)
            # 第三行：来源表和月度销售
            self.content_grid.addWidget(self.source_table_card, 2, 0)
            self.content_grid.addWidget(self.monthly_sales_card, 2, 1, 1, 2)
            
            # 设置列伸缩因子
            self.content_grid.setColumnStretch(0, 1)
            self.content_grid.setColumnStretch(1, 1)
            self.content_grid.setColumnStretch(2, 1)
            
            # 设置行伸缩因子
            self.content_grid.setRowStretch(0, 1)
            self.content_grid.setRowStretch(1, 3)
            self.content_grid.setRowStretch(2, 3)
    
    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        
        # 获取当前窗口大小
        current_width = event.size().width()
        current_height = event.size().height()
        
        # 计算并应用布局模式
        layout_mode = ResponsiveLayoutManager.get_layout_mode(current_width)
        if layout_mode != self.current_layout_mode:
            self.current_layout_mode = layout_mode
            self.adjust_layout_for_size(current_width, current_height, layout_mode)
        else:
            # 即使布局模式未变，仍然需要调整以适应新尺寸
            self.adjust_layout_for_size(current_width, current_height, layout_mode)
        
        # 调整在紧凑模式下需要隐藏的组件
        for widget_name, widget in self.compact_hide_widgets.items():
            widget.setVisible(layout_mode != LayoutMode.COMPACT)
    
    def refresh_data(self):
        """刷新仪表盘数据"""
        # 生成测试数据
        self.overview_data = self.generate_overview_data()
        self.sales_data = self.generate_sales_data()
        self.inventory_data = self.generate_inventory_data()
        
        # 更新UI
        self.update_cards_data()
    
    def on_time_range_changed(self):
        """时间范围变化处理"""
        self.refresh_data()
    
    def generate_overview_data(self):
        """生成概览数据"""
        # 示例数据，实际应从数据库获取
        return {
            'total_revenue': random.uniform(10000, 50000),
            'revenue_change': random.uniform(-15, 25),
            'total_inventory': random.uniform(5000, 20000),
            'inventory_change': random.uniform(-10, 20),
            'active_users': random.randint(100, 5000),
            'users_change': random.uniform(-12, 18)
        }
    
    def generate_sales_data(self):
        """生成销售数据"""
        # 示例数据，实际应从数据库获取
        days_range = {
            0: 1,     # 今日
            1: 1,     # 昨日
            2: 7,     # 近7天
            3: 30,    # 近30天
            4: 90     # 近90天
        }.get(self.time_range_combo.currentIndex(), 7)
        
        dates = []
        sales = []
        platforms = ['平台A', '平台B', '平台C']
        platform_data = {p: [] for p in platforms}
        
        # 生成最近N天的数据
        end_date = datetime.now()
        if self.time_range_combo.currentIndex() == 1:  # 昨日
            end_date = end_date - timedelta(days=1)
        
        for i in range(days_range-1, -1, -1):
            current_date = end_date - timedelta(days=i)
            dates.append(current_date.strftime('%m-%d'))
            
            # 总销售额
            daily_sales = random.uniform(500, 2000)
            sales.append(daily_sales)
            
            # 各平台销售额
            remaining = daily_sales
            for platform in platforms[:-1]:
                platform_sales = remaining * random.uniform(0.2, 0.5)
                platform_data[platform].append(platform_sales)
                remaining -= platform_sales
            platform_data[platforms[-1]].append(remaining)
        
        return {
            'dates': dates,
            'sales': sales,
            'platform_data': platform_data
        }
    
    def generate_inventory_data(self):
        """生成库存数据"""
        # 示例数据，实际应从数据库获取
        items = ['女娲石', '银两', '霜玉', '血玉', '魂玉', '仙玉']
        inventory = []
        
        for item in items:
            stock = random.randint(10, 500)
            value = stock * random.uniform(20, 200)
            profit_rate = random.uniform(0.05, 0.40)
            inventory.append({
                'item': item,
                'stock': stock,
                'value': value,
                'profit_rate': profit_rate
            })
        
        return inventory
    
    def update_cards_data(self):
        """更新所有卡片数据"""
        # 更新指标卡片
        self.revenue_card.update_data(
            f"¥{self.overview_data['total_revenue']:,.2f}", 
            f"{self.overview_data['revenue_change']:+.1f}% 月环比", 
            self.overview_data['revenue_change'] >= 0
        )
        
        self.inventory_card.update_data(
            f"¥{self.overview_data['total_inventory']:,.2f}", 
            f"{self.overview_data['inventory_change']:+.1f}% 月环比", 
            self.overview_data['inventory_change'] >= 0
        )
        
        self.users_card.update_data(
            f"{self.overview_data['active_users']:,}", 
            f"{self.overview_data['users_change']:+.1f}% 月环比", 
            self.overview_data['users_change'] >= 0
        )
        
        # 更新销售趋势图表
        self.update_sales_trend_chart()
        
        # 更新用户列表
        self.update_user_list()
        
        # 更新来源表格
        self.update_source_table()
        
        # 更新月度销售图表
        self.update_monthly_sales_chart()
    
    def update_sales_trend_chart(self):
        """更新销售趋势图表"""
        # 清除图表
        self.sales_trend_card.chart.clear()
        
        # 设置坐标轴标签
        self.sales_trend_card.chart.set_axes_labels("日期", "销售额 (¥)")
        
        # 准备平台数据
        data_list = []
        for platform, values in self.sales_data['platform_data'].items():
            data_list.append({
                'data': {'x': self.sales_data['dates'], 'y': values},
                'label': platform
            })
        
        # 绘制折线图
        self.sales_trend_card.chart.plot_multiple(data_list)
    
    def update_user_list(self):
        """更新用户列表"""
        # 清空列表
        self.users_list_card.clear()
        
        # 添加示例用户
        users = [
            ("Helena Smith", "helena@example.com"),
            ("James Wilson", "james@example.com"),
            ("Sophie Brown", "sophie@example.com"),
            ("Michael Chen", "michael@example.com"),
            ("Olivia Johnson", "olivia@example.com")
        ]
        
        for name, email in users:
            self.users_list_card.add_user(name, email)
    
    def update_source_table(self):
        """更新来源表格"""
        # 生成示例数据
        data = [
            ["website.net", "4321", ("+84%", "positive")],
            ["app.store", "4033", ("-8%", "negative")],
            ["social.net", "3128", ("+2%", "positive")],
            ["search.com", "2104", ("+33%", "positive")],
            ["ref.link", "2003", ("+30%", "positive")],
            ["email.marketing", "1894", ("+15%", "positive")],
            ["affiliate.net", "405", ("-12%", "negative")]
        ]
        
        # 更新表格
        self.source_table_card.set_data(data)
    
    def update_monthly_sales_chart(self):
        """更新月度销售图表"""
        # 清除图表
        self.monthly_sales_card.chart.clear()
        
        # 设置坐标轴标签
        self.monthly_sales_card.chart.set_axes_labels("月份", "销售额 (¥)")
        
        # 准备数据
        months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        values = [random.uniform(30000, 80000) for _ in range(12)]
        
        # 绘制柱状图
        self.monthly_sales_card.chart.plot_data(months, values)
    
    def adjust_splitter_sizes(self, width, height):
        """根据窗口当前大小微调分割器比例"""
        # 此方法在新设计中已不再需要，保留是为了兼容性
        pass


def main():
    """测试函数"""
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("仪表盘测试")
    main_window.resize(1200, 800)
    
    # 创建一个模拟的主GUI对象，提供ui_manager属性
    class MockMainGUI:
        def __init__(self):
            from src_qt.utils.ui_manager import UIManager
            self.ui_manager = UIManager()
            self.ui_manager.setup_fonts()
            self.ui_manager.setup_colors()
    
    mock_main_gui = MockMainGUI()
    
    # 创建仪表盘标签页
    dashboard = DashboardTab(main_window, mock_main_gui)
    main_window.setCentralWidget(dashboard)
    
    # 显示窗口
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()