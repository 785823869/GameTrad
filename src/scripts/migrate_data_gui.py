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
import json

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
        """刷新备份列表"""
        self.backup_tree.clear()
        backup_dir = os.path.join("data", "database_backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        for file in os.listdir(backup_dir):
            if file.endswith('.sql'):
                file_path = os.path.join(backup_dir, file)
                size = os.path.getsize(file_path)
                time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                item = QTreeWidgetItem([
                    file,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{size/1024/1024:.1f}MB"
                ])
                self.backup_tree.addTopLevelItem(item)

    def restore_selected_backup(self):
        """恢复选中的备份"""
        selected = self.backup_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要恢复的备份文件")
            return
        
        backup_file = selected[0].text(0)
        reply = QMessageBox.question(
            self,
            "确认恢复",
            f"确定要恢复备份 {backup_file} 吗？\n这将覆盖当前数据库中的所有数据！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.migrator.restore_database(
                    backup_file,
                    "192.168.3.22",
                    "root",
                    "123456",
                    "OcrTrade"
                ):
                    QMessageBox.information(self, "成功", "数据库恢复完成")
                else:
                    QMessageBox.warning(self, "失败", "数据库恢复失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"恢复过程中出错: {str(e)}")

    def refresh_report_list(self):
        """刷新报告列表"""
        self.report_tree.clear()
        backup_dir = os.path.join("data", "database_backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        for file in os.listdir(backup_dir):
            if file.endswith('.json'):
                file_path = os.path.join(backup_dir, file)
                size = os.path.getsize(file_path)
                time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                item = QTreeWidgetItem([
                    file,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{size/1024:.1f}KB"
                ])
                self.report_tree.addTopLevelItem(item)

    def view_selected_report(self):
        """查看选中的报告"""
        selected = self.report_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要查看的报告")
            return
        
        report_file = selected[0].text(0)
        report_path = os.path.join("data", "database_backups", report_file)
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 在浏览器中打开报告
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2196F3; }}
                    .info {{ margin: 10px 0; }}
                    .tables {{ margin-top: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f5f5f5; }}
                </style>
            </head>
            <body>
                <h1>迁移报告</h1>
                <div class="info">
                    <p><strong>时间:</strong> {report_data['timestamp']}</p>
                    <p><strong>状态:</strong> {report_data['status']}</p>
                </div>
                <div class="tables">
                    <h2>迁移的表</h2>
                    <table>
                        <tr><th>表名</th></tr>
                        {''.join(f'<tr><td>{table}</td></tr>' for table in report_data['tables'])}
                    </table>
                </div>
            </body>
            </html>
            """
            
            # 保存为临时HTML文件
            temp_html = os.path.join("data", "database_backups", "temp_report.html")
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # 在浏览器中打开
            webbrowser.open(f'file://{os.path.abspath(temp_html)}')
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查看报告时出错: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MigrationGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 