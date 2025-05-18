import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QPushButton, QCheckBox, QProgressBar, 
                            QTextEdit, QTreeWidget, QTreeWidgetItem, QMessageBox, 
                            QGroupBox, QScrollArea, QFrame, QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import threading
import webbrowser
from datetime import datetime
import os

# 设置导入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# 使用绝对导入
from src.scripts.migrate_data import DataMigrator
import json

# 导入项目的数据库管理器，获取当前连接信息
try:
    from src.core.db_manager import DatabaseManager
    HAS_DB_MANAGER = True
except ImportError:
    HAS_DB_MANAGER = False

class MigrationThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, source_config, target_config, selected_tables):
        super().__init__()
        self.source_config = source_config
        self.target_config = target_config
        self.selected_tables = selected_tables
        self.migrator = DataMigrator()
        
    def run(self):
        try:
            self.log.emit("初始化迁移器...")
            
            # 确保端口是整数
            source_port = self.source_config['port']
            if source_port is None or not isinstance(source_port, int):
                try:
                    source_port = int(source_port) if source_port else 3306
                except:
                    source_port = 3306
                    
            target_port = self.target_config['port']
            if target_port is None or not isinstance(target_port, int):
                try:
                    target_port = int(target_port) if target_port else 33306
                except:
                    target_port = 33306
            
            # 检查表结构
            self.log.emit("检查表结构...")
            try:
                self.check_and_create_tables()
                self.log.emit("表结构检查完成")
            except Exception as e:
                self.log.emit(f"表结构检查失败: {str(e)}")
                # 继续执行，因为migrate_all_tables会自动创建表
            
            # 调用迁移方法，传入源和目标配置
            self.log.emit("准备迁移数据...")
            success = self.migrator.migrate_all_tables(
                local_db=self.source_config['db'], 
                local_user=self.source_config['user'],
                local_pass=self.source_config['passwd'],
                remote_db=self.target_config['db'],
                remote_ip=self.target_config['host'],
                remote_user=self.target_config['user'],
                remote_pass=self.target_config['passwd'],
                selected_tables=self.selected_tables,
                local_host=self.source_config['host'],
                local_port=source_port,
                remote_port=target_port
            )
            
            if success:
                self.log.emit("所有数据迁移成功！")
                self.finished.emit(True, "数据迁移完成！")
            else:
                self.log.emit("数据迁移过程中出现错误，请查看日志。")
                self.finished.emit(False, "数据迁移过程中出现错误，请查看日志。")
                
        except Exception as e:
            error_msg = str(e)
            self.log.emit(f"迁移失败: {error_msg}")
            
            # 提供更有用的失败信息
            if "Can't connect to MySQL server" in error_msg:
                self.log.emit("可能原因: 无法连接到MySQL服务器，请检查网络连接和服务器状态。")
            elif "Access denied" in error_msg:
                self.log.emit("可能原因: 访问被拒绝，请检查用户名和密码。")
            elif "Unknown database" in error_msg:
                self.log.emit("可能原因: 数据库不存在，请先创建数据库或勾选自动创建选项。")
                
            self.finished.emit(False, f"迁移失败: {error_msg}")
            
    def check_and_create_tables(self):
        """检查并创建必要的表结构"""
        import MySQLdb
        
        # 确保端口是整数
        source_port = self.source_config['port']
        if source_port is None or not isinstance(source_port, int):
            try:
                source_port = int(source_port) if source_port else 3306
            except:
                source_port = 3306
                
        target_port = self.target_config['port']
        if target_port is None or not isinstance(target_port, int):
            try:
                target_port = int(target_port) if target_port else 33306
            except:
                target_port = 33306
        
        # 连接到目标数据库
        target_conn = MySQLdb.connect(
            host=self.target_config['host'],
            port=target_port,
            user=self.target_config['user'],
            passwd=self.target_config['passwd'],
            db=self.target_config['db'],
            charset="utf8mb4"
        )
        target_cursor = target_conn.cursor()
        
        # 连接到源数据库
        source_conn = MySQLdb.connect(
            host=self.source_config['host'],
            port=source_port,
            user=self.source_config['user'],
            passwd=self.source_config['passwd'],
            db=self.source_config['db'],
            charset="utf8mb4"
        )
        source_cursor = source_conn.cursor()
        
        try:
            # 获取选中的表
            for table in self.selected_tables:
                # 检查目标数据库表是否存在
                target_cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not target_cursor.fetchone():
                    self.log.emit(f"表 {table} 在目标数据库中不存在，正在创建...")
                    
                    # 从源数据库获取表结构
                    source_cursor.execute(f"SHOW CREATE TABLE {table}")
                    create_table_sql = source_cursor.fetchone()[1]
                    
                    # 在目标数据库执行创建表
                    target_cursor.execute(create_table_sql)
                    target_conn.commit()
                    
                    self.log.emit(f"表 {table} 创建成功")
        finally:
            # 关闭连接
            source_cursor.close()
            source_conn.close()
            target_cursor.close()
            target_conn.close()

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
        self.migrator = DataMigrator()
        self.current_report = None
        
        # 加载当前数据库连接信息
        self.load_current_db_info()
        
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

    def load_current_db_info(self):
        """加载当前应用程序使用的数据库连接信息"""
        if HAS_DB_MANAGER:
            try:
                # 创建临时DatabaseManager实例获取连接信息
                db_manager = DatabaseManager()
                # 获取连接方法的源代码
                import inspect
                source = inspect.getsource(db_manager.get_connection)
                
                # 提取连接参数（通过简单解析源代码）
                self.current_db_info = {
                    'host': None,
                    'port': None,
                    'user': None,
                    'passwd': None,
                    'db': None
                }
                
                # 解析源代码提取参数
                for line in source.splitlines():
                    line = line.strip()
                    for key in self.current_db_info.keys():
                        if f"{key}=" in line or f"{key} =" in line:
                            # 提取参数值
                            start_pos = line.find('"') if '"' in line else line.find("'")
                            end_pos = line.rfind('"') if '"' in line else line.rfind("'")
                            if start_pos > 0 and end_pos > start_pos:
                                self.current_db_info[key] = line[start_pos+1:end_pos]
                            elif key == 'port' and '=' in line:
                                # 提取数字参数
                                value = line.split('=')[1].strip().rstrip(',')
                                try:
                                    self.current_db_info[key] = int(value)
                                except:
                                    pass
                
                print(f"当前数据库连接信息: {self.current_db_info}")
                
                # 更新界面
                if hasattr(self, 'source_host_input'):
                    # 使用远程数据库作为源，因为本地可能没有MySQL服务器
                    self.source_host_input.setText(self.current_db_info['host'] or "sql.didiba.uk")
                    self.source_port_input.setText(str(self.current_db_info['port'] or "33306"))
                    self.source_user_input.setText(self.current_db_info['user'] or "root")
                    self.source_passwd_input.setText(self.current_db_info['passwd'] or "")
                    self.source_db_input.setText(self.current_db_info['db'] or "OcrTrade")
                
            except Exception as e:
                print(f"读取当前数据库连接信息失败: {e}")
                self.current_db_info = {
                    'host': 'sql.didiba.uk',  # 默认使用远程服务器
                    'port': 33306,
                    'user': 'root',
                    'passwd': '',
                    'db': 'OcrTrade'
                }
        else:
            self.current_db_info = {
                'host': 'sql.didiba.uk',  # 默认使用远程服务器
                'port': 33306,
                'user': 'root',
                'passwd': '',
                'db': 'OcrTrade'
            }

    def setup_migration_page(self):
        migration_widget = QWidget()
        layout = QVBoxLayout(migration_widget)
        
        # 添加帮助按钮
        help_layout = QHBoxLayout()
        help_btn = QPushButton("帮助")
        help_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        help_btn.clicked.connect(self.show_help)
        help_layout.addStretch()
        help_layout.addWidget(help_btn)
        layout.addLayout(help_layout)
        
        # 数据库连接信息组
        source_group = QGroupBox("源数据库（当前连接的数据库）")
        source_layout = QFormLayout()
        
        self.source_host_input = QLineEdit()
        self.source_port_input = QLineEdit()
        self.source_user_input = QLineEdit()
        self.source_passwd_input = QLineEdit()
        self.source_passwd_input.setEchoMode(QLineEdit.Password)
        self.source_db_input = QLineEdit()
        
        source_layout.addRow("主机:", self.source_host_input)
        source_layout.addRow("端口:", self.source_port_input)
        source_layout.addRow("用户名:", self.source_user_input)
        source_layout.addRow("密码:", self.source_passwd_input)
        source_layout.addRow("数据库名:", self.source_db_input)
        
        source_test_btn = QPushButton("测试连接")
        source_test_btn.clicked.connect(self.test_source_connection)
        source_layout.addRow("", source_test_btn)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # 目标数据库信息组
        target_group = QGroupBox("目标数据库（迁移数据的目标）")
        self.target_layout = QFormLayout()  # 保存为实例变量以便在其他方法中访问
        
        self.target_host_input = QLineEdit("sql.didiba.uk")
        self.target_port_input = QLineEdit("33306")
        self.target_user_input = QLineEdit("root")
        self.target_passwd_input = QLineEdit()
        self.target_passwd_input.setEchoMode(QLineEdit.Password)
        self.target_db_input = QLineEdit("OcrTrade")
        
        # 添加一个新的输入框，用于创建新数据库
        self.new_db_input = QLineEdit()
        self.new_db_input.setPlaceholderText("例如: OcrTrade_Backup")
        
        self.target_layout.addRow("主机:", self.target_host_input)
        self.target_layout.addRow("端口:", self.target_port_input)
        self.target_layout.addRow("用户名:", self.target_user_input)
        self.target_layout.addRow("密码:", self.target_passwd_input)
        self.target_layout.addRow("数据库名:", self.target_db_input)
        self.target_layout.addRow("新数据库名(可选):", self.new_db_input)
        
        # 添加创建新数据库的按钮
        create_db_btn = QPushButton("创建新数据库")
        create_db_btn.clicked.connect(self.create_new_database)
        self.target_layout.addRow("", create_db_btn)
        
        # 添加自动创建数据库复选框
        self.auto_create_db = QCheckBox("自动创建数据库和表结构（如果不存在）")
        self.auto_create_db.setChecked(True)
        self.target_layout.addRow("", self.auto_create_db)
        
        target_test_btn = QPushButton("测试连接")
        target_test_btn.clicked.connect(self.test_target_connection)
        self.target_layout.addRow("", target_test_btn)
        
        target_group.setLayout(self.target_layout)
        layout.addWidget(target_group)
        
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
        
        # 填充默认值
        self.load_current_db_info()

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

    def get_source_config(self):
        """获取源数据库配置"""
        return {
            'host': self.source_host_input.text(),
            'port': int(self.source_port_input.text() or "3306"),
            'user': self.source_user_input.text(),
            'passwd': self.source_passwd_input.text(),
            'db': self.source_db_input.text()
        }
        
    def get_target_config(self):
        """获取目标数据库配置"""
        return {
            'host': self.target_host_input.text(),
            'port': int(self.target_port_input.text() or "3306"),
            'user': self.target_user_input.text(),
            'passwd': self.target_passwd_input.text(),
            'db': self.target_db_input.text()
        }

    def test_source_connection(self):
        """测试源数据库连接"""
        config = self.get_source_config()
        self.test_connection(config, "源数据库")
        
    def test_target_connection(self):
        """测试目标数据库连接"""
        config = self.get_target_config()
        self.test_connection(config, "目标数据库")
        
    def test_connection(self, config, db_type):
        """测试数据库连接"""
        self.log(f"测试{db_type}连接...")
        try:
            # 确保端口是整数
            port = config['port']
            if port is None or not isinstance(port, int):
                try:
                    port = int(port) if port else (33306 if db_type == "目标数据库" else 3306)
                except:
                    port = 33306 if db_type == "目标数据库" else 3306
            
            import MySQLdb
            conn = MySQLdb.connect(
                host=config['host'],
                port=port,
                user=config['user'],
                passwd=config['passwd'],
                db=config['db'],
                charset="utf8mb4",
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            self.log(f"{db_type}连接成功！MySQL版本: {version[0]}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            self.log(f"{db_type}表: {[table[0] for table in tables]}")
            
            cursor.close()
            conn.close()
            
            QMessageBox.information(self, "连接测试", f"{db_type}连接成功！")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"{db_type}连接失败: {error_msg}")
            
            help_msg = ""
            if "Can't connect" in error_msg and "localhost" in error_msg:
                help_msg = "• 请确保MySQL服务已启动\n• 检查主机名是否正确（可能需要使用IP地址而非localhost）\n• 确认端口号是否正确（默认为3306）"
            elif "Access denied" in error_msg:
                help_msg = "• 用户名或密码可能不正确\n• 确认该用户是否有权限访问指定的数据库"
            elif "Unknown database" in error_msg:
                help_msg = "• 指定的数据库不存在\n• 您可以勾选下方的'自动创建数据库'选项"
                # 添加自动创建数据库选项
                if db_type == "目标数据库" and not hasattr(self, 'auto_create_db'):
                    self.auto_create_db = QCheckBox("自动创建数据库和表结构")
                    self.auto_create_db.setChecked(True)
                    if hasattr(self, 'target_layout'):
                        self.target_layout.addRow("", self.auto_create_db)
            
            detail_msg = f"{db_type}连接失败: {error_msg}\n\n可能的原因和解决方案:\n{help_msg}"
            
            msg_box = QMessageBox(QMessageBox.Warning, "连接测试", f"{db_type}连接失败")
            msg_box.setDetailedText(detail_msg)
            msg_box.exec_()
            return False

    def create_new_database(self):
        """创建新数据库"""
        new_db_name = self.new_db_input.text().strip()
        if not new_db_name:
            QMessageBox.warning(self, "警告", "请输入新数据库名")
            return
            
        # 获取目标数据库配置
        config = self.get_target_config()
        
        try:
            self.log(f"正在尝试创建新数据库: {new_db_name}...")
            import MySQLdb
            
            # 连接到MySQL服务器（不指定数据库）
            conn = MySQLdb.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                passwd=config['passwd'],
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            
            # 检查数据库是否已存在
            cursor.execute(f"SHOW DATABASES LIKE '{new_db_name}'")
            if cursor.fetchone():
                self.log(f"数据库 {new_db_name} 已存在")
                QMessageBox.information(self, "提示", f"数据库 {new_db_name} 已存在")
            else:
                # 创建新数据库
                cursor.execute(f"CREATE DATABASE `{new_db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.commit()
                self.log(f"数据库 {new_db_name} 创建成功")
                
                # 更新目标数据库输入框
                self.target_db_input.setText(new_db_name)
                
                QMessageBox.information(self, "成功", f"数据库 {new_db_name} 创建成功，并已设置为目标数据库")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"创建数据库失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"创建数据库失败: {error_msg}")
            
    def start_migration(self):
        # 获取数据库配置
        source_config = self.get_source_config()
        target_config = self.get_target_config()
        
        # 检查源数据库和目标数据库是否相同
        if (source_config['host'] == target_config['host'] and
            source_config['port'] == target_config['port'] and
            source_config['db'] == target_config['db']):
            if not QMessageBox.question(
                self,
                "确认操作",
                "源数据库和目标数据库相同，这将导致数据被复制到同一个数据库中。\n\n您确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            ) == QMessageBox.Yes:
                return
        
        # 如果启用了自动创建数据库，先检查并创建目标数据库
        if hasattr(self, 'auto_create_db') and self.auto_create_db.isChecked():
            try:
                self.log("检查目标数据库是否存在，如不存在则自动创建...")
                import MySQLdb
                
                # 先不指定数据库名连接到服务器
                conn = MySQLdb.connect(
                    host=target_config['host'],
                    port=target_config['port'],
                    user=target_config['user'],
                    passwd=target_config['passwd'],
                    charset="utf8mb4",
                    connect_timeout=5
                )
                cursor = conn.cursor()
                
                # 检查数据库是否存在
                cursor.execute(f"SHOW DATABASES LIKE '{target_config['db']}'")
                if not cursor.fetchone():
                    self.log(f"数据库 {target_config['db']} 不存在，正在创建...")
                    cursor.execute(f"CREATE DATABASE `{target_config['db']}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    self.log(f"数据库 {target_config['db']} 创建成功")
                
                cursor.close()
                conn.close()
            except Exception as e:
                self.log(f"尝试创建数据库时出错: {e}")
                QMessageBox.warning(self, "警告", f"无法自动创建数据库，您可能需要手动创建: {str(e)}")
        
        # 测试连接
        source_connected = self.test_connection(source_config, "源数据库")
        target_connected = self.test_connection(target_config, "目标数据库")
        
        if not source_connected:
            # 通常源数据库连接失败，意味着本地没有MySQL服务或用户凭据错误
            error_message = "源数据库连接失败。\n\n可能原因：\n" + \
                            "1. 本地MySQL服务未运行\n" + \
                            "2. 用户名或密码不正确\n" + \
                            "3. 指定的数据库不存在\n\n" + \
                            "建议：\n" + \
                            "- 确认MySQL已安装并运行\n" + \
                            "- 检查数据库连接参数\n" + \
                            "- 使用MySQL命令行工具验证能否连接"
            QMessageBox.critical(self, "连接错误", error_message)
            return
        
        if not target_connected:
            error_message = "目标数据库连接失败。\n\n可能原因：\n" + \
                            "1. 目标服务器无法访问（网络问题）\n" + \
                            "2. 用户名或密码不正确\n" + \
                            "3. 指定的数据库不存在\n\n" + \
                            "建议：\n" + \
                            "- 确认网络连接正常\n" + \
                            "- 检查服务器地址和端口\n" + \
                            "- 验证用户凭据\n" + \
                            "- 勾选「自动创建数据库」选项"
            QMessageBox.critical(self, "连接错误", error_message)
            return
        
        # 获取选中的表
        selected_tables = [table for table, checkbox in self.tables_var.items() 
                         if checkbox.isChecked()]
        if not selected_tables:
            QMessageBox.warning(self, "警告", "请至少选择一个表进行迁移")
            return
        
        # 确认迁移
        reply = QMessageBox.question(
            self,
            "确认迁移",
            f"确定要将数据从源数据库迁移到目标数据库吗？\n这将可能覆盖目标数据库的数据。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        # 禁用按钮
        self.migrate_btn.setEnabled(False)
        
        # 清空日志
        self.log_text.clear()
        self.log("开始数据迁移...")
        self.log(f"迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建并启动迁移线程
        self.migration_thread = MigrationThread(source_config, target_config, selected_tables)
        self.migration_thread.log.connect(self.log)
        self.migration_thread.progress.connect(self.progress_bar.setValue)
        self.migration_thread.finished.connect(self.migration_finished)
        self.migration_thread.start()

    def migration_finished(self, success, message):
        self.migrate_btn.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            # 计算迁移的表数量
            migrated_tables = [table for table, checkbox in self.tables_var.items() if checkbox.isChecked()]
            table_count = len(migrated_tables)
            
            # 构建成功信息
            detail_msg = (
                f"迁移完成！\n\n"
                f"成功迁移 {table_count} 张表:\n- " + 
                "\n- ".join(migrated_tables)
            )
            
            # 显示成功对话框
            success_box = QMessageBox(QMessageBox.Information, "迁移成功", message)
            success_box.setDetailedText(detail_msg)
            success_box.exec_()
            
            # 刷新报告列表
            self.refresh_report_list()
        else:
            # 从日志中提取错误信息
            log_text = self.log_text.toPlainText()
            error_lines = [line for line in log_text.split('\n') if '失败' in line or '错误' in line]
            
            # 构建错误摘要
            error_summary = "\n".join(error_lines) if error_lines else "无法确定具体错误，请查看完整日志"
            
            # 构建帮助信息
            help_text = (
                "请检查以下可能的问题：\n"
                "1. 确保源数据库和目标数据库都能正常连接\n"
                "2. 检查网络连接是否稳定\n"
                "3. 确认用户是否有足够的权限执行数据迁移\n"
                "4. 确认目标数据库中表的结构与源数据库兼容\n\n"
                "您可以尝试：\n"
                "• 使用较少的表重新执行迁移\n"
                "• 检查日志中的详细错误信息\n"
                "• 手动在目标数据库创建相应表结构"
            )
            
            # 显示错误对话框
            error_box = QMessageBox(QMessageBox.Critical, "迁移失败", message)
            error_box.setDetailedText(f"错误摘要:\n{error_summary}\n\n帮助信息:\n{help_text}")
            error_box.exec_()

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
                target_config = self.get_target_config()
                if self.migrator.restore_database(
                    backup_file,
                    target_config['host'],
                    target_config['user'],
                    target_config['passwd'],
                    target_config['db']
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

    def show_help(self):
        """显示帮助信息"""
        help_text = """
<h3>数据迁移工具使用指南</h3>

<h4>常见问题解决方案：</h4>

<b>1. 本地数据库连接失败 (错误代码10061)</b>
<ul>
<li>原因：本地没有运行MySQL服务器或服务器未在指定端口监听</li>
<li>解决方案：将源数据库也设置为远程数据库，使用相同的主机地址和凭据</li>
</ul>

<b>2. 如何在两个远程数据库之间迁移数据</b>
<ul>
<li>将源数据库和目标数据库都设置为远程服务器地址</li>
<li>在目标数据库部分，使用"新数据库名"创建一个新的数据库</li>
<li>确保勾选"自动创建数据库和表结构"选项</li>
</ul>

<b>3. 权限问题</b>
<ul>
<li>确保使用的用户账户有足够权限创建数据库和表</li>
<li>如果没有创建数据库的权限，请联系数据库管理员先创建数据库</li>
</ul>

<b>4. 最佳实践</b>
<ul>
<li>迁移前先测试源和目标数据库连接</li>
<li>对重要数据进行备份</li>
<li>如果只需要表结构而非数据，可以在迁移后手动清空表</li>
</ul>
"""
        msg_box = QMessageBox(QMessageBox.Information, "数据迁移工具帮助", "数据迁移工具使用指南")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(help_text)
        msg_box.exec_()

def main():
    app = QApplication(sys.argv)
    window = MigrationGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 