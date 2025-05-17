"""
OCR图片预览组件 - Qt版本
用于显示、管理和处理待OCR识别的图片
"""
from PyQt6.QtWidgets import (QWidget, QScrollArea, QFrame, QLabel, QPushButton, 
                            QHBoxLayout, QVBoxLayout, QSizePolicy, QDialog)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import io

class ImagePreviewItem(QFrame):
    """单个图片预览项"""
    deleteClicked = pyqtSignal(int)  # 删除信号
    previewClicked = pyqtSignal(int)  # 预览信号
    
    def __init__(self, image, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.image = image
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        # 设置边框和样式
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            ImagePreviewItem {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin: 2px;
            }
            ImagePreviewItem:hover {
                border: 1px solid #3498db;
            }
        """)
        
        # 垂直布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 创建缩略图
        img_bytes = io.BytesIO()
        thumbnail = self.image.copy()
        thumbnail.thumbnail((100, 100))
        thumbnail.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        q_image = QImage.fromData(img_bytes.getvalue())
        pixmap = QPixmap.fromImage(q_image)
        
        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(100, 100)
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_label.mousePressEvent = self.on_image_click
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setFixedWidth(80)
        self.delete_button.clicked.connect(self.on_delete_click)
        
        # 添加到布局
        layout.addWidget(self.image_label)
        layout.addWidget(self.delete_button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def on_delete_click(self):
        """处理删除按钮点击"""
        self.deleteClicked.emit(self.index)
    
    def on_image_click(self, event):
        """处理图片点击"""
        self.previewClicked.emit(self.index)


class ImagePreviewDialog(QDialog):
    """图片预览对话框"""
    
    def __init__(self, image, index, parent=None):
        super().__init__(parent)
        self.image = image
        self.index = index
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"图片预览 #{self.index + 1}")
        self.resize(800, 600)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 创建图片标签
        img_bytes = io.BytesIO()
        display_img = self.image.copy()
        # 等比例缩放图片以适应对话框
        display_img.thumbnail((780, 560))
        display_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        q_image = QImage.fromData(img_bytes.getvalue())
        pixmap = QPixmap.fromImage(q_image)
        
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.setFixedWidth(100)
        self.close_button.clicked.connect(self.close)
        
        # 添加到布局
        layout.addWidget(self.image_label)
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)


class QImagePreview(QWidget):
    """OCR图片预览组件 - Qt版本"""
    
    def __init__(self, parent=None, height=150):
        super().__init__(parent)
        self.images = []  # 存储原始图片对象列表
        self.image_items = []  # 存储预览项对象
        self.delete_callback = None  # 删除回调函数
        self.setup_ui(height)
        
    def setup_ui(self, height):
        """设置UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumHeight(height)
        self.scroll_area.setMaximumHeight(height)
        
        # 创建内容容器
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)
        
        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.scroll_content)
        
        # 初始提示标签
        self.empty_label = QLabel("暂无图片，请添加或粘贴图片")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-style: italic;")
        self.scroll_layout.addWidget(self.empty_label)
        
        # 添加到主布局
        main_layout.addWidget(self.scroll_area)
    
    def add_image(self, image):
        """添加图片到预览"""
        # 确保是PIL图像对象
        if not isinstance(image, Image.Image):
            raise TypeError("图片必须是PIL Image对象")
        
        # 添加到列表
        self.images.append(image)
        
        # 清除空提示
        if self.empty_label.isVisible():
            self.empty_label.hide()
        
        # 刷新显示
        self.refresh()
        
    def delete_image(self, idx):
        """删除指定索引的图片"""
        if 0 <= idx < len(self.images):
            self.images.pop(idx)
            self.refresh()
            
            # 显示空提示
            if not self.images:
                self.empty_label.show()
            
            # 调用回调
            if self.delete_callback:
                self.delete_callback(idx)
    
    def set_callback(self, callback):
        """设置删除图片的回调函数"""
        self.delete_callback = callback
    
    def get_images(self):
        """获取所有图片列表"""
        return self.images.copy()
    
    def clear_images(self):
        """清除所有图片"""
        self.images.clear()
        self.refresh()
        self.empty_label.show()
    
    def show_preview(self, idx):
        """显示大图预览"""
        if 0 <= idx < len(self.images):
            dialog = ImagePreviewDialog(self.images[idx], idx, self)
            dialog.exec()
    
    def refresh(self):
        """刷新图片显示"""
        # 清除所有当前显示的图片项
        for item in self.image_items:
            self.scroll_layout.removeWidget(item)
            item.setParent(None)  # 从父组件中分离
            item.deleteLater()  # 安排删除
        
        self.image_items.clear()
        
        # 添加图片项
        for idx, image in enumerate(self.images):
            item = ImagePreviewItem(image, idx)
            item.deleteClicked.connect(self.delete_image)
            item.previewClicked.connect(self.show_preview)
            self.scroll_layout.addWidget(item)
            self.image_items.append(item) 