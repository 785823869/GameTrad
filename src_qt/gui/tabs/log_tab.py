"""
操作日志标签页 - 显示和管理系统操作日志
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QComboBox, QHeaderView, QMessageBox,
                             QDateEdit, QSpinBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSlot, QDate, QTimer
from PyQt6.QtGui import QColor
from datetime import datetime
import json
import os
import csv

class LogTab(QWidget):
    """操作日志标签页"""
    
    def __init__(self, parent_frame, main_gui=None):
        super().__init__(parent_frame)
        self.main_gui = main_gui
        self.ui_manager = main_gui.ui_manager if main_gui else None
        
        # 日志数据
        self.log_data = []
        self.filtered_data = []
        self.logs_per_page = 50  # 每页显示的日志数量
        self.current_page = 1
        self.total_pages = 1
        
        # 搜索和过滤条件
        self.log_search_text = ""
        
        # 初始化UI
        self.init_ui()
        
        # 加载日志数据
        self.load_logs()
    
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
        
        title_label = QLabel("操作日志")
        title_label.setFont(self.ui_manager.title_font if self.ui_manager else QLabel().font())
        title_layout.addWidget(title_label, 1)  # 1是伸缩系数
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setFixedWidth(80)
        refresh_button.clicked.connect(self.refresh_logs)
        title_layout.addWidget(refresh_button)
        
        main_layout.addWidget(title_frame)
        
        # 搜索和工具栏
        toolbar_frame = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索区域
        search_label = QLabel("关键词:")
        toolbar_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.returnPressed.connect(self.search_logs)
        toolbar_layout.addWidget(self.search_input, 1)
        
        # 操作类型过滤
        type_label = QLabel("操作类型:")
        toolbar_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "添加", "修改", "删除", "导入", "导出", "查询", "其他"])
        self.type_combo.currentIndexChanged.connect(self.filter_logs)
        toolbar_layout.addWidget(self.type_combo)
        
        # 日期范围
        date_label = QLabel("日期:")
        toolbar_layout.addWidget(date_label)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))  # 默认显示最近一个月
        toolbar_layout.addWidget(self.date_from)
        
        date_to_label = QLabel(" 至 ")
        toolbar_layout.addWidget(date_to_label)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        toolbar_layout.addWidget(self.date_to)
        
        # 搜索按钮
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_logs)
        toolbar_layout.addWidget(search_button)
        
        main_layout.addWidget(toolbar_frame)
        
        # 操作按钮
        actions_frame = QWidget()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # 导出按钮
        export_button = QPushButton("导出CSV")
        export_button.clicked.connect(self.export_logs)
        actions_layout.addWidget(export_button)
        
        # 删除按钮
        delete_button = QPushButton("删除选中")
        delete_button.clicked.connect(self.delete_logs)
        actions_layout.addWidget(delete_button)
        
        # 删除全部按钮
        clear_button = QPushButton("清空日志")
        clear_button.clicked.connect(self.clear_logs)
        actions_layout.addWidget(clear_button)
        
        actions_layout.addStretch(1)  # 添加伸缩空间
        
        # 每页显示数量
        actions_layout.addWidget(QLabel("每页显示:"))
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["20", "50", "100", "200", "500"])
        self.page_size_combo.setCurrentText(str(self.logs_per_page))
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        actions_layout.addWidget(self.page_size_combo)
        
        main_layout.addWidget(actions_frame)
        
        # 日志表格
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["操作类型", "操作对象", "操作时间", "详细信息"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # 详细信息列可调整
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.log_table, 1)  # 1是伸缩系数
        
        # 分页控件
        pagination_frame = QWidget()
        pagination_layout = QHBoxLayout(pagination_frame)
        pagination_layout.setContentsMargins(0, 0, 0, 0)
        
        # 总记录数
        self.record_count_label = QLabel("总记录: 0")
        pagination_layout.addWidget(self.record_count_label)
        
        pagination_layout.addStretch(1)  # 添加伸缩空间
        
        # 分页控件
        self.prev_button = QPushButton("上一页")
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)
        
        # 页码输入
        pagination_layout.addWidget(QLabel("页码:"))
        
        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.setMaximum(1)
        self.page_input.valueChanged.connect(self.jump_to_page)
        pagination_layout.addWidget(self.page_input)
        
        self.page_count_label = QLabel("/ 1")
        pagination_layout.addWidget(self.page_count_label)
        
        self.next_button = QPushButton("下一页")
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        main_layout.addWidget(pagination_frame)
    
    def load_logs(self):
        """加载日志数据"""
        try:
            # 检查日志文件是否存在
            if os.path.exists('logs/operation_logs.json'):
                with open('logs/operation_logs.json', 'r', encoding='utf-8') as f:
                    self.log_data = json.load(f)
            else:
                # 确保目录存在
                os.makedirs('logs', exist_ok=True)
                # 创建空日志文件
                self.log_data = []
                with open('logs/operation_logs.json', 'w', encoding='utf-8') as f:
                    json.dump(self.log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"加载日志数据失败: {e}")
            self.log_data = []
        
        # 更新筛选后的数据
        self.filtered_data = self.log_data.copy()
        
        # 更新UI
        self.update_pagination()
        self.display_logs()
    
    def refresh_logs(self):
        """刷新日志数据"""
        self.load_logs()
    
    def search_logs(self):
        """搜索日志"""
        search_text = self.search_input.text().strip().lower()
        op_type = self.type_combo.currentText()
        date_from = self.date_from.date().toPyDate().strftime("%Y-%m-%d")
        date_to = self.date_to.date().toPyDate().strftime("%Y-%m-%d")
        
        # 保存搜索文本
        self.log_search_text = search_text
        
        # 根据筛选条件过滤日志
        self.filtered_data = []
        for log in self.log_data:
            # 检查日期范围
            log_date = log.get("timestamp", "").split(" ")[0]
            if log_date < date_from or log_date > date_to:
                continue
            
            # 检查操作类型
            if op_type != "全部" and log.get("op_type", "") != op_type:
                continue
            
            # 检查搜索文本
            if search_text:
                # 在所有字段中搜索
                found = False
                for key, value in log.items():
                    if isinstance(value, str) and search_text in value.lower():
                        found = True
                        break
                    elif isinstance(value, dict):
                        # 搜索嵌套的数据字典
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, str) and search_text in subvalue.lower():
                                found = True
                                break
                
                if not found:
                    continue
            
            # 通过所有筛选，添加到结果中
            self.filtered_data.append(log)
        
        # 重置到第一页
        self.current_page = 1
        
        # 更新UI
        self.update_pagination()
        self.display_logs()
    
    def filter_logs(self):
        """根据操作类型筛选日志"""
        self.search_logs()
    
    def display_logs(self):
        """显示当前页的日志"""
        # 清空表格
        self.log_table.setRowCount(0)
        
        # 计算当前页显示的日志范围
        start_idx = (self.current_page - 1) * self.logs_per_page
        end_idx = min(start_idx + self.logs_per_page, len(self.filtered_data))
        
        # 添加日志到表格
        for row, log in enumerate(self.filtered_data[start_idx:end_idx]):
            self.log_table.insertRow(row)
            
            # 操作类型
            op_type = log.get("op_type", "")
            type_item = QTableWidgetItem(op_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 0, type_item)
            
            # 操作对象
            tab_name = log.get("tab_name", "")
            tab_item = QTableWidgetItem(tab_name)
            tab_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 1, tab_item)
            
            # 操作时间
            timestamp = log.get("timestamp", "")
            time_item = QTableWidgetItem(timestamp)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 2, time_item)
            
            # 详细信息 - 将字典转为字符串
            data = log.get("data", {})
            if isinstance(data, dict):
                data_str = "\n".join([f"{k}: {v}" for k, v in data.items()])
            else:
                data_str = str(data)
                
            data_item = QTableWidgetItem(data_str)
            data_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.log_table.setItem(row, 3, data_item)
    
    def update_pagination(self):
        """更新分页信息"""
        total_records = len(self.filtered_data)
        self.total_pages = max(1, (total_records + self.logs_per_page - 1) // self.logs_per_page)
        
        # 确保当前页在有效范围内
        self.current_page = min(max(1, self.current_page), self.total_pages)
        
        # 更新页码输入控件
        self.page_input.setMaximum(self.total_pages)
        self.page_input.setValue(self.current_page)
        self.page_count_label.setText(f"/ {self.total_pages}")
        
        # 更新记录数量显示
        self.record_count_label.setText(f"总记录: {total_records}")
        
        # 更新按钮状态
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_pagination()
            self.display_logs()
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_pagination()
            self.display_logs()
    
    def jump_to_page(self, page):
        """跳转到指定页"""
        if page != self.current_page:
            self.current_page = page
            self.display_logs()
    
    def change_page_size(self, size_text):
        """更改每页显示数量"""
        self.logs_per_page = int(size_text)
        self.current_page = 1  # 重置到第一页
        self.update_pagination()
        self.display_logs()
    
    def export_logs(self):
        """导出日志到CSV文件"""
        if not self.filtered_data:
            QMessageBox.warning(self, "警告", "没有日志数据可导出")
            return
        
        # 打开文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if not file_path:
            return  # 用户取消操作
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(["操作类型", "操作对象", "操作时间", "详细信息"])
                
                # 写入数据
                for log in self.filtered_data:
                    op_type = log.get("op_type", "")
                    tab_name = log.get("tab_name", "")
                    timestamp = log.get("timestamp", "")
                    
                    # 将数据转换为字符串
                    data = log.get("data", {})
                    if isinstance(data, dict):
                        data_str = "; ".join([f"{k}: {v}" for k, v in data.items()])
                    else:
                        data_str = str(data)
                    
                    writer.writerow([op_type, tab_name, timestamp, data_str])
            
            QMessageBox.information(self, "成功", f"日志已导出到 {file_path}")
            
            # 记录导出操作
            if self.main_gui:
                self.main_gui.log_operation("导出", "操作日志", {"文件": file_path})
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出日志失败: {str(e)}")
    
    def delete_logs(self):
        """删除选中的日志"""
        selected_rows = sorted(set(item.row() for item in self.log_table.selectedItems()), reverse=True)
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要删除的日志")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 条日志记录吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # 计算原始索引
            start_idx = (self.current_page - 1) * self.logs_per_page
            
            # 删除选中的行
            deleted_indices = []
            for table_row in selected_rows:
                original_idx = start_idx + table_row
                if 0 <= original_idx < len(self.filtered_data):
                    # 记录要删除的日志在原始数据中的索引
                    log_to_delete = self.filtered_data[original_idx]
                    orig_idx = self.log_data.index(log_to_delete)
                    deleted_indices.append(orig_idx)
            
            # 从原始数据中删除，从大到小删除避免索引变化
            for idx in sorted(deleted_indices, reverse=True):
                if 0 <= idx < len(self.log_data):
                    del self.log_data[idx]
            
            # 保存更新后的日志
            with open('logs/operation_logs.json', 'w', encoding='utf-8') as f:
                json.dump(self.log_data, f, ensure_ascii=False, indent=2)
            
            # 重新应用筛选
            self.search_logs()
            
            QMessageBox.information(self, "成功", f"已删除 {len(deleted_indices)} 条日志记录")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除日志失败: {str(e)}")
    
    def clear_logs(self):
        """清空所有日志"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有日志记录吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # 清空日志
            self.log_data = []
            
            # 保存更新后的日志
            with open('logs/operation_logs.json', 'w', encoding='utf-8') as f:
                json.dump(self.log_data, f, ensure_ascii=False, indent=2)
            
            # 更新UI
            self.filtered_data = []
            self.update_pagination()
            self.display_logs()
            
            QMessageBox.information(self, "成功", "已清空所有日志记录")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空日志失败: {str(e)}") 