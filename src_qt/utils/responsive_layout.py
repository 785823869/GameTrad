"""
响应式布局工具 - 提供自适应布局支持
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                            QPushButton, QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve

class LayoutMode:
    """布局模式枚举"""
    COMPACT = 0    # 紧凑模式 - 用于窗口小于900像素宽时
    NORMAL = 1     # 标准模式 - 用于900-1200像素宽的窗口
    EXPANDED = 2   # 展开模式 - 用于大于1200像素宽的窗口

class WindowSizeThreshold:
    """窗口大小阈值常量"""
    COMPACT_WIDTH = 900   # 紧凑模式的最大宽度阈值
    NORMAL_WIDTH = 1200   # 标准模式的最大宽度阈值
    
    COMPACT_HEIGHT = 600  # 紧凑模式的最大高度阈值
    NORMAL_HEIGHT = 800   # 标准模式的最大高度阈值

class ResponsiveSplitter(QSplitter):
    """响应式分割器，根据窗口尺寸调整分割位置"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.default_sizes = []
        self.compact_sizes = []
        self.expanded_sizes = []
        self.current_mode = LayoutMode.NORMAL
    
    def set_responsive_sizes(self, default_sizes, compact_sizes=None, expanded_sizes=None):
        """设置不同布局模式下的分割尺寸
        
        参数:
        - default_sizes: 标准模式下的尺寸比例列表
        - compact_sizes: 紧凑模式下的尺寸比例列表（可选）
        - expanded_sizes: 展开模式下的尺寸比例列表（可选）
        """
        self.default_sizes = default_sizes
        self.compact_sizes = compact_sizes or default_sizes
        self.expanded_sizes = expanded_sizes or default_sizes
        
        # 应用默认尺寸
        self.setSizes(self.default_sizes)
    
    def update_layout_mode(self, width, height):
        """根据容器宽度更新布局模式
        
        返回:
        - 如果布局模式发生变化，返回True；否则返回False
        """
        old_mode = self.current_mode
        
        # 确定新的布局模式
        if width < WindowSizeThreshold.COMPACT_WIDTH:
            self.current_mode = LayoutMode.COMPACT
        elif width < WindowSizeThreshold.NORMAL_WIDTH:
            self.current_mode = LayoutMode.NORMAL
        else:
            self.current_mode = LayoutMode.EXPANDED
        
        # 如果模式改变，应用相应的尺寸
        if old_mode != self.current_mode:
            if self.current_mode == LayoutMode.COMPACT:
                self.setSizes(self.compact_sizes)
            elif self.current_mode == LayoutMode.NORMAL:
                self.setSizes(self.default_sizes)
            else:  # EXPANDED
                self.setSizes(self.expanded_sizes)
            return True
        
        return False

class CollapsiblePanel(QWidget):
    """可折叠的面板"""
    
    # 折叠状态变化信号
    stateChanged = pyqtSignal(bool)  # True表示展开，False表示折叠
    
    def __init__(self, title="", parent=None, collapsible=True, collapsed=False, min_width=200):
        super().__init__(parent)
        
        self.collapsible = collapsible
        self.collapsed = collapsed
        self.min_width = min_width
        self.animation = None
        self.content_widget = None
        
        # 设置布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 创建标题栏
        self.header = QFrame()
        self.header.setFrameShape(QFrame.Shape.StyledPanel)
        self.header.setMinimumHeight(30)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
            }
        """)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 2, 10, 2)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        if collapsible:
            self.toggle_button = QPushButton("▼" if not collapsed else "►")
            self.toggle_button.setFixedSize(20, 20)
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
            """)
            self.toggle_button.clicked.connect(self.toggle_collapsed)
            header_layout.addWidget(self.toggle_button)
        
        self.layout.addWidget(self.header)
        
        # 创建内容区域框架
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-top: none;
                border-radius: 0px 0px 4px 4px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        
        self.layout.addWidget(self.content_frame)
        
        # 初始化折叠状态
        if collapsed:
            self.content_frame.setMaximumHeight(0)
            self.content_frame.setMinimumHeight(0)
    
    def set_content(self, widget):
        """设置面板内容"""
        self.content_widget = widget
        self.content_layout.addWidget(widget)
    
    def toggle_collapsed(self):
        """切换折叠状态"""
        self.set_collapsed(not self.collapsed)
    
    def set_collapsed(self, collapsed):
        """设置折叠状态"""
        if self.collapsed == collapsed or not self.collapsible:
            return
        
        self.collapsed = collapsed
        
        # 更新切换按钮文本
        if hasattr(self, 'toggle_button'):
            self.toggle_button.setText("▼" if not collapsed else "►")
        
        # 创建展开/折叠动画
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self.content_frame, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        if collapsed:
            self.animation.setStartValue(self.content_frame.height())
            self.animation.setEndValue(0)
        else:
            content_height = self.content_widget.sizeHint().height() + 20  # 添加一些间距
            self.animation.setStartValue(0)
            self.animation.setEndValue(content_height)
            self.content_frame.setMaximumHeight(content_height)
        
        self.animation.start()
        
        # 发送状态变化信号
        self.stateChanged.emit(not collapsed)

class ResponsiveLayoutManager:
    """响应式布局管理器，提供辅助函数管理响应式布局"""
    
    @staticmethod
    def get_layout_mode(width, height=None):
        """根据窗口宽度获取当前应该使用的布局模式"""
        if width < WindowSizeThreshold.COMPACT_WIDTH:
            return LayoutMode.COMPACT
        elif width < WindowSizeThreshold.NORMAL_WIDTH:
            return LayoutMode.NORMAL
        else:
            return LayoutMode.EXPANDED
    
    @staticmethod
    def clear_layout_safely(container):
        """安全清除容器的布局，不使用setLayout(None)
        
        参数:
        - container: 包含布局的容器
        """
        if not container or not container.layout():
            return
            
        # 清理旧布局中的所有项目
        while container.layout().count():
            item = container.layout().takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # 标记布局为删除
        container.layout().deleteLater()
    
    @staticmethod
    def apply_responsive_columns(container, items, layout_mode):
        """根据布局模式创建自适应的列布局
        
        参数:
        - container: 要添加列布局的容器
        - items: 要显示的项目列表
        - layout_mode: 当前布局模式
        
        返回:
        - 创建的布局
        """
        # 使用安全方法清除现有布局
        ResponsiveLayoutManager.clear_layout_safely(container)
        
        # 根据布局模式确定列数
        if layout_mode == LayoutMode.COMPACT:
            columns = 1
        elif layout_mode == LayoutMode.NORMAL:
            columns = 2
        else:  # EXPANDED
            columns = 3
        
        # 创建网格布局
        from PyQt6.QtWidgets import QGridLayout
        layout = QGridLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 计算每列的项目数
        items_per_column = max(1, (len(items) + columns - 1) // columns)
        
        # 添加项目到布局
        for i, item in enumerate(items):
            row = i % items_per_column
            col = i // items_per_column
            layout.addWidget(item, row, col)
        
        return layout
    
    @staticmethod
    def set_visibility_based_on_mode(widgets_dict, layout_mode):
        """根据布局模式设置组件可见性
        
        参数:
        - widgets_dict: 字典，键是布局模式的组合，值是组件列表
          例如：{LayoutMode.NORMAL | LayoutMode.EXPANDED: [widget1, widget2]}
        - layout_mode: 当前布局模式
        """
        for modes, widgets in widgets_dict.items():
            visible = (modes & layout_mode) > 0
            for widget in widgets:
                widget.setVisible(visible)
    
    @staticmethod
    def create_responsive_button(text, icon=None, show_text_threshold=LayoutMode.NORMAL):
        """创建一个会根据布局模式调整的按钮
        
        参数:
        - text: 按钮文本
        - icon: 按钮图标
        - show_text_threshold: 显示文本的布局模式阈值
        
        返回:
        - 创建的按钮
        """
        from PyQt6.QtGui import QIcon
        
        button = QPushButton(text)
        if icon:
            button.setIcon(QIcon(icon))
        
        # 存储原始文本
        button.original_text = text
        button.show_text_threshold = show_text_threshold
        
        # 添加方法以根据布局模式更新按钮
        def update_for_mode(mode):
            if mode >= show_text_threshold:
                button.setText(button.original_text)
            else:
                button.setText("")
        
        button.update_for_mode = update_for_mode
        
        return button 