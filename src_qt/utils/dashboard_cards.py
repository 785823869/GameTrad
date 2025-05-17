"""
仪表盘卡片组件 - 提供各种类型的数据卡片
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QGridLayout, QSizePolicy, QTableWidget,
                            QTableWidgetItem, QHeaderView, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPixmap

from ..utils.matplotlib_chart import LineChart, BarChart, PieChart

class MetricCard(QFrame):
    """指标卡片组件，用于显示关键数据指标"""
    
    def __init__(self, parent=None, title="", value="0", change="", is_positive=True):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #eaeaea;
                border-radius: 6px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(120)
        
        self.setup_ui(title, value, change, is_positive)
    
    def setup_ui(self, title, value, change, is_positive):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # 标题 - 小字体，顶部对齐
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #666; font-size: 12px; font-weight: normal;")
        layout.addWidget(self.title_label)
        
        # 数值 - 大字体，居中对齐，加粗
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #333; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # 描述 - 小字体，带颜色指示
        self.change_container = QWidget()
        change_layout = QHBoxLayout(self.change_container)
        change_layout.setContentsMargins(0, 0, 0, 0)
        change_layout.setSpacing(2)
        
        # 箭头图标
        self.arrow_label = QLabel("▲" if is_positive else "▼")
        color = "#4caf50" if is_positive else "#f44336"
        self.arrow_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        change_layout.addWidget(self.arrow_label)
        
        # 变化文字
        self.change_label = QLabel(change)
        self.change_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        change_layout.addWidget(self.change_label)
        change_layout.addStretch()
        
        layout.addWidget(self.change_container)
        layout.addStretch()  # 底部弹性空间，使内容上对齐
    
    def update_data(self, value, change="", is_positive=True):
        """更新卡片数据"""
        self.value_label.setText(value)
        
        if change:
            color = "#4caf50" if is_positive else "#f44336"
            self.arrow_label.setText("▲" if is_positive else "▼")
            self.arrow_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.change_label.setText(change)
            self.change_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        
        self.change_container.setVisible(bool(change))


class ChartCard(QFrame):
    """图表卡片组件，用于显示各种图表"""
    
    def __init__(self, parent=None, title="", chart_type=LineChart, chart_options=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #eaeaea;
                border-radius: 6px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(250)
        
        chart_options = chart_options or {}
        self.setup_ui(title, chart_type, chart_options)
    
    def setup_ui(self, title, chart_type, chart_options):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 标题
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #333; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 创建图表
        self.chart = chart_type(
            parent=self,
            title=chart_options.get("title", ""),
            figsize=chart_options.get("figsize", (5, 4)),
            dpi=chart_options.get("dpi", 100),
            toolbar=chart_options.get("toolbar", False)
        )
        layout.addWidget(self.chart, 1)  # 图表应该占据所有可用的垂直空间


class TableCard(QFrame):
    """表格卡片组件，用于显示数据表格"""
    
    def __init__(self, parent=None, title="", headers=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #eaeaea;
                border-radius: 6px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(250)
        
        headers = headers or ["列1", "列2", "列3"]
        self.setup_ui(title, headers)
    
    def setup_ui(self, title, headers):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 标题
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #333; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: white;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table, 1)
    
    def set_data(self, data):
        """设置表格数据
        
        参数:
        data -- 列表的列表，每个子列表代表一行数据
        """
        self.table.setRowCount(0)
        
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            for col, cell_data in enumerate(row_data):
                if isinstance(cell_data, tuple) and len(cell_data) == 2:
                    # 如果是元组，第一个元素是文本，第二个元素是样式
                    text, style = cell_data
                    item = QTableWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, style)
                    if style == "positive":
                        item.setForeground(QColor("#4caf50"))
                    elif style == "negative":
                        item.setForeground(QColor("#f44336"))
                else:
                    # 普通文本
                    item = QTableWidgetItem(str(cell_data))
                
                self.table.setItem(row, col, item)


class UserListCard(QFrame):
    """用户列表卡片组件，用于显示用户列表"""
    
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #eaeaea;
                border-radius: 6px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(250)
        
        self.setup_ui(title)
    
    def setup_ui(self, title):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 标题
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #333; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 用户列表容器
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        scroll_area.setWidget(self.list_container)
        
        layout.addWidget(scroll_area, 1)
    
    def add_user(self, name, email, avatar=None):
        """添加用户到列表"""
        user_item = UserListItem(self.list_container, name, email, avatar)
        self.list_layout.addWidget(user_item)
        return user_item
    
    def clear(self):
        """清空用户列表"""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class UserListItem(QFrame):
    """用户列表项组件"""
    
    clicked = pyqtSignal(object)  # 点击信号，传递自身作为参数
    
    def __init__(self, parent=None, name="", email="", avatar=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)
        
        # 用户头像
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(36, 36)
        self.avatar_label.setStyleSheet("""
            background-color: #eaeaea;
            border-radius: 18px;
        """)
        
        if avatar:
            # 如果提供了头像图片，则显示
            pixmap = QPixmap(avatar)
            self.avatar_label.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            # 否则显示首字母
            initials = name[0].upper() if name else "U"
            self.avatar_label.setText(initials)
            self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.avatar_label.setStyleSheet("""
                background-color: #3498db;
                color: white;
                border-radius: 18px;
                font-weight: bold;
            """)
        
        layout.addWidget(self.avatar_label)
        
        # 用户信息
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("font-weight: bold; color: #333; font-size: 13px;")
        info_layout.addWidget(self.name_label)
        
        self.email_label = QLabel(email)
        self.email_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(self.email_label)
        
        layout.addWidget(info_container, 1)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)
        self.clicked.emit(self) 