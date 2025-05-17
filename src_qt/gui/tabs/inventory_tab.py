"""
库存管理标签页 - 显示物品库存及价值分析
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QComboBox, QHeaderView, QMessageBox,
                             QFileDialog, QMenu, QStatusBar, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QColor, QAction, QKeySequence

import pandas as pd
from datetime import datetime

class InventoryTab(QWidget):
    """库存管理标签页"""
    
    def __init__(self, parent_frame, main_gui=None):
        super().__init__(parent_frame)
        self.main_gui = main_gui
        self.ui_manager = main_gui.ui_manager if main_gui else None
        
        # 初始化状态变量
        self.status_message = "就绪"
        
        # 初始化UI
        self.init_ui()
        
        # 添加自动刷新
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_inventory)
        self.refresh_timer.start(300000)  # 5分钟刷新一次
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("库存管理")
        title_label.setFont(self.ui_manager.title_font if self.ui_manager else QLabel().font())
        title_layout.addWidget(title_label, 1)  # 1是伸缩系数
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(refresh_button, "small")
        else:
            refresh_button.setFixedWidth(80)
        refresh_button.clicked.connect(self.refresh_inventory)
        title_layout.addWidget(refresh_button)
        
        main_layout.addWidget(title_frame)
        
        # 搜索区域
        search_frame = QWidget()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入物品名称搜索...")
        self.search_input.returnPressed.connect(self.search_inventory)
        search_layout.addWidget(self.search_input, 1)
        
        sort_label = QLabel("排序:")
        search_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["物品名称", "库存数量", "入库均价", "库存价值"])
        self.sort_combo.currentIndexChanged.connect(self.sort_inventory)
        search_layout.addWidget(self.sort_combo)
        
        search_button = QPushButton("搜索")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(search_button, "small")
        else:
            search_button.setFixedWidth(80)
        search_button.clicked.connect(self.search_inventory)
        search_layout.addWidget(search_button)
        
        main_layout.addWidget(search_frame)
        
        # 表格
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(["物品名称", "库存数量", "入库均价", "出库均价", "库存价值"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置表格为可扩展的，以便自适应窗口大小变化
        if self.ui_manager:
            self.ui_manager.apply_expandable_style_to_widget(self.inventory_table)
        else:
            self.inventory_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        main_layout.addWidget(self.inventory_table, 1)  # 1是伸缩系数
        
        # 临时提示标签
        dev_label = QLabel("库存管理功能正在开发中...")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_label.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(dev_label)
    
    def refresh_inventory(self):
        """刷新库存数据"""
        # 清空表格
        self.inventory_table.setRowCount(0)
        
        # TODO: 从数据库或其他数据源加载库存数据
        # 临时使用示例数据
        sample_data = [
            ("女娲石", 100, 3.5, 4.0, 350),
            ("银两", 10000, 0.8, 0.9, 8000),
            ("龙角", 50, 15.0, 18.0, 750)
        ]
        
        # 添加数据到表格
        for row_idx, item_data in enumerate(sample_data):
            self.inventory_table.insertRow(row_idx)
            for col_idx, value in enumerate(item_data):
                # 将数值格式化为字符串
                if isinstance(value, (int, float)):
                    if col_idx == 1:  # 数量列
                        text = f"{value:,}"
                    elif col_idx in [2, 3]:  # 价格列
                        text = f"¥{value:.2f}"
                    elif col_idx == 4:  # 价值列
                        text = f"¥{value:,.2f}"
                    else:
                        text = str(value)
                else:
                    text = str(value)
                
                # 创建单元格项
                table_item = QTableWidgetItem(text)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.inventory_table.setItem(row_idx, col_idx, table_item)
    
    def search_inventory(self):
        """搜索库存"""
        search_text = self.search_input.text().strip().lower()
        
        # 隐藏不符合条件的行
        for row in range(self.inventory_table.rowCount()):
            item_name = self.inventory_table.item(row, 0).text().lower()
            if search_text in item_name:
                self.inventory_table.setRowHidden(row, False)
            else:
                self.inventory_table.setRowHidden(row, True)
    
    def sort_inventory(self):
        """排序库存"""
        sort_column = self.sort_combo.currentIndex()
        self.inventory_table.sortItems(sort_column, Qt.SortOrder.AscendingOrder) 