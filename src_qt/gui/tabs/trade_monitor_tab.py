"""
交易监控标签页 - 监控交易数据和价格趋势
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QComboBox, QHeaderView, QMessageBox,
                             QDateEdit, QSplitter, QGroupBox, QFileDialog,
                             QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSlot, QDate, QTimer, QBuffer
from PyQt6.QtGui import QColor, QGuiApplication
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
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

from datetime import datetime
from PIL import Image, ImageGrab
import io
import os
import json

from src_qt.gui.components.image_preview import QImagePreview
from src_qt.utils.ocr_utils import OCRUtils

class PriceHistoryChart(QWidget):
    """价格历史图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        
        # 添加到布局
        layout.addWidget(self.canvas)
        
        # 初始化空图表
        self.init_chart()
    
    def init_chart(self):
        """初始化图表"""
        self.axes.clear()
        self.axes.set_title('价格历史趋势')
        self.axes.set_xlabel('日期')
        self.axes.set_ylabel('价格 (元)')
        self.axes.grid(True, linestyle='--', alpha=0.7)
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_chart(self, dates, prices, item_name=''):
        """更新图表数据"""
        self.axes.clear()
        self.axes.plot(dates, prices, 'b-', marker='o', markersize=4)
        
        if item_name:
            self.axes.set_title(f'{item_name} 价格历史趋势')
        else:
            self.axes.set_title('价格历史趋势')
            
        self.axes.set_xlabel('日期')
        self.axes.set_ylabel('价格 (元)')
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        # 自动旋转日期标签以避免重叠
        plt.setp(self.axes.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()

class TradeMonitorTab(QWidget):
    """交易监控标签页"""
    
    def __init__(self, parent_frame, main_gui=None):
        super().__init__(parent_frame)
        self.main_gui = main_gui
        self.ui_manager = main_gui.ui_manager if main_gui else None
        self._pending_ocr_images = []  # 存储待识别的图片
        
        # 初始化UI
        self.init_ui()
        
        # 自动刷新计时器 (10分钟刷新一次)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_monitor)
        self.refresh_timer.start(600000)  # 600000毫秒 = 10分钟
    
    def init_ui(self):
        """初始化UI"""
        # 创建主布局 - 使用水平布局以支持右侧面板
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 左侧主要内容区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # 标题
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("交易监控")
        title_label.setFont(self.ui_manager.title_font if self.ui_manager else QLabel().font())
        title_layout.addWidget(title_label, 1)  # 1是伸缩系数
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setFixedWidth(80)
        refresh_button.clicked.connect(self.refresh_monitor)
        title_layout.addWidget(refresh_button)
        
        # 添加监控按钮
        add_button = QPushButton("添加监控")
        add_button.setFixedWidth(120)
        add_button.clicked.connect(self.add_monitor)
        title_layout.addWidget(add_button)
        
        left_layout.addWidget(title_frame)
        
        # 搜索和过滤区域
        search_frame = QWidget()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 市场选择
        market_label = QLabel("市场:")
        search_layout.addWidget(market_label)
        
        self.market_combo = QComboBox()
        self.market_combo.addItems(["全部", "DD373", "UU898", "5173", "7881", "其他"])
        self.market_combo.currentIndexChanged.connect(self.filter_monitor)
        search_layout.addWidget(self.market_combo)
        
        # 物品搜索
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入物品名称搜索...")
        self.search_input.returnPressed.connect(self.search_monitor)
        search_layout.addWidget(self.search_input, 1)
        
        # 排序选项
        sort_label = QLabel("排序:")
        search_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["物品名称", "当前价格", "昨日价格", "价格变化", "变化率"])
        self.sort_combo.currentIndexChanged.connect(self.sort_monitor)
        search_layout.addWidget(self.sort_combo)
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_monitor)
        search_layout.addWidget(search_button)
        
        left_layout.addWidget(search_frame)
        
        # 创建分割器，上部显示表格，下部显示图表
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 表格区域
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.monitor_table = QTableWidget()
        self.monitor_table.setColumnCount(7)
        self.monitor_table.setHorizontalHeaderLabels(["物品名称", "当前价格", "昨日价格", "价格变化", "变化率", "市场", "最后更新时间"])
        self.monitor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monitor_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.monitor_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.monitor_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        
        table_layout.addWidget(self.monitor_table)
        
        # 图表区域
        self.price_chart = PriceHistoryChart()
        
        # 添加到分割器
        splitter.addWidget(table_widget)
        splitter.addWidget(self.price_chart)
        
        # 设置初始分割比例
        splitter.setSizes([600, 400])
        
        left_layout.addWidget(splitter, 1)  # 1是伸缩系数
        
        # 右侧操作面板
        right_panel = QWidget()
        right_panel.setFixedWidth(260)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # 操作按钮组
        operations_group = QGroupBox("操作")
        operations_layout = QVBoxLayout(operations_group)
        
        refresh_btn = QPushButton("刷新监控")
        refresh_btn.clicked.connect(self.refresh_monitor)
        operations_layout.addWidget(refresh_btn)
        
        upload_ocr_btn = QPushButton("上传图片自动识别导入")
        upload_ocr_btn.clicked.connect(self.upload_ocr_import_monitor)
        operations_layout.addWidget(upload_ocr_btn)
        
        batch_ocr_btn = QPushButton("批量识别粘贴图片")
        batch_ocr_btn.clicked.connect(self.batch_ocr_import_monitor)
        operations_layout.addWidget(batch_ocr_btn)
        
        right_layout.addWidget(operations_group)
        
        # OCR预览区域
        ocr_group = QGroupBox("OCR图片预览")
        ocr_layout = QVBoxLayout(ocr_group)
        
        self.ocr_preview = QImagePreview(height=150)
        self.ocr_preview.set_callback(self.delete_ocr_image)
        ocr_layout.addWidget(self.ocr_preview)
        
        right_layout.addWidget(ocr_group)
        right_layout.addStretch(1)  # 添加弹性空间
        
        # 说明文本
        info_label = QLabel("提示: 使用Ctrl+V可直接粘贴剪贴板中的图片")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        info_label.setWordWrap(True)
        right_layout.addWidget(info_label)
        
        # 将左右面板添加到主布局
        main_layout.addWidget(left_panel, 3)  # 左侧占比较大
        main_layout.addWidget(right_panel, 1)  # 右侧占比较小
        
        # 安装事件过滤器以捕获全局键盘事件
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获全局键盘事件"""
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        if event.type() == QEvent.Type.KeyPress:
            key_event = event
            # 检测Ctrl+V
            if key_event.modifiers() & Qt.KeyboardModifier.ControlModifier and key_event.key() == Qt.Key.Key_V:
                self.paste_ocr_import_monitor()
                return True
        
        return super().eventFilter(obj, event)
    
    def refresh_monitor(self):
        """刷新监控数据"""
        # 清空表格
        self.monitor_table.setRowCount(0)
        
        # TODO: 从数据库或其他数据源加载监控数据
        # 临时使用示例数据
        sample_data = [
            ("女娲石", 4.0, 3.8, 0.2, 5.26, "DD373", "2023-05-25 15:30"),
            ("银两", 0.9, 0.85, 0.05, 5.88, "UU898", "2023-05-25 15:35"),
            ("龙角", 18.0, 19.0, -1.0, -5.26, "5173", "2023-05-25 15:40")
        ]
        
        # 添加数据到表格
        for row_idx, item_data in enumerate(sample_data):
            self.monitor_table.insertRow(row_idx)
            item_name, current, yesterday, change, change_rate, market, update_time = item_data
            
            # 物品名称
            name_item = QTableWidgetItem(item_name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monitor_table.setItem(row_idx, 0, name_item)
            
            # 当前价格
            current_item = QTableWidgetItem(f"¥{current:.2f}")
            current_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monitor_table.setItem(row_idx, 1, current_item)
            
            # 昨日价格
            yesterday_item = QTableWidgetItem(f"¥{yesterday:.2f}")
            yesterday_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monitor_table.setItem(row_idx, 2, yesterday_item)
            
            # 价格变化
            change_item = QTableWidgetItem(f"{change:+.2f}")
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 根据变化值设置颜色
            if change > 0:
                change_item.setForeground(QColor("green"))
            elif change < 0:
                change_item.setForeground(QColor("red"))
            self.monitor_table.setItem(row_idx, 3, change_item)
            
            # 变化率
            rate_item = QTableWidgetItem(f"{change_rate:+.2f}%")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 根据变化率设置颜色
            if change_rate > 0:
                rate_item.setForeground(QColor("green"))
            elif change_rate < 0:
                rate_item.setForeground(QColor("red"))
            self.monitor_table.setItem(row_idx, 4, rate_item)
            
            # 市场
            market_item = QTableWidgetItem(market)
            market_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monitor_table.setItem(row_idx, 5, market_item)
            
            # 最后更新时间
            time_item = QTableWidgetItem(update_time)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monitor_table.setItem(row_idx, 6, time_item)
    
    def search_monitor(self):
        """搜索监控记录"""
        search_text = self.search_input.text().strip().lower()
        
        # 遍历所有行
        for row in range(self.monitor_table.rowCount()):
            found = False
            # 在物品名称列中搜索
            item_name = self.monitor_table.item(row, 0).text().lower()
            
            if search_text in item_name:
                found = True
                
            # 隐藏不匹配的行
            self.monitor_table.setRowHidden(row, not found)
    
    def filter_monitor(self):
        """按市场筛选监控记录"""
        market_filter = self.market_combo.currentText()
        
        # 如果选择了"全部"，显示所有记录
        if market_filter == "全部":
            for row in range(self.monitor_table.rowCount()):
                self.monitor_table.setRowHidden(row, False)
            return
        
        # 遍历所有行
        for row in range(self.monitor_table.rowCount()):
            market = self.monitor_table.item(row, 5).text()
            # 隐藏不匹配的行
            self.monitor_table.setRowHidden(row, market != market_filter)
    
    def sort_monitor(self):
        """排序监控记录"""
        sort_column = self.sort_combo.currentIndex()
        
        if sort_column == 0:  # 物品名称
            self.monitor_table.sortItems(0, Qt.SortOrder.AscendingOrder)
        elif sort_column in [1, 2]:  # 价格列
            self.monitor_table.sortItems(sort_column, Qt.SortOrder.DescendingOrder)
        elif sort_column in [3, 4]:  # 变化列
            self.monitor_table.sortItems(sort_column, Qt.SortOrder.DescendingOrder)
    
    def add_monitor(self):
        """添加交易监控记录"""
        # 创建添加监控记录对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加监控记录")
        dialog.setMinimumWidth(400)
        
        # 创建表单布局
        layout = QFormLayout(dialog)
        
        # 物品名称输入
        item_name_input = QLineEdit()
        item_name_input.setPlaceholderText("输入物品名称...")
        layout.addRow("物品名称:", item_name_input)
        
        # 当前价格输入
        current_price_input = QDoubleSpinBox()
        current_price_input.setRange(0, 1000000)
        current_price_input.setDecimals(2)
        current_price_input.setSingleStep(1)
        layout.addRow("当前价格:", current_price_input)
        
        # 市场选择
        market_input = QComboBox()
        market_input.addItems(["DD373", "UU898", "5173", "7881", "其他"])
        layout.addRow("市场来源:", market_input)
        
        # 数量输入
        quantity_input = QSpinBox()
        quantity_input.setRange(1, 10000)
        layout.addRow("数量:", quantity_input)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # 获取输入的数据
                item_name = item_name_input.text().strip()
                current_price = current_price_input.value()
                market = market_input.currentText()
                quantity = quantity_input.value()
                
                # 验证数据
                if not item_name:
                    raise ValueError("物品名称不能为空")
                
                # TODO: 实际添加监控记录到数据库
                # self.main_gui.db.add_monitor_record(...)
                
                # 刷新表格显示
                self.refresh_monitor()
                
                QMessageBox.information(self, "成功", "监控记录添加成功！")
            except ValueError as e:
                QMessageBox.critical(self, "错误", str(e))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加监控记录失败: {str(e)}")
    
    def on_table_selection_changed(self):
        """表格选择变化时的处理"""
        # TODO: 实现选择行变化时的图表更新
        selected_items = self.monitor_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            item_name = self.monitor_table.item(selected_row, 0).text()
            
            # 临时示例数据
            import numpy as np
            from datetime import datetime, timedelta
            today = datetime.now()
            dates = [today - timedelta(days=i) for i in range(30, 0, -1)]
            prices = np.random.normal(4.0, 0.5, len(dates))  # 生成随机价格数据
            
            # 更新图表
            self.price_chart.update_chart(dates, prices, item_name)
    
    def upload_ocr_import_monitor(self):
        """上传图片进行OCR识别"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
            
        try:
            img = Image.open(file_path)
            self._pending_ocr_images.append(img)
            # 添加图片到预览组件
            self.ocr_preview.add_image(img)
            QMessageBox.information(self, "提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"图片加载失败: {str(e)}")
    
    def paste_ocr_import_monitor(self):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            clipboard = QGuiApplication.clipboard()
            pixmap = clipboard.pixmap()
            
            if not pixmap.isNull():
                # 转换QPixmap为PIL Image - 修复保存方法
                buffer = QBuffer()
                buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                pixmap.save(buffer, "PNG")
                buffer.seek(0)
                
                pil_img = Image.open(io.BytesIO(buffer.data().data()))
                
                self._pending_ocr_images.append(pil_img)
                # 添加图片到预览组件
                self.ocr_preview.add_image(pil_img)
                QMessageBox.information(self, "提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
            else:
                QMessageBox.information(self, "提示", "剪贴板中没有图片")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"粘贴图片失败: {str(e)}")
    
    def batch_ocr_import_monitor(self):
        """批量识别已添加的图片，识别后导入"""
        # 从预览组件获取图片列表
        ocr_images = self.ocr_preview.get_images()
        if not ocr_images:
            QMessageBox.information(self, "提示", "请先添加图片")
            return
        
        # 加载物品字典
        dict_items = self.load_item_dict()
        if not dict_items:
            QMessageBox.warning(self, "物品字典为空", 
                "物品字典未设置或内容为空，无法分割物品名。请在'物品字典管理'中添加物品名后重试。")
            return
            
        # 处理所有图片
        all_data = []
        for img in ocr_images:
            # 发送OCR请求
            text = OCRUtils.send_ocr_request(img)
            if not text:
                continue
                
            # 解析OCR结果
            data = OCRUtils.parse_monitor_ocr_text(text, dict_items)
            if isinstance(data, list) and data:
                all_data.extend(data)
            elif data:
                all_data.append(data)
        
        # 如果有数据，导入到数据库
        if all_data:
            # TODO: 连接实际数据库实现
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 导入成功后清除图片
            self.ocr_preview.clear_images()
            self._pending_ocr_images.clear()
            
            # 刷新表格
            self.refresh_monitor()
            
            # 显示导入结果
            QMessageBox.information(self, "成功", f"已成功识别并导入{len(all_data)}条监控记录！")
        else:
            QMessageBox.warning(self, "警告", "未能识别有效的监控记录！")
    
    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            self._pending_ocr_images.pop(idx)
    
    def load_item_dict(self):
        """加载物品字典"""
        # TODO: 实现从数据库或配置文件加载物品字典
        # 临时返回示例数据
        return ["女娲石", "银两", "龙角", "神魂", "星魂", "魔魂", "仙魂"] 