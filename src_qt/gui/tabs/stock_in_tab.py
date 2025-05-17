"""
入库管理标签页 - 管理物品入库记录
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QComboBox, QHeaderView, QMessageBox,
                             QDateEdit, QGroupBox, QFileDialog, QSizePolicy,
                             QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit)
from PyQt6.QtCore import Qt, pyqtSlot, QDate, QBuffer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QGuiApplication
from datetime import datetime
from PIL import Image
import io

from src_qt.gui.components.image_preview import QImagePreview
from src_qt.utils.ocr_utils import OCRUtils
from src_qt.utils.responsive_layout import LayoutMode, WindowSizeThreshold, ResponsiveLayoutManager, CollapsiblePanel

class StockInTab(QWidget):
    """入库管理标签页"""
    
    def __init__(self, parent_frame, main_gui=None):
        super().__init__(parent_frame)
        self.main_gui = main_gui
        self.ui_manager = main_gui.ui_manager if main_gui else None
        self._pending_ocr_images = []  # 存储待识别的图片
        
        # 当前布局模式
        self.current_layout_mode = LayoutMode.NORMAL
        
        # 右侧面板状态
        self.right_panel_visible = True
        self.right_panel_animation = None
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 创建主布局 - 使用水平布局以支持右侧面板
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 左侧主要内容区域
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(15)
        
        # 标题和控制区域
        self.init_header()
        
        # 搜索和过滤区域
        self.init_search_area()
        
        # 表格
        self.init_table()
        
        # 右侧操作面板
        self.init_right_panel()
        
        # 设置左右面板的自适应比例
        self.main_layout.addWidget(self.left_panel, 3)  # 左侧占比较大
        self.main_layout.addWidget(self.right_panel, 1)  # 右侧占比较小
        
        # 确保左侧面板是可扩展的
        self.left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 安装事件过滤器以捕获全局键盘事件
        self.installEventFilter(self)
    
    def init_header(self):
        """初始化标题区域"""
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QLabel("入库管理")
        title_label.setFont(self.ui_manager.title_font if self.ui_manager else QLabel().font())
        title_layout.addWidget(title_label, 1)  # 1是伸缩系数
        
        # 右侧面板切换按钮（默认隐藏，只在紧凑模式下显示）
        self.toggle_panel_btn = QPushButton("◀ 显示操作面板")
        self.ui_manager.apply_fixed_button_size(self.toggle_panel_btn, "medium")
        self.toggle_panel_btn.clicked.connect(self.toggle_right_panel)
        self.toggle_panel_btn.setVisible(False)  # 初始时隐藏
        title_layout.addWidget(self.toggle_panel_btn)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(refresh_button, "small")
        else:
            refresh_button.setFixedWidth(80)
        refresh_button.clicked.connect(self.refresh_stock_in)
        title_layout.addWidget(refresh_button)
        
        # 添加入库记录按钮
        add_button = QPushButton("添加入库记录")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(add_button, "medium")
        else:
            add_button.setFixedWidth(120)
        add_button.clicked.connect(self.add_stock_in)
        title_layout.addWidget(add_button)
        
        self.left_layout.addWidget(title_frame)
    
    def init_search_area(self):
        """初始化搜索区域"""
        self.search_frame = QWidget()
        search_layout = QHBoxLayout(self.search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 日期筛选
        date_label = QLabel("日期:")
        search_layout.addWidget(date_label)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))  # 默认显示最近一个月
        search_layout.addWidget(self.date_from)
        
        date_to_label = QLabel(" 至 ")
        search_layout.addWidget(date_to_label)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        search_layout.addWidget(self.date_to)
        
        # 物品搜索
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入物品名称搜索...")
        self.search_input.returnPressed.connect(self.search_stock_in)
        search_layout.addWidget(self.search_input, 1)
        
        # 排序选项
        sort_label = QLabel("排序:")
        search_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["日期", "物品名称", "数量", "单价", "总价"])
        self.sort_combo.currentIndexChanged.connect(self.sort_stock_in)
        search_layout.addWidget(self.sort_combo)
        
        # 搜索按钮
        search_button = QPushButton("搜索")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(search_button, "small")
        else:
            search_button.setFixedWidth(80)
        search_button.clicked.connect(self.search_stock_in)
        search_layout.addWidget(search_button)
        
        self.left_layout.addWidget(self.search_frame)
        
        # 存储要在紧凑模式下隐藏的组件
        self.compact_hide_widgets = {
            "date_label": date_label,
            "date_from": self.date_from,
            "date_to_label": date_to_label,
            "date_to": self.date_to,
            "sort_label": sort_label,
            "sort_combo": self.sort_combo
        }
    
    def init_table(self):
        """初始化表格"""
        self.stock_in_table = QTableWidget()
        self.stock_in_table.setColumnCount(7)
        self.stock_in_table.setHorizontalHeaderLabels(["日期", "物品名称", "数量", "单价", "总价", "来源", "备注"])
        self.stock_in_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stock_in_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stock_in_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置表格为可扩展的，以便自适应窗口大小变化
        if self.ui_manager:
            self.ui_manager.apply_expandable_style_to_widget(self.stock_in_table)
        else:
            self.stock_in_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.left_layout.addWidget(self.stock_in_table, 1)  # 1是伸缩系数
    
    def init_right_panel(self):
        """初始化右侧面板"""
        self.right_panel = QWidget()
        self.right_panel.setFixedWidth(260)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # 操作按钮组
        operations_group = QGroupBox("操作")
        operations_layout = QVBoxLayout(operations_group)
        
        refresh_btn = QPushButton("刷新入库记录")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(refresh_btn, "medium")
        else:
            refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self.refresh_stock_in)
        operations_layout.addWidget(refresh_btn)
        
        upload_ocr_btn = QPushButton("上传图片自动识别导入")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(upload_ocr_btn, "large")
        else:
            upload_ocr_btn.setFixedWidth(160)
        upload_ocr_btn.clicked.connect(self.upload_ocr_import_stock_in)
        operations_layout.addWidget(upload_ocr_btn)
        
        batch_ocr_btn = QPushButton("批量识别粘贴图片")
        if self.ui_manager:
            self.ui_manager.apply_fixed_button_size(batch_ocr_btn, "large")
        else:
            batch_ocr_btn.setFixedWidth(160)
        batch_ocr_btn.clicked.connect(self.batch_ocr_import_stock_in)
        operations_layout.addWidget(batch_ocr_btn)
        
        right_layout.addWidget(operations_group)
        
        # OCR预览区域
        ocr_group = QGroupBox("OCR图片预览")
        ocr_layout = QVBoxLayout(ocr_group)
        
        self.ocr_preview = QImagePreview(height=150)
        self.ocr_preview.set_callback(self.delete_ocr_image)
        ocr_layout.addWidget(self.ocr_preview)
        
        # 设置OCR预览区域为可扩展的
        if self.ui_manager:
            self.ui_manager.apply_expandable_style_to_widget(ocr_group)
        else:
            ocr_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        right_layout.addWidget(ocr_group)
        right_layout.addStretch(1)  # 添加弹性空间
        
        # 说明文本
        info_label = QLabel("提示: 使用Ctrl+V可直接粘贴剪贴板中的图片")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        info_label.setWordWrap(True)
        right_layout.addWidget(info_label)
    
    def toggle_right_panel(self):
        """切换右侧面板的显示/隐藏状态"""
        self.right_panel_visible = not self.right_panel_visible
        
        if self.right_panel_visible:
            # 显示右侧面板
            self.right_panel.setVisible(True)
            self.toggle_panel_btn.setText("◀ 隐藏操作面板")
        else:
            # 隐藏右侧面板
            self.right_panel.setVisible(False)
            self.toggle_panel_btn.setText("▶ 显示操作面板")
    
    def update_layout_for_mode(self, layout_mode):
        """更新标签页布局以适应新的布局模式"""
        if self.current_layout_mode == layout_mode:
            return
            
        self.current_layout_mode = layout_mode
        
        # 更新主布局的边距
        if layout_mode == LayoutMode.COMPACT:
            self.main_layout.setContentsMargins(10, 10, 10, 10)
            self.main_layout.setSpacing(10)
            
            # 显示右侧面板切换按钮
            self.toggle_panel_btn.setVisible(True)
            
            # 隐藏部分搜索组件
            for widget in self.compact_hide_widgets.values():
                widget.setVisible(False)
            
            # 自动隐藏右侧面板
            if self.right_panel_visible:
                self.toggle_right_panel()
                
        elif layout_mode == LayoutMode.NORMAL:
            self.main_layout.setContentsMargins(15, 15, 15, 15)
            self.main_layout.setSpacing(15)
            
            # 隐藏右侧面板切换按钮
            self.toggle_panel_btn.setVisible(False)
            
            # 显示所有搜索组件
            for widget in self.compact_hide_widgets.values():
                widget.setVisible(True)
            
            # 如果右侧面板隐藏了，就显示它
            if not self.right_panel_visible:
                self.toggle_right_panel()
                
        else:  # EXPANDED
            self.main_layout.setContentsMargins(20, 20, 20, 20)
            self.main_layout.setSpacing(20)
            
            # 隐藏右侧面板切换按钮
            self.toggle_panel_btn.setVisible(False)
            
            # 显示所有搜索组件
            for widget in self.compact_hide_widgets.values():
                widget.setVisible(True)
            
            # 如果右侧面板隐藏了，就显示它
            if not self.right_panel_visible:
                self.toggle_right_panel()
        
        # 调整表格列视图
        self.adjust_table_columns_for_mode(layout_mode)
    
    def adjust_table_columns_for_mode(self, layout_mode):
        """根据布局模式调整表格列的显示"""
        if layout_mode == LayoutMode.COMPACT:
            # 紧凑模式下只显示关键列
            self.stock_in_table.setColumnHidden(5, True)  # 隐藏"来源"列
            self.stock_in_table.setColumnHidden(6, True)  # 隐藏"备注"列
        else:
            # 其他模式下显示所有列
            self.stock_in_table.setColumnHidden(5, False)
            self.stock_in_table.setColumnHidden(6, False)
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获全局键盘事件"""
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        if event.type() == QEvent.Type.KeyPress:
            key_event = event
            # 检测Ctrl+V
            if key_event.modifiers() & Qt.KeyboardModifier.ControlModifier and key_event.key() == Qt.Key.Key_V:
                self.paste_ocr_import_stock_in()
                return True
        
        return super().eventFilter(obj, event)
    
    def refresh_stock_in(self):
        """刷新入库记录"""
        # 清空表格
        self.stock_in_table.setRowCount(0)
        
        # TODO: 从数据库或其他数据源加载入库记录
        # 临时使用示例数据
        sample_data = [
            ("2023-05-01", "女娲石", 20, 3.5, 70, "淘宝", "特价购入"),
            ("2023-05-02", "银两", 5000, 0.8, 4000, "拍卖行", ""),
            ("2023-05-03", "龙角", 10, 15.0, 150, "游戏交易", "活动期间购入")
        ]
        
        # 添加数据到表格
        for row_idx, item_data in enumerate(sample_data):
            self.stock_in_table.insertRow(row_idx)
            for col_idx, value in enumerate(item_data):
                # 将数值格式化为字符串
                if isinstance(value, (int, float)):
                    if col_idx == 2:  # 数量列
                        text = f"{value:,}"
                    elif col_idx in [3, 4]:  # 价格列
                        text = f"¥{value:.2f}"
                    else:
                        text = str(value)
                else:
                    text = str(value)
                
                # 创建单元格项
                table_item = QTableWidgetItem(text)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stock_in_table.setItem(row_idx, col_idx, table_item)
    
    def search_stock_in(self):
        """搜索入库记录"""
        search_text = self.search_input.text().strip().lower()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        # 隐藏不符合条件的行
        for row in range(self.stock_in_table.rowCount()):
            # 检查日期范围
            date_cell = self.stock_in_table.item(row, 0).text()
            if date_cell < date_from or date_cell > date_to:
                self.stock_in_table.setRowHidden(row, True)
                continue
            
            # 检查物品名称
            item_name = self.stock_in_table.item(row, 1).text().lower()
            if search_text and search_text not in item_name:
                self.stock_in_table.setRowHidden(row, True)
            else:
                self.stock_in_table.setRowHidden(row, False)
    
    def sort_stock_in(self):
        """排序入库记录"""
        sort_column = self.sort_combo.currentIndex()
        self.stock_in_table.sortItems(sort_column, Qt.SortOrder.AscendingOrder)
    
    def add_stock_in(self):
        """添加入库记录"""
        # 创建添加入库记录对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加入库记录")
        dialog.setMinimumWidth(400)
        
        # 创建表单布局
        layout = QFormLayout(dialog)
        
        # 物品名称输入
        item_name_input = QLineEdit()
        item_name_input.setPlaceholderText("输入物品名称...")
        layout.addRow("物品名称:", item_name_input)
        
        # 数量输入
        quantity_input = QSpinBox()
        quantity_input.setRange(1, 10000)
        layout.addRow("数量:", quantity_input)
        
        # 单价输入
        unit_price_input = QDoubleSpinBox()
        unit_price_input.setRange(0, 1000000)
        unit_price_input.setDecimals(2)
        unit_price_input.setSingleStep(1)
        layout.addRow("单价:", unit_price_input)
        
        # 来源选择
        source_input = QComboBox()
        source_input.addItems(["淘宝", "拍卖行", "游戏交易", "其他"])
        source_input.setEditable(True)
        layout.addRow("来源:", source_input)
        
        # 日期选择
        date_input = QDateTimeEdit()
        date_input.setDateTime(datetime.now())
        date_input.setCalendarPopup(True)
        layout.addRow("日期:", date_input)
        
        # 备注输入
        remark_input = QLineEdit()
        remark_input.setPlaceholderText("可选")
        layout.addRow("备注:", remark_input)
        
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
                quantity = quantity_input.value()
                unit_price = unit_price_input.value()
                source = source_input.currentText()
                date_time = date_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
                remark = remark_input.text()
                
                # 验证数据
                if not item_name:
                    raise ValueError("物品名称不能为空")
                
                # 计算总价
                total_price = quantity * unit_price
                
                # TODO: 实际添加入库记录到数据库
                # self.main_gui.db.add_stock_in_record(...)
                
                # 刷新表格显示
                self.refresh_stock_in()
                
                QMessageBox.information(self, "成功", "入库记录添加成功！")
            except ValueError as e:
                QMessageBox.critical(self, "错误", str(e))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加入库记录失败: {str(e)}")
    
    def upload_ocr_import_stock_in(self):
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
    
    def paste_ocr_import_stock_in(self):
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
    
    def batch_ocr_import_stock_in(self):
        """批量识别已添加的图片，识别后导入"""
        # 从预览组件获取图片列表
        ocr_images = self.ocr_preview.get_images()
        if not ocr_images:
            QMessageBox.information(self, "提示", "请先添加图片")
            return
            
        # 处理所有图片
        all_data = []
        for img in ocr_images:
            # 发送OCR请求
            text = OCRUtils.send_ocr_request(img)
            if not text:
                continue
                
            # 解析OCR结果
            data = OCRUtils.parse_stock_in_ocr_text(text)
            if data:
                all_data.append(data)
        
        # 如果有数据，导入到数据库
        if all_data:
            # TODO: 连接实际数据库实现
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 导入成功后清除图片
            self.ocr_preview.clear_images()
            self._pending_ocr_images.clear()
            
            # 刷新表格
            self.refresh_stock_in()
            
            # 显示导入结果
            QMessageBox.information(self, "成功", f"已成功识别并导入{len(all_data)}条入库记录！")
        else:
            QMessageBox.warning(self, "警告", "未能识别有效的入库记录！")
    
    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            self._pending_ocr_images.pop(idx) 