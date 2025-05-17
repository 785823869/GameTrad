"""
现代化侧边栏组件 - PyQt6实现
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                            QFrame, QStackedWidget, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor

class ModernSidebar(QWidget):
    """现代化侧边栏组件"""
    # 标签页切换信号
    tabChanged = pyqtSignal(str)
    
    def __init__(self, parent=None, width=220):
        super().__init__(parent)
        
        # 设置基本属性
        self.setFixedWidth(width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.active_tab = None
        self.tabs = []
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 30, 10, 10)
        self.layout.setSpacing(15)  # 增加按钮之间的间距
        
        # 设置侧边栏样式
        self.setStyleSheet("""
            ModernSidebar {
                background-color: #1a2530;  /* 更暗的背景色，增加与按钮的对比 */
                border-right: 1px solid #34495e;
            }
        """)
        
        # 创建标题标签
        title = QLabel("GameTrad 交易系统")
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #ffffff;  /* 纯白色文字 */
            padding: 10px;
            background-color: rgba(41, 128, 185, 0.6);  /* 更鲜明的蓝色背景 */
            border-radius: 5px;
            margin: 0px 5px;
            border: 1px solid rgba(255, 255, 255, 0.5);  /* 更明显的边框 */
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)
        self.layout.addSpacing(20)
        
        # 内容区域将由主窗口管理
        self.content_stack = None
    
    def set_content_widget(self, content_stack):
        """设置内容区域的堆叠部件"""
        self.content_stack = content_stack
    
    def add_tab(self, title, icon, tab_class, tab_params=None):
        """添加标签页"""
        tab_id = f"tab_{len(self.tabs)}"
        
        # 创建按钮带有渐变效果
        btn = QPushButton(f" {icon}  {title}")  # 添加额外空格增加图标和文字间距
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.7);  /* 更深的背景色，降低透明度 */
                color: #ffffff;  /* 纯白色文字 */
                border: none;
                border-radius: 5px;
                padding: 12px;
                margin: 3px 5px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;  /* 粗体文字 */
                letter-spacing: 0.5px;
                border-left: 2px solid rgba(255, 255, 255, 0.3);  /* 半透明白色左边框 */
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.7);  /* 蓝色背景，与选中状态相似 */
                color: #ffffff;
                border-left: 3px solid #ffffff;  /* 纯白色左边框 */
            }
            QPushButton:checked {
                background-color: rgba(52, 152, 219, 0.8);  /* 稍亮的蓝色背景 */
                color: #ffffff;
                font-weight: bold;
                border-left: 3px solid #ffffff;
                border-top: 1px solid rgba(255, 255, 255, 0.5);  /* 添加顶部边框增加立体感 */
                border-right: 1px solid rgba(255, 255, 255, 0.5);  /* 添加右侧边框增加立体感 */
                border-bottom: 1px solid rgba(255, 255, 255, 0.5);  /* 添加底部边框增加立体感 */
            }
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.switch_tab(tab_id))
        
        # 确保侧边栏按钮高度固定，但宽度可以填充整个侧边栏
        btn.setFixedHeight(40)  # 固定高度
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.layout.addWidget(btn)
        
        # 创建内容页
        tab_frame = QWidget()
        tab_params = tab_params or {}
        try:
            tab_content = tab_class(tab_frame, **tab_params)
        except Exception as e:
            print(f"标签页初始化错误: {e}")
            tab_content = None
        
        # 确保标签内容页可以自适应调整大小
        tab_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 保存信息
        self.tabs.append({
            'id': tab_id,
            'title': title,
            'button': btn,
            'widget': tab_frame,
            'content': tab_content
        })
        
        # 返回创建的组件，以便主窗口管理
        return tab_frame, tab_content
    
    def switch_tab(self, tab_id):
        """切换标签页"""
        # 更新按钮状态
        for tab in self.tabs:
            tab['button'].setChecked(tab['id'] == tab_id)
        
        # 查找目标标签页索引
        target_idx = -1
        for i, tab in enumerate(self.tabs):
            if tab['id'] == tab_id:
                target_idx = i
                break
        
        if target_idx >= 0 and self.content_stack:
            # 创建切换动画
            self.anim = QPropertyAnimation(self.content_stack, b"currentIndex")
            self.anim.setDuration(300)
            self.anim.setStartValue(self.content_stack.currentIndex())
            self.anim.setEndValue(target_idx)
            self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.anim.start()
            
            # 更新活动标签
            self.active_tab = tab_id
            
            # 发射信号
            self.tabChanged.emit(tab_id)
    
    def get_active_tab_content(self):
        """获取当前活动标签页的内容"""
        for tab in self.tabs:
            if tab['id'] == self.active_tab:
                return tab['content']
        return None 