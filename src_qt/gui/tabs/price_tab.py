"""
价格行情标签页基类 - 提供价格行情图表和数据处理的共用功能
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSplitter, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QDateEdit, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSlot, QDate, QTimer
from PyQt6.QtGui import QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib

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

import numpy as np
from datetime import datetime, timedelta
import random

from src_qt.utils.responsive_layout import LayoutMode, WindowSizeThreshold, ResponsiveLayoutManager, ResponsiveSplitter

class PriceChart(QWidget):
    """价格走势图表组件"""
    
    def __init__(self, parent=None, title='价格走势'):
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        
        # 添加工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 添加到布局
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # 设置标题
        self.chart_title = title
        
        # 初始化空图表
        self.init_chart()
    
    def init_chart(self):
        """初始化图表"""
        self.axes.clear()
        self.axes.set_title(self.chart_title)
        self.axes.set_xlabel('日期')
        self.axes.set_ylabel('价格 (元)')
        self.axes.grid(True, linestyle='--', alpha=0.7)
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_chart(self, data):
        """
        更新图表数据
        
        参数:
        data - 包含多个系列的字典，格式如下:
        {
            'dates': [...],  # 日期列表
            'series': {
                '平台1': [...],  # 价格列表
                '平台2': [...],
                ...
            }
        }
        """
        self.axes.clear()
        
        if not data or 'dates' not in data or 'series' not in data:
            self.init_chart()
            return
        
        dates = data['dates']
        series = data['series']
        
        # 为不同平台生成不同颜色的线条
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        
        for i, (platform, prices) in enumerate(series.items()):
            if prices and len(prices) == len(dates):
                color = colors[i % len(colors)]
                self.axes.plot(dates, prices, color=color, marker='o', markersize=4, label=platform)
        
        self.axes.set_title(self.chart_title)
        self.axes.set_xlabel('日期')
        self.axes.set_ylabel('价格 (元)')
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        # 自动旋转日期标签以避免重叠
        plt.setp(self.axes.get_xticklabels(), rotation=45, ha='right')
        
        # 添加图例
        if series:
            self.axes.legend(loc='best')
        
        self.figure.tight_layout()
        self.canvas.draw()

class PriceTab(QWidget):
    """价格行情标签页基类"""
    
    def __init__(self, parent_frame, main_gui=None, item_name='', chart_title=''):
        super().__init__(parent_frame)
        self.main_gui = main_gui
        self.ui_manager = main_gui.ui_manager if main_gui else None
        self.item_name = item_name
        self.chart_title = chart_title or f'{item_name}价格走势'
        
        # 用于存储最后一次获取的数据，方便子类访问
        self._last_price_data = None
        
        # 当前布局模式
        self.current_layout_mode = LayoutMode.NORMAL
        
        # 初始化UI
        self.init_ui()
        
        # 自动刷新计时器 (30分钟刷新一次)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(1800000)  # 1800000毫秒 = 30分钟
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 标题区域
        self.init_header()
        
        # 创建统一的价格数据容器
        self.price_container, price_layout = self.ui_manager.create_dashboard_container(self)
        
        # 创建响应式分割器，上部显示图表，下部显示数据表
        self.splitter = ResponsiveSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        
        # 设置分割器为可扩展的
        self.splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 图表区域
        self.chart_frame = QWidget()
        self.init_chart_area()
        
        # 数据表格区域
        self.table_frame = QWidget()
        self.init_table_area()
        
        # 为分割器添加组件
        self.splitter.addWidget(self.chart_frame)
        self.splitter.addWidget(self.table_frame)
        
        # 设置分割器默认尺寸比例（图表:表格 = 2:1）
        self.splitter.set_responsive_sizes(
            default_sizes=[200, 100],       # 标准模式下的尺寸比例
            compact_sizes=[300, 100],       # 紧凑模式下的尺寸比例
            expanded_sizes=[300, 150]       # 展开模式下的尺寸比例
        )
        
        # 将分割器添加到价格容器中
        price_layout.addWidget(self.splitter, 1)
        
        # 将价格容器添加到主布局
        self.main_layout.addWidget(self.price_container, 1)
        
        # 状态栏
        self.init_stats_area()
    
    def init_header(self):
        """初始化标题区域"""
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(f"{self.item_name}行情")
        title_label.setFont(self.ui_manager.title_font if self.ui_manager else QLabel().font())
        title_layout.addWidget(title_label, 1)  # 1是伸缩系数
        
        # 时间范围选择
        time_range_label = QLabel("时间范围:")
        title_layout.addWidget(time_range_label)
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["近7天", "近30天", "近90天", "近半年", "近一年"])
        self.time_range_combo.setCurrentIndex(1)  # 默认选择近30天
        self.time_range_combo.currentIndexChanged.connect(self.on_time_range_changed)
        title_layout.addWidget(self.time_range_combo)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(refresh_button, "small")
        else:
            refresh_button.setFixedWidth(80)
        refresh_button.clicked.connect(self.refresh_data)
        title_layout.addWidget(refresh_button)
        
        self.main_layout.addWidget(title_frame)
        
        # 存储要在紧凑模式下隐藏的组件
        self.compact_hide_widgets = {
            "time_range_label": time_range_label
        }
    
    def init_chart_area(self):
        """初始化图表区域"""
        chart_layout = QVBoxLayout(self.chart_frame)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.price_chart = PriceChart(title=self.chart_title)
        chart_layout.addWidget(self.price_chart)
    
    def init_table_area(self):
        """初始化表格区域"""
        table_layout = QVBoxLayout(self.table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # 表格标题
        table_header = QWidget()
        table_header_layout = QHBoxLayout(table_header)
        table_header_layout.setContentsMargins(0, 0, 0, 0)
        
        table_header_layout.addWidget(QLabel("历史价格数据"))
        table_header_layout.addStretch(1)
        
        # 平台筛选
        platform_label = QLabel("平台:")
        table_header_layout.addWidget(platform_label)
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["全部平台", "DD373", "UU898", "5173", "7881", "其他"])
        self.platform_combo.currentIndexChanged.connect(self.filter_price_data)
        table_header_layout.addWidget(self.platform_combo)
        
        table_layout.addWidget(table_header)
        
        # 价格表格
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(5)
        self.price_table.setHorizontalHeaderLabels(["日期", "平台", "最低价", "平均价", "最高价"])
        self.price_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.price_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.price_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置表格为可扩展的
        if self.ui_manager:
            self.ui_manager.apply_expandable_style_to_widget(self.price_table)
        else:
            self.price_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        table_layout.addWidget(self.price_table, 1)
        
        # 存储要在紧凑模式下隐藏的组件
        self.table_compact_hide_widgets = {
            "platform_label": platform_label
        }
    
    def init_stats_area(self):
        """初始化统计区域"""
        self.stats_frame = QWidget()
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(5, 5, 5, 5)
        stats_layout.setSpacing(20)
        
        # 当前价格统计
        self.current_price_label = QLabel("当前价格: -")
        self.current_price_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(self.current_price_label)
        
        # 30天价格趋势
        self.trend_label = QLabel("30天趋势: -")
        stats_layout.addWidget(self.trend_label)
        
        # 价格波动
        self.volatility_label = QLabel("价格波动: -")
        stats_layout.addWidget(self.volatility_label)
        
        stats_layout.addStretch(1)
        
        # 最后更新时间
        self.last_update_label = QLabel("最后更新: -")
        self.last_update_label.setStyleSheet("color: gray; font-style: italic;")
        stats_layout.addWidget(self.last_update_label)
        
        self.main_layout.addWidget(self.stats_frame)
    
    def update_layout_for_mode(self, layout_mode):
        """更新标签页布局以适应新的布局模式"""
        if self.current_layout_mode == layout_mode:
            return
            
        self.current_layout_mode = layout_mode
        
        # 更新主布局的边距
        if layout_mode == LayoutMode.COMPACT:
            self.main_layout.setContentsMargins(10, 10, 10, 10)
            self.main_layout.setSpacing(10)
            # 更新价格容器边距
            self.price_container.layout().setContentsMargins(10, 10, 10, 10)
            self.price_container.layout().setSpacing(10)
            
            # 隐藏非核心组件
            for widget in self.compact_hide_widgets.values():
                widget.setVisible(False)
            
            for widget in self.table_compact_hide_widgets.values():
                widget.setVisible(False)
            
            # 调整表格列视图
            self.adjust_table_columns_for_mode(layout_mode)
            
        elif layout_mode == LayoutMode.NORMAL:
            self.main_layout.setContentsMargins(15, 15, 15, 15)
            self.main_layout.setSpacing(15)
            # 更新价格容器边距
            self.price_container.layout().setContentsMargins(15, 15, 15, 15)
            self.price_container.layout().setSpacing(15)
            
            # 显示所有组件
            for widget in self.compact_hide_widgets.values():
                widget.setVisible(True)
                
            for widget in self.table_compact_hide_widgets.values():
                widget.setVisible(True)
                
            # 调整表格列视图
            self.adjust_table_columns_for_mode(layout_mode)
            
        else:  # EXPANDED
            self.main_layout.setContentsMargins(20, 20, 20, 20)
            self.main_layout.setSpacing(20)
            # 更新价格容器边距
            self.price_container.layout().setContentsMargins(20, 20, 20, 20)
            self.price_container.layout().setSpacing(20)
            
            # 显示所有组件
            for widget in self.compact_hide_widgets.values():
                widget.setVisible(True)
                
            for widget in self.table_compact_hide_widgets.values():
                widget.setVisible(True)
                
            # 调整表格列视图
            self.adjust_table_columns_for_mode(layout_mode)
        
        # 更新分割器尺寸比例
        self.splitter.update_layout_mode(self.width(), self.height())
    
    def adjust_table_columns_for_mode(self, layout_mode):
        """根据布局模式调整表格列的显示"""
        if layout_mode == LayoutMode.COMPACT:
            # 紧凑模式下只显示关键列
            self.price_table.setColumnHidden(4, True)  # 隐藏"最高价"列
        else:
            # 其他模式下显示所有列
            self.price_table.setColumnHidden(4, False)
    
    def refresh_data(self):
        """刷新价格数据 - 子类应重写此方法实现具体物品的数据获取"""
        # 获取时间范围
        days = self.get_days_from_range()
        
        # 生成测试数据
        data = self.generate_test_data(days)
        
        # 更新图表和表格
        self.update_ui_with_data(data)
    
    def get_days_from_range(self):
        """根据选择的时间范围返回天数"""
        range_text = self.time_range_combo.currentText()
        if range_text == "近7天":
            return 7
        elif range_text == "近30天":
            return 30
        elif range_text == "近90天":
            return 90
        elif range_text == "近半年":
            return 180
        elif range_text == "近一年":
            return 365
        return 30  # 默认30天
    
    def generate_test_data(self, days):
        """生成测试数据"""
        # 生成日期列表
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_list = []
        current = start_date
        while current <= end_date:
            date_list.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        # 生成不同平台的价格数据
        platforms = ["DD373", "UU898", "5173", "7881"]
        series_data = {}
        
        # 设置基础价格和波动范围
        if self.item_name == "女娲石":
            base_price = 4.0
            fluctuation = 0.8
        elif self.item_name == "银两":
            base_price = 0.9
            fluctuation = 0.2
        else:
            base_price = 10.0
            fluctuation = 2.0
        
        # 为每个平台生成价格
        for platform in platforms:
            # 给每个平台一个稍微不同的基础价格
            platform_base = base_price * (0.9 + 0.2 * random.random())
            
            # 生成该平台的价格序列
            prices = []
            current_price = platform_base
            
            for i in range(len(date_list)):
                # 添加一些随机波动
                change = (random.random() - 0.5) * fluctuation * 0.1
                # 添加一些趋势
                trend = (i / len(date_list) - 0.5) * fluctuation * 0.2
                
                current_price = current_price * (1 + change) + trend
                # 确保价格不会低于0
                current_price = max(0.1, current_price)
                
                prices.append(round(current_price, 2))
            
            series_data[platform] = prices
        
        # 构建返回数据
        data = {
            'dates': date_list,
            'series': series_data
        }
        
        # 保存最后一次数据
        self._last_price_data = data
        
        return data
    
    def update_ui_with_data(self, data):
        """更新UI显示"""
        if not data:
            return
        
        # 更新图表
        self.price_chart.update_chart(data)
        
        # 更新表格
        self.update_price_table(data)
        
        # 更新统计信息
        self.update_stats(data)
        
        # 更新更新时间
        self.last_update_label.setText(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def update_price_table(self, data):
        """更新价格表格"""
        self.price_table.setRowCount(0)
        
        if not data or 'dates' not in data or 'series' not in data:
            return
        
        dates = data['dates']
        series = data['series']
        
        # 遍历所有数据，添加到表格
        row = 0
        for platform, prices in series.items():
            for i, (date, price) in enumerate(zip(dates, prices)):
                self.price_table.insertRow(row)
                
                # 日期
                date_item = QTableWidgetItem(date)
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.price_table.setItem(row, 0, date_item)
                
                # 平台
                platform_item = QTableWidgetItem(platform)
                platform_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.price_table.setItem(row, 1, platform_item)
                
                # 价格
                price_item = QTableWidgetItem(f"¥{price:.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.price_table.setItem(row, 2, price_item)
                
                row += 1
        
        # 按日期降序排序
        self.price_table.sortItems(0, Qt.SortOrder.DescendingOrder)
    
    def filter_price_data(self):
        """根据平台筛选表格数据"""
        selected_platform = self.platform_combo.currentText()
        
        # 如果选择全部平台，显示所有行
        if selected_platform == "全部平台":
            for row in range(self.price_table.rowCount()):
                self.price_table.setRowHidden(row, False)
            return
        
        # 否则，只显示选中平台的数据
        for row in range(self.price_table.rowCount()):
            platform = self.price_table.item(row, 1).text()
            self.price_table.setRowHidden(row, platform != selected_platform)
    
    def update_stats(self, data):
        """更新统计信息"""
        if not data or 'series' not in data:
            return
        
        all_prices = []
        for platform, prices in data['series'].items():
            all_prices.extend(prices)
        
        if not all_prices:
            return
        
        # 计算统计数据
        current_price = all_prices[-1] if all_prices else 0
        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        max_price = max(all_prices) if all_prices else 0
        min_price = min(all_prices) if all_prices else 0
        
        # 更新标签
        self.current_price_label.setText(f"当前价格: ¥{current_price:.2f}")
        self.trend_label.setText(f"30天趋势: {avg_price:.2f}")
        self.volatility_label.setText(f"价格波动: {max_price - min_price:.2f}")
    
    def on_time_range_changed(self):
        """时间范围变更时刷新数据"""
        self.refresh_data() 