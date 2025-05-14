import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QPushButton, QCheckBox, QProgressBar, 
                            QTextEdit, QTreeWidget, QTreeWidgetItem, QMessageBox, 
                            QGroupBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import threading
import webbrowser
from datetime import datetime
import os
from migrate_data import DataMigrator

class MigrationThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, selected_tables):
        super().__init__()
        self.selected_tables = selected_tables
        
    def run(self):
        try:
            self.migrator = DataMigrator()
            self.migrator.migrate_all_tables()
            self.finished.emit(True, "数据迁移完成！")
        except Exception as e:
            self.finished.emit(False, f"迁移失败: {str(e)}")

class MigrationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据库迁移工具")
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        layout = QVBoxLayout(main_widget)
        
        # 创建标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 创建各个页面
        self.setup_migration_page()
        self.setup_backup_page()
        self.setup_report_page()
        
        # 初始化迁移器
        self.migrator = None
        self.current_report = None
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
            }
            QTabBar::tab {
                background: #e1e1e1;
                border: 1px solid #cccccc;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

    def setup_migration_page(self):
        migration_widget = QWidget()
        layout = QVBoxLayout(migration_widget)
        
        # 数据库连接信息
        conn_group = QGroupBox("数据库连接信息")
        conn_layout = QVBoxLayout()
        
        local_db = QLabel("本地数据库: game_trading")
        remote_db = QLabel("远程数据库: OcrTrade (192.168.3.22)")
        
        conn_layout.addWidget(local_db)
        conn_layout.addWidget(remote_db)
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # 迁移选项
        options_group = QGroupBox("迁移选项")
        options_layout = QVBoxLayout()
        
        # 表选择
        self.tables_var = {}
        tables = [
            'stock_in',
            'stock_out',
            'trade_monitor',
            'inventory',
            'operation_logs',
            'item_dict',
            'silver_monitor'
        ]
        
        tables_layout = QHBoxLayout()
        for i, table in enumerate(tables):
            if i % 2 == 0:
                tables_layout = QHBoxLayout()
                options_layout.addLayout(tables_layout)
            
            checkbox = QCheckBox(table)
            checkbox.setChecked(True)
            self.tables_var[table] = checkbox
            tables_layout.addWidget(checkbox)
        
        # 全选/取消全选按钮
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        deselect_all_btn = QPushButton("取消全选")
        select_all_btn.clicked.connect(self.select_all_tables)
        deselect_all_btn.clicked.connect(self.deselect_all_tables)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        options_layout.addLayout(btn_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 迁移按钮
        self.migrate_btn = QPushButton("开始迁移")
        self.migrate_btn.clicked.connect(self.start_migration)
        layout.addWidget(self.migrate_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # 日志显示
        log_group = QGroupBox("迁移日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.tabs.addTab(migration_widget, "数据迁移")

    def setup_backup_page(self):
        backup_widget = QWidget()
        layout = QVBoxLayout(backup_widget)
        
        # 备份列表
        self.backup_tree = QTreeWidget()
        self.backup_tree.setHeaderLabels(["文件名", "时间", "大小"])
        self.backup_tree.setColumnWidth(0, 300)
        self.backup_tree.setColumnWidth(1, 200)
        self.backup_tree.setColumnWidth(2, 100)
        layout.addWidget(self.backup_tree)
        
        # 按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新列表")
        restore_btn = QPushButton("恢复选中备份")
        refresh_btn.clicked.connect(self.refresh_backup_list)
        restore_btn.clicked.connect(self.restore_selected_backup)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(restore_btn)
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(backup_widget, "备份管理")

    def setup_report_page(self):
        report_widget = QWidget()
        layout = QVBoxLayout(report_widget)
        
        # 报告列表
        self.report_tree = QTreeWidget()
        self.report_tree.setHeaderLabels(["文件名", "时间", "状态"])
        self.report_tree.setColumnWidth(0, 300)
        self.report_tree.setColumnWidth(1, 200)
        self.report_tree.setColumnWidth(2, 100)
        layout.addWidget(self.report_tree)
        
        # 按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新列表")
        view_btn = QPushButton("查看选中报告")
        refresh_btn.clicked.connect(self.refresh_report_list)
        view_btn.clicked.connect(self.view_selected_report)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(view_btn)
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(report_widget, "迁移报告")

    def select_all_tables(self):
        for checkbox in self.tables_var.values():
            checkbox.setChecked(True)

    def deselect_all_tables(self):
        for checkbox in self.tables_var.values():
            checkbox.setChecked(False)

    def log(self, message):
        self.log_text.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")

    def start_migration(self):
        # 获取选中的表
        selected_tables = [table for table, checkbox in self.tables_var.items() 
                         if checkbox.isChecked()]
        if not selected_tables:
            QMessageBox.warning(self, "警告", "请至少选择一个表进行迁移")
            return
        
        # 禁用按钮
        self.migrate_btn.setEnabled(False)
        
        # 清空日志
        self.log_text.clear()
        
        # 创建并启动迁移线程
        self.migration_thread = MigrationThread(selected_tables)
        self.migration_thread.log.connect(self.log)
        self.migration_thread.progress.connect(self.progress_bar.setValue)
        self.migration_thread.finished.connect(self.migration_finished)
        self.migration_thread.start()

    def migration_finished(self, success, message):
        self.migrate_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", message)
        self.refresh_report_list()

    def refresh_backup_list(self):
        self.backup_tree.clear()
        
        if not self.migrator:
            self.migrator = DataMigrator()
        
        backups = self.migrator.list_backups()
        for backup in backups:
            item = QTreeWidgetItem([
                backup["file"],
                backup["time"].strftime("%Y-%m-%d %H:%M:%S"),
                f"{backup['size']/1024:.1f} KB"
            ])
            self.backup_tree.addTopLevelItem(item)

    def restore_selected_backup(self):
        selected = self.backup_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请选择一个备份文件")
            return
        
        reply = QMessageBox.question(self, "确认", 
                                   "确定要恢复选中的备份吗？这将覆盖当前数据库。",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            backup_file = selected[0].text(0)
            backup_path = os.path.join("database_backups", backup_file)
            
            try:
                if self.migrator.restore_database(backup_path):
                    QMessageBox.information(self, "成功", "数据库恢复成功！")
                else:
                    QMessageBox.critical(self, "错误", "数据库恢复失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"恢复失败: {str(e)}")

    def refresh_report_list(self):
        self.report_tree.clear()
        
        report_dir = "database_backups"
        if not os.path.exists(report_dir):
            return
        
        for file in os.listdir(report_dir):
            if file.startswith("migration_report_") and file.endswith(".html"):
                file_path = os.path.join(report_dir, file)
                time_str = file[16:-5]  # 提取时间戳
                try:
                    time = datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                    item = QTreeWidgetItem([
                        file,
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        "完成"
                    ])
                    self.report_tree.addTopLevelItem(item)
                except ValueError:
                    continue

    def view_selected_report(self):
        selected = self.report_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请选择一个报告文件")
            return
        
        report_file = selected[0].text(0)
        report_path = os.path.join("database_backups", report_file)
        
        if os.path.exists(report_path):
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        else:
            QMessageBox.critical(self, "错误", "报告文件不存在")

def main():
    app = QApplication(sys.argv)
    window = MigrationGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 