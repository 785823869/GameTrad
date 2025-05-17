"""
UI管理器 - 负责样式和主题
"""
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, 
                            QScrollArea, QSizePolicy, QPushButton)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect, QPointF
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QPainterPath
import platform

from src_qt.utils.responsive_layout import CollapsiblePanel, ResponsiveSplitter, LayoutMode, WindowSizeThreshold

class ClickableCard(QFrame):
    """可点击的卡片组件，支持鼠标悬停和点击效果"""
    
    # 点击信号
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 启用鼠标跟踪以捕获悬停事件
        self.setMouseTracking(True)
        
        # 设置光标
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置尺寸策略，使卡片能够在水平方向上扩展，但垂直方向上保持固定大小
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 状态和样式
        self.is_hovered = False
        self.is_pressed = False
        self.base_style = ""
        self.hover_style = ""
        self.pressed_style = ""
    
    def set_styles(self, base_style, hover_style):
        """设置基本样式和悬停样式"""
        self.base_style = base_style
        self.hover_style = hover_style
        self.pressed_style = hover_style.replace(
            "border: 1px solid", "border: 2px solid"
        )
        self.setStyleSheet(self.base_style)
    
    def update_style(self):
        """根据当前状态更新样式"""
        if self.is_pressed:
            self.setStyleSheet(self.pressed_style)
        elif self.is_hovered:
            self.setStyleSheet(self.hover_style)
        else:
            self.setStyleSheet(self.base_style)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.update_style()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.update_style()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            was_pressed = self.is_pressed
            self.is_pressed = False
            self.update_style()
            
            # 只有在卡片区域内释放鼠标才触发点击事件
            if was_pressed and self.rect().contains(event.pos()):
                self.clicked.emit()
        
        super().mouseReleaseEvent(event)


class MiniSparklineWidget(QWidget):
    """迷你趋势图小部件"""
    
    def __init__(self, data=None, color="#3498db", width=60, height=20):
        super().__init__()
        self.data = data or []
        self.color = QColor(color)
        self.setFixedSize(width, height)
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
    
    def set_data(self, data):
        """设置数据"""
        self.data = data
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        """绘制事件"""
        if not self.data or len(self.data) < 2:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 准备路径
        path = QPainterPath()
        
        # 计算比例
        width = self.width()
        height = self.height()
        x_scale = width / (len(self.data) - 1)
        
        # 找到最小值和最大值
        min_val = min(self.data)
        max_val = max(self.data)
        
        # 如果所有值都相同，增加一点空间
        if min_val == max_val:
            min_val = min_val * 0.9
            max_val = max_val * 1.1
        
        # 计算垂直比例
        value_range = max_val - min_val
        y_scale = height / value_range if value_range > 0 else 1
        
        # 创建路径
        for i, value in enumerate(self.data):
            x = i * x_scale
            # 翻转y轴，因为Qt的坐标系是从左上角开始的
            y = height - ((value - min_val) * y_scale)
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        # 绘制路径
        pen = QPen(self.color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # 强调最后一个点
        last_x = (len(self.data) - 1) * x_scale
        last_y = height - ((self.data[-1] - min_val) * y_scale)
        painter.setBrush(self.color)
        painter.drawEllipse(QPointF(last_x, last_y), 2, 2)


class UIManager:
    """UI管理器，负责全局样式和字体设置"""
    
    def __init__(self):
        self.setup_fonts()
        self.setup_colors()
        
        # 定义按钮的标准尺寸
        self.standard_button_height = 30
        self.small_button_width = 80
        self.medium_button_width = 120
        self.large_button_width = 160
        
        # 添加响应式设计参数
        self.current_layout_mode = LayoutMode.NORMAL
        
    def setup_fonts(self):
        """设置全局字体"""
        system = platform.system()
        
        # 检测可用中文字体
        if system == 'Windows':
            # Windows系统优先使用微软雅黑
            self.main_font = 'Microsoft YaHei'
        elif system == 'Darwin':  # macOS
            # macOS系统优先使用苹方
            self.main_font = 'PingFang SC'
        else:  # Linux等其他系统
            # Linux系统优先使用文泉驿
            self.main_font = 'WenQuanYi Micro Hei'
            
        # 定义字体大小组合
        self.small_font = QFont(self.main_font, 10)
        self.medium_font = QFont(self.main_font, 12)
        self.large_font = QFont(self.main_font, 14)
        
        # 粗体版本
        self.medium_bold_font = QFont(self.main_font, 12, QFont.Weight.Bold)
        self.large_bold_font = QFont(self.main_font, 14, QFont.Weight.Bold)
        self.title_font = QFont(self.main_font, 18, QFont.Weight.Bold)
        
        # 确保字体渲染清晰
        for font in [self.small_font, self.medium_font, self.large_font, 
                     self.medium_bold_font, self.large_bold_font, self.title_font]:
            font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    
    def setup_colors(self):
        """设置全局配色方案"""
        self.colors = {
            'primary': '#2c3e50',     # 深蓝色，作为主要强调色
            'secondary': '#3498db',   # 浅蓝色
            'warning': '#f39c12',     # 橙色，更明亮
            'danger': '#e74c3c',      # 红色
            'info': '#2980b9',        # 蓝色
            'light': '#ecf0f1',       # 浅灰色
            'dark': '#2c3e50',        # 深色
            'bg_light': '#ffffff',    # 纯白背景色
            'bg_dark': '#34495e',     # 深背景色
            'text_primary': '#2c3e50', # 主文本颜色，深色更易读
            'text_secondary': '#7f8c8d' # 次要文本颜色
        }
    
    def create_dashboard_container(self, parent, title=None):
        """创建一个用于包含仪表盘部件的容器
        
        参数:
        - parent: 父组件
        - title: 容器标题（可选）
        
        返回:
        - 容器框架, 内容布局
        """
        # 创建外部容器框架
        container = QFrame(parent)
        container.setFrameShape(QFrame.Shape.StyledPanel)
        # 使用Qt样式表添加阴影和更精致的边框
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                margin: 0px;
            }
        """)
        
        # 添加投影效果（如果平台支持）
        try:
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            from PyQt6.QtGui import QColor
            
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 2)
            container.setGraphicsEffect(shadow)
        except ImportError:
            # 如果不支持图形效果，则使用边框代替
            pass
            
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 创建布局
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 添加标题（如果提供）
        if title:
            title_label = QLabel(title)
            title_label.setFont(self.medium_bold_font)
            title_label.setStyleSheet(f"color: {self.colors['primary']};")
            main_layout.addWidget(title_label)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        main_layout.addWidget(content_widget)
        
        return container, content_layout
    
    def create_card(self, parent, title, value="--", description="", icon=None):
        """创建信息卡片"""
        card = QFrame(parent)
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['bg_light']};
                border-radius: 8px;
                border: 1px solid {self.colors['light']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题行
        title_frame = QWidget(card)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setFont(self.medium_font)
        title_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
        title_layout.addWidget(title_label, 1)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 16px; color: {self.colors['primary']};")
            title_layout.addWidget(icon_label)
        
        layout.addWidget(title_frame)
        
        # 值显示
        value_label = QLabel(value)
        value_label.setFont(self.title_font)
        value_label.setStyleSheet(f"color: {self.colors['primary']};")
        layout.addWidget(value_label)
        
        # 描述
        if description:
            desc_label = QLabel(description)
            desc_label.setFont(self.small_font)
            desc_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
            layout.addWidget(desc_label)
            
        return card, value_label
    
    def create_stats_card(self, parent, title, value, change_value=None, is_positive=True, trend_data=None, on_click=None):
        """创建带有变化指标和迷你趋势图的统计卡片"""
        # 创建可点击卡片
        card = ClickableCard(parent)
        card.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 设置基本样式和悬停样式
        base_style = f"""
            QFrame {{
                background-color: {self.colors['bg_light']};
                border-radius: 8px;
                border: 1px solid {self.colors['light']};
                padding: 10px;
            }}
        """
        
        hover_style = f"""
            QFrame {{
                background-color: {self.colors['bg_light']};
                border-radius: 8px;
                border: 1px solid {self.colors['secondary']};
                padding: 10px;
            }}
        """
        
        card.set_styles(base_style, hover_style)
        
        # 设置尺寸策略，水平方向扩展，垂直方向固定
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(120)
        
        # 使用垂直布局
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(self.medium_font)
        title_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
        layout.addWidget(title_label)
        
        # 值
        value_label = QLabel(value)
        value_label.setFont(self.title_font)
        value_label.setStyleSheet(f"color: {self.colors['primary']};")
        layout.addWidget(value_label)
        
        # 底部框架，包含变化值和迷你趋势图
        bottom_frame = QWidget()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 变化值
        if change_value:
            change_color = self.colors['info'] if is_positive else self.colors['danger']
            change_icon = "▲" if is_positive else "▼"
            
            icon_label = QLabel(change_icon)
            icon_label.setStyleSheet(f"color: {change_color}; font-size: 12px;")
            
            change_label = QLabel(change_value)
            change_label.setStyleSheet(f"color: {change_color};")
            change_label.setFont(self.small_font)
            
            bottom_layout.addWidget(icon_label)
            bottom_layout.addWidget(change_label)
        
        bottom_layout.addStretch(1)  # 添加弹性空间
        
        # 添加迷你趋势图
        if trend_data:
            trend_color = self.colors['info'] if is_positive else self.colors['danger']
            sparkline = MiniSparklineWidget(trend_data, trend_color, 60, 20)
            bottom_layout.addWidget(sparkline, 0, Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(bottom_frame)
        layout.addStretch()  # 添加底部弹性空间
        
        # 连接点击信号
        if on_click:
            card.clicked.connect(on_click)
        
        return card, value_label
    
    def apply_fixed_button_size(self, button, size="medium"):
        """应用固定按钮大小
        
        参数:
        - button: QPushButton对象
        - size: 大小类型，可选值为"small"、"medium"、"large"或具体的宽度数值
        """
        # 设置固定高度
        button.setFixedHeight(self.standard_button_height)
        
        # 根据指定的大小类型设置宽度
        if size == "small":
            button.setFixedWidth(self.small_button_width)
        elif size == "medium":
            button.setFixedWidth(self.medium_button_width)
        elif size == "large":
            button.setFixedWidth(self.large_button_width)
        elif isinstance(size, int):
            button.setFixedWidth(size)
        
        # 设置大小策略为固定
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    def apply_modern_style(self, app):
        """应用现代风格到整个应用"""
        app.setStyle("Fusion")
        
        # 设置全局调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors['bg_light']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors['bg_light']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors['light']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.colors['dark']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor('white'))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors['light']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.Link, QColor(self.colors['secondary']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors['secondary']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor('white'))
        
        app.setPalette(palette)
        
        # 设置简化的全局样式表
        app.setStyleSheet("""
            QMainWindow, QDialog { 
                background-color: white;
            }
            
            QLabel { 
                color: #2c3e50;
            }
            
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 30px;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QLineEdit, QTextEdit, QPlainTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            
            QTableView, QTreeView, QListView {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            
            /* 确保表格和其他数据显示区域可以自适应 */
            QTableWidget, QTreeWidget, QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
    
    def create_scroll_area(self, parent):
        """创建自定义滚动区域"""
        scroll = QScrollArea(parent)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        scroll.setWidget(content)
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        return scroll, content, layout
    
    def apply_global_font(self, app):
        """应用全局字体设置"""
        app.setFont(self.medium_font)
    
    def apply_expandable_style_to_widget(self, widget):
        """设置组件为可扩展样式，适用于数据显示区域
        
        参数:
        - widget: 需要设置为可扩展的组件
        """
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    # 添加响应式布局支持方法
    def create_collapsible_panel(self, title, content_widget, parent=None, collapsed=False):
        """创建可折叠面板
        
        参数:
        - title: 面板标题
        - content_widget: 面板内容组件
        - parent: 父组件
        - collapsed: 初始状态是否折叠
        
        返回:
        - 创建的可折叠面板
        """
        panel = CollapsiblePanel(title, parent, collapsible=True, collapsed=collapsed)
        panel.set_content(content_widget)
        return panel
    
    def create_responsive_splitter(self, orientation=Qt.Orientation.Horizontal, parent=None):
        """创建响应式分割器
        
        参数:
        - orientation: 分割方向
        - parent: 父组件
        
        返回:
        - 创建的响应式分割器
        """
        return ResponsiveSplitter(orientation, parent)
    
    def update_layout_mode(self, width):
        """根据宽度更新布局模式
        
        参数:
        - width: 容器宽度
        
        返回:
        - 如果布局模式发生变化，返回True；否则返回False
        """
        old_mode = self.current_layout_mode
        
        # 确定新的布局模式
        if width < WindowSizeThreshold.COMPACT_WIDTH:
            self.current_layout_mode = LayoutMode.COMPACT
        elif width < WindowSizeThreshold.NORMAL_WIDTH:
            self.current_layout_mode = LayoutMode.NORMAL
        else:
            self.current_layout_mode = LayoutMode.EXPANDED
        
        # 如果模式改变，返回True
        return old_mode != self.current_layout_mode
    
    def get_current_layout_mode(self):
        """获取当前布局模式"""
        return self.current_layout_mode
    
    def create_responsive_button(self, text, icon=None, size="medium", show_text_modes=(LayoutMode.NORMAL, LayoutMode.EXPANDED)):
        """创建一个会根据布局模式调整的按钮
        
        参数:
        - text: 按钮文本
        - icon: 按钮图标
        - size: 按钮大小类型
        - show_text_modes: 显示文本的布局模式列表
        
        返回:
        - 创建的按钮
        """
        from PyQt6.QtGui import QIcon
        
        button = QPushButton(text)
        if icon:
            button.setIcon(QIcon(icon))
        
        self.apply_fixed_button_size(button, size)
        
        # 存储原始文本
        button.original_text = text
        button.show_text_modes = show_text_modes
        
        # 添加方法以根据布局模式更新按钮
        def update_for_mode(mode):
            if mode in button.show_text_modes:
                button.setText(button.original_text)
            else:
                button.setText("")
        
        button.update_for_mode = update_for_mode
        
        return button 