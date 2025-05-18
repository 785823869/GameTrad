import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import MySQLdb
import logging
import threading
import re
import time
import json
import os
import shutil
import sys
import subprocess
from datetime import datetime

class ServerManagerDialog(tk.Toplevel):
    """游戏服务器管理对话框，集成创建和切换服务器功能"""
    
    # 服务器映射配置文件路径
    SERVER_MAP_FILE = os.path.join("data", "config", "server_map.json")
    
    # 数据库备份路径
    DATABASE_BACKUP_DIR = os.path.join("data", "database_backups")
    
    def __init__(self, parent, db_manager, main_gui=None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            db_manager: 数据库管理器实例
            main_gui: 主界面实例，用于刷新数据
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.main_gui = main_gui
        
        # 获取日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 设置对话框属性
        self.title("游戏服务器管理")
        self.geometry("650x680")
        self.resizable(False, False)
        self.transient(parent)  # 设置为父窗口的临时窗口
        self.grab_set()  # 模态对话框
        
        # 当前数据库配置
        self.current_config = self.db_manager.config.copy()
        
        # 服务器列表
        self.servers = []
        
        # 数据库名称到服务器名称的映射
        self.server_name_map = {}
        
        # 加载服务器名称映射
        self.load_server_map()
        
        # 加载服务器列表
        self.load_servers()
        
        # 创建UI组件
        self.create_widgets()
        
        # 居中显示
        self.center_window()
        
        # 线程
        self.create_thread = None
        self.switch_thread = None
        
        # 显式更新确保所有小部件正确显示
        self.update_idletasks()

    def load_server_map(self):
        """加载服务器名称映射配置"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.SERVER_MAP_FILE), exist_ok=True)
            
            # 如果配置文件存在，加载它
            if os.path.exists(self.SERVER_MAP_FILE):
                with open(self.SERVER_MAP_FILE, 'r', encoding='utf-8') as f:
                    self.server_name_map = json.load(f)
                    self.logger.info(f"已加载服务器映射配置: {len(self.server_name_map)} 个映射")
            else:
                self.server_name_map = {}
                self.logger.info("服务器映射配置文件不存在，使用空映射")
                
            # 确保OcrTrade映射到"诛仙瑶光沁雪"
            if "OcrTrade" not in self.server_name_map:
                self.server_name_map["OcrTrade"] = "诛仙瑶光沁雪"
                self.save_server_map()
                
        except Exception as e:
            self.logger.error(f"加载服务器映射配置失败: {e}", exc_info=True)
            self.server_name_map = {"OcrTrade": "诛仙瑶光沁雪"}
    
    def save_server_map(self):
        """保存服务器名称映射配置"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.SERVER_MAP_FILE), exist_ok=True)
            
            # 保存配置
            with open(self.SERVER_MAP_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.server_name_map, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"已保存服务器映射配置: {len(self.server_name_map)} 个映射")
        except Exception as e:
            self.logger.error(f"保存服务器映射配置失败: {e}", exc_info=True)

    def load_servers(self):
        """加载可用的服务器列表"""
        try:
            # 连接到MySQL服务器（不指定数据库）
            self.logger.info(f"正在连接到MySQL服务器: {self.current_config['host']}:{self.current_config['port']}")
            conn = MySQLdb.connect(
                host=self.current_config['host'],
                port=int(self.current_config['port']),
                user=self.current_config['user'],
                passwd=self.current_config['passwd'],
                charset=self.current_config['charset']
            )
            cursor = conn.cursor()
            
            # 获取所有数据库
            cursor.execute("SHOW DATABASES")
            all_databases = [db[0] for db in cursor.fetchall()]
            
            # 过滤出游戏数据库（假设游戏数据库都包含特定的表）
            self.servers = []
            for db_name in all_databases:
                # 排除系统数据库
                if db_name in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                    continue
                
                try:
                    # 检查是否有游戏系统的特定表（假设有inventory表）
                    cursor.execute(f"SHOW TABLES FROM `{db_name}` LIKE 'inventory'")
                    if cursor.fetchone():
                        self.servers.append(db_name)
                except Exception:
                    # 如果无法访问该数据库，跳过
                    pass
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"找到 {len(self.servers)} 个游戏服务器数据库")
            
            # 确保映射中包含所有服务器
            for db_name in self.servers:
                if db_name not in self.server_name_map:
                    # 如果没有映射，使用数据库名称作为服务器名称
                    self.server_name_map[db_name] = db_name
            
            # 保存更新后的映射
            self.save_server_map()
            
        except Exception as e:
            self.logger.error(f"加载服务器列表失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"加载服务器列表失败: {str(e)}")
            self.servers = []  # 确保服务器列表为空列表而非None
    
    def get_server_display_names(self):
        """获取用于显示的服务器名称列表"""
        return [self.server_name_map.get(db_name, db_name) for db_name in self.servers]
    
    def get_db_name_from_display(self, display_name):
        """从显示名称获取数据库名称"""
        # 如果直接匹配数据库名称，直接返回
        if display_name in self.servers:
            return display_name
            
        # 否则在映射中查找
        for db_name, server_name in self.server_name_map.items():
            if server_name == display_name and db_name in self.servers:
                return db_name
                
        # 如果找不到，返回原始名称
        return display_name

    def create_widgets(self):
        """创建对话框组件"""
        # 创建一个主容器
        self.main_container = tk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 标题
        self.title_frame = tk.Frame(self.main_container)
        self.title_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = tb.Label(
            self.title_frame, 
            text="游戏服务器管理", 
            font=("Microsoft YaHei", 18, "bold"),
            bootstyle="primary"
        )
        self.title_label.pack(anchor="center")
        
        # 当前数据库信息
        self.current_db_frame = tb.LabelFrame(self.main_container, text="当前数据库", padding=10)
        self.current_db_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 显示当前数据库连接信息
        config = self.db_manager.config
        info_text = f"主机: {config['host']}    端口: {config['port']}    数据库: {config['db']}"
        self.db_info_label = tb.Label(self.current_db_frame, text=info_text)
        self.db_info_label.pack(fill=tk.X)

        # 创建标签页控件
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页1：创建服务器
        self.create_tab = tk.Frame(self.notebook)
        self.notebook.add(self.create_tab, text="创建服务器")
        
        # 创建标签页2：切换服务器
        self.switch_tab = tk.Frame(self.notebook)
        self.notebook.add(self.switch_tab, text="切换服务器")
        
        # 创建标签页3：管理服务器
        self.manage_tab = tk.Frame(self.notebook)
        self.notebook.add(self.manage_tab, text="管理服务器")
        
        # 初始化标签页内容
        self.init_create_tab()
        self.init_switch_tab()
        self.init_manage_tab()
        
        # 底部按钮区域
        self.button_frame = tk.Frame(self.main_container)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15)
        
        # 关闭按钮
        self.close_button = tk.Button(
            self.button_frame, 
            text="关闭", 
            command=self.destroy,
            bg="#6c757d",  # 灰色背景
            fg="white",    # 白色文本
            font=("Microsoft YaHei", 10),
            width=10,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.close_button.pack(side=tk.RIGHT, padx=10)

    def init_create_tab(self):
        """初始化创建服务器标签页"""
        # 创建内容框架
        create_frame = tk.Frame(self.create_tab, padx=10, pady=10)
        create_frame.pack(fill=tk.BOTH, expand=True)
        
        # 新服务器信息输入
        self.input_frame = tb.LabelFrame(create_frame, text="新服务器信息", padding=10)
        self.input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 服务器名称输入
        self.server_name_frame = tk.Frame(self.input_frame)
        self.server_name_frame.pack(fill=tk.X, pady=5)
        
        self.server_name_label = tb.Label(self.server_name_frame, text="服务器名称:", width=12, anchor=tk.W)
        self.server_name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.server_name_var = tk.StringVar()
        self.server_name_entry = tb.Entry(self.server_name_frame, textvariable=self.server_name_var, width=30)
        self.server_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 数据库名称输入
        self.db_name_frame = tk.Frame(self.input_frame)
        self.db_name_frame.pack(fill=tk.X, pady=5)
        
        self.db_name_label = tb.Label(self.db_name_frame, text="数据库名称:", width=12, anchor=tk.W)
        self.db_name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.db_name_var = tk.StringVar()
        # 添加验证功能，只允许英文字母、数字和下划线
        validate_cmd = (self.register(self.validate_db_name), '%P')
        self.db_name_entry = tb.Entry(
            self.db_name_frame, 
            textvariable=self.db_name_var, 
            width=30, 
            validate="key", 
            validatecommand=validate_cmd
        )
        self.db_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 说明文本
        self.note_label = tb.Label(
            self.input_frame, 
            text="注意: 将创建与当前数据库结构相同的新数据库，但不包含数据。\n数据库名称只能包含英文字母、数字和下划线。",
            font=("Microsoft YaHei", 9),
            foreground="gray"
        )
        self.note_label.pack(pady=(10, 0))
        
        # 创建按钮
        self.create_button_frame = tk.Frame(create_frame)
        self.create_button_frame.pack(fill=tk.X, pady=10)
        
        self.create_button = tk.Button(
            self.create_button_frame, 
            text="创建服务器", 
            command=self.confirm_create_server,
            bg="#28a745",  # 绿色背景
            fg="white",    # 白色文本
            font=("Microsoft YaHei", 10, "bold"),
            width=12,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.create_button.pack(side=tk.RIGHT, padx=10)
        
        # 进度条
        self.create_progress_frame = tb.LabelFrame(create_frame, text="操作进度", padding=10)
        self.create_progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.create_progress_var = tk.DoubleVar(value=0.0)
        self.create_progress_bar = ttk.Progressbar(
            self.create_progress_frame, 
            orient="horizontal", 
            mode="determinate",
            variable=self.create_progress_var
        )
        self.create_progress_bar.pack(fill=tk.X, pady=10)
        
        # 日志区域
        self.create_log_frame = tb.LabelFrame(create_frame, text="操作日志", padding=10)
        self.create_log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_log_text = tb.Text(self.create_log_frame, height=10, wrap=tk.WORD)
        self.create_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        self.create_log_scrollbar = tb.Scrollbar(self.create_log_frame, command=self.create_log_text.yview)
        self.create_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.create_log_text.config(yscrollcommand=self.create_log_scrollbar.set)
        
        # 初始化日志
        self.append_create_log("请输入新服务器信息")

    def init_switch_tab(self):
        """初始化切换服务器标签页"""
        # 创建内容框架
        switch_frame = tk.Frame(self.switch_tab, padx=10, pady=10)
        switch_frame.pack(fill=tk.BOTH, expand=True)
        
        # 服务器选择框架
        self.select_frame = tb.LabelFrame(switch_frame, text="选择目标服务器", padding=10)
        self.select_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 服务器下拉选择框
        self.server_frame = tk.Frame(self.select_frame)
        self.server_frame.pack(fill=tk.X, pady=5)
        
        self.server_label = tb.Label(self.server_frame, text="服务器数据库:", width=15, anchor=tk.W)
        self.server_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.server_var = tk.StringVar()
        self.server_combobox = ttk.Combobox(self.server_frame, textvariable=self.server_var, width=30, state="readonly")
        self.server_combobox['values'] = self.get_server_display_names()
        
        # 设置当前数据库为默认选中的项
        current_db = self.current_config['db']
        current_display_name = self.server_name_map.get(current_db, current_db)
        
        display_names = self.get_server_display_names()
        if display_names:
            if current_display_name in display_names:
                self.server_combobox.set(current_display_name)
            else:
                self.server_combobox.current(0)
        
        self.server_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 刷新按钮
        self.refresh_button = tk.Button(
            self.server_frame,
            text="刷新列表",
            command=self.refresh_servers,
            bg="#17a2b8",  # 浅蓝色背景
            fg="white",    # 白色文本
            font=("Microsoft YaHei", 9),
            width=10,
            relief=tk.RAISED,
            bd=2
        )
        self.refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # 说明文本
        self.note_label = tb.Label(
            self.select_frame, 
            text="注意: 切换服务器后，当前会话中的所有数据将被新服务器的数据替换。",
            font=("Microsoft YaHei", 9),
            foreground="gray"
        )
        self.note_label.pack(pady=(10, 0))
        
        # 切换按钮
        self.switch_button_frame = tk.Frame(switch_frame)
        self.switch_button_frame.pack(fill=tk.X, pady=10)
        
        self.switch_button = tk.Button(
            self.switch_button_frame, 
            text="切换服务器", 
            command=self.confirm_switch_server,
            bg="#007bff",  # 蓝色背景
            fg="white",    # 白色文本
            font=("Microsoft YaHei", 10, "bold"),
            width=12,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.switch_button.pack(side=tk.RIGHT, padx=10)
        
        # 进度条
        self.switch_progress_frame = tb.LabelFrame(switch_frame, text="操作进度", padding=10)
        self.switch_progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.switch_progress_var = tk.DoubleVar(value=0.0)
        self.switch_progress_bar = ttk.Progressbar(
            self.switch_progress_frame, 
            orient="horizontal", 
            mode="determinate",
            variable=self.switch_progress_var
        )
        self.switch_progress_bar.pack(fill=tk.X, pady=10)
        
        # 日志区域
        self.switch_log_frame = tb.LabelFrame(switch_frame, text="操作日志", padding=10)
        self.switch_log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.switch_log_text = tb.Text(self.switch_log_frame, height=10, wrap=tk.WORD)
        self.switch_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        self.switch_log_scrollbar = tb.Scrollbar(self.switch_log_frame, command=self.switch_log_text.yview)
        self.switch_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.switch_log_text.config(yscrollcommand=self.switch_log_scrollbar.set)
        
        # 初始化日志
        self.append_switch_log("请选择要切换到的服务器数据库")

    def init_manage_tab(self):
        """初始化管理服务器标签页"""
        # 创建内容框架
        manage_frame = tk.Frame(self.manage_tab, padx=10, pady=10)
        manage_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用左右两列布局来优化空间使用
        left_column = tk.Frame(manage_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_column = tk.Frame(manage_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 服务器列表框架 - 放在左列
        self.manage_list_frame = tb.LabelFrame(left_column, text="服务器列表", padding=10)
        self.manage_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建服务器列表（Treeview）
        columns = ("server_name", "db_name")
        self.server_tree = ttk.Treeview(self.manage_list_frame, columns=columns, show="headings", height=8)
        
        # 定义列
        self.server_tree.heading("server_name", text="服务器名称")
        self.server_tree.heading("db_name", text="数据库名称")
        
        # 设置列宽
        self.server_tree.column("server_name", width=140, anchor="center")
        self.server_tree.column("db_name", width=140, anchor="center")
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(self.manage_list_frame, orient="vertical", command=self.server_tree.yview)
        self.server_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局列表和滚动条
        self.server_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.server_tree.bind("<<TreeviewSelect>>", self.on_server_select)
        
        # 按钮区域 - 放在左列
        self.manage_buttons_frame = tk.Frame(left_column)
        self.manage_buttons_frame.pack(fill=tk.X, pady=5)
        
        # 刷新按钮
        self.manage_refresh_button = tk.Button(
            self.manage_buttons_frame,
            text="刷新列表",
            command=self.refresh_server_list,
            bg="#17a2b8",  # 浅蓝色背景
            fg="white",    # 白色文本
            font=("Microsoft YaHei", 9),
            width=10,
            relief=tk.RAISED,
            bd=2
        )
        self.manage_refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮区域 - 使用单独的 Frame 容纳两个删除按钮
        delete_buttons_frame = tk.Frame(self.manage_buttons_frame)
        delete_buttons_frame.pack(side=tk.RIGHT)
        
        # 删除并备份按钮
        self.delete_backup_button = tk.Button(
            delete_buttons_frame,
            text="删除并备份",
            command=self.confirm_delete_server_with_backup,
            bg="#ffc107",  # 黄色背景
            fg="black",    # 黑色文本
            font=("Microsoft YaHei", 9, "bold"),
            width=10,
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED  # 初始状态禁用
        )
        self.delete_backup_button.pack(side=tk.RIGHT, padx=5)
        
        # 仅删除按钮
        self.delete_button = tk.Button(
            delete_buttons_frame,
            text="仅删除",
            command=self.confirm_delete_server,
            bg="#dc3545",  # 红色背景
            fg="white",    # 白色文本
            font=("Microsoft YaHei", 9, "bold"),
            width=8,
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED  # 初始状态禁用
        )
        self.delete_button.pack(side=tk.RIGHT, padx=5)
        
        # 进度条 - 放在左列
        self.manage_progress_frame = tb.LabelFrame(left_column, text="操作进度", padding=10)
        self.manage_progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.manage_progress_var = tk.DoubleVar(value=0.0)
        self.manage_progress_bar = ttk.Progressbar(
            self.manage_progress_frame, 
            orient="horizontal", 
            mode="determinate",
            variable=self.manage_progress_var
        )
        self.manage_progress_bar.pack(fill=tk.X, pady=10)
        
        # 日志区域 - 放在右列，给予更大的空间
        self.manage_log_frame = tb.LabelFrame(right_column, text="操作日志", padding=10)
        self.manage_log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.manage_log_text = tb.Text(self.manage_log_frame, wrap=tk.WORD)
        self.manage_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        self.manage_log_scrollbar = tb.Scrollbar(self.manage_log_frame, command=self.manage_log_text.yview)
        self.manage_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.manage_log_text.config(yscrollcommand=self.manage_log_scrollbar.set)
        
        # 初始化
        self.selected_server = None
        self.append_manage_log("请选择要管理的服务器")
        self.refresh_server_list()
    
    def on_server_select(self, event):
        """服务器列表选择事件处理"""
        selected_items = self.server_tree.selection()
        
        if not selected_items:
            self.selected_server = None
            self.delete_button.config(state=tk.DISABLED)
            self.delete_backup_button.config(state=tk.DISABLED)
            return
            
        # 获取选中的服务器信息
        item = selected_items[0]
        values = self.server_tree.item(item, "values")
        if len(values) >= 2:
            server_name = values[0]
            db_name = values[1]
            
            self.selected_server = {
                "server_name": server_name,
                "db_name": db_name
            }
            
            # 如果是当前数据库，禁用删除按钮
            if db_name == self.current_config['db']:
                self.delete_button.config(state=tk.DISABLED)
                self.delete_backup_button.config(state=tk.DISABLED)
                self.append_manage_log(f"无法删除当前正在使用的服务器: {server_name}")
            else:
                self.delete_button.config(state=tk.NORMAL)
                self.delete_backup_button.config(state=tk.NORMAL)
                self.append_manage_log(f"已选择服务器: {server_name} (数据库: {db_name})")
    
    def refresh_server_list(self):
        """刷新服务器列表"""
        # 清空树形视图
        for item in self.server_tree.get_children():
            self.server_tree.delete(item)
            
        # 添加所有服务器到列表
        for db_name in self.servers:
            server_name = self.server_name_map.get(db_name, db_name)
            self.server_tree.insert("", "end", values=(server_name, db_name))
            
        self.append_manage_log(f"服务器列表已更新，共找到 {len(self.servers)} 个服务器")
        
        # 重置选择状态
        self.selected_server = None
        self.delete_button.config(state=tk.DISABLED)
        self.delete_backup_button.config(state=tk.DISABLED)
    
    def confirm_delete_server_with_backup(self):
        """确认删除服务器并备份"""
        if not self.selected_server:
            messagebox.showerror("错误", "请先选择要删除的服务器")
            return
            
        server_name = self.selected_server["server_name"]
        db_name = self.selected_server["db_name"]
        
        # 如果是当前数据库，禁止删除
        if db_name == self.current_config['db']:
            messagebox.showerror("错误", "无法删除当前正在使用的服务器")
            return
            
        # 确认操作
        confirm = messagebox.askyesno(
            "确认删除并备份", 
            f"确定要删除服务器 {server_name} 并备份吗？\n\n"
            f"数据库: {db_name}\n\n"
            "注意：将在删除前备份数据库到备份目录。",
            icon='warning'
        )
        
        if not confirm:
            return
            
        # 禁用按钮
        self.delete_button.config(state=tk.DISABLED)
        self.delete_backup_button.config(state=tk.DISABLED)
        self.manage_refresh_button.config(state=tk.DISABLED)
        
        # 重置进度条
        self.update_manage_progress(0)
        
        # 开始删除
        self.append_manage_log(f"准备删除并备份服务器: {server_name} (数据库: {db_name})")
        
        # 在新线程中执行删除操作
        self.delete_thread = threading.Thread(
            target=self.delete_server, 
            args=(server_name, db_name, True),  # 传递备份标志
            daemon=True
        )
        self.delete_thread.start()
    
    def confirm_delete_server(self):
        """确认删除服务器（不备份）"""
        if not self.selected_server:
            messagebox.showerror("错误", "请先选择要删除的服务器")
            return
            
        server_name = self.selected_server["server_name"]
        db_name = self.selected_server["db_name"]
        
        # 如果是当前数据库，禁止删除
        if db_name == self.current_config['db']:
            messagebox.showerror("错误", "无法删除当前正在使用的服务器")
            return
            
        # 确认操作
        confirm = messagebox.askyesno(
            "确认删除", 
            f"确定要删除服务器 {server_name} 吗？\n\n"
            f"数据库: {db_name}\n\n"
            "注意：此操作将永久删除该服务器的所有数据，且无法恢复！",
            icon='warning'
        )
        
        if not confirm:
            return
            
        # 二次确认
        confirm2 = messagebox.askyesno(
            "再次确认", 
            f"您真的确定要删除服务器 {server_name} 吗？\n\n"
            "数据一旦删除将无法恢复！",
            icon='warning'
        )
        
        if not confirm2:
            return
            
        # 禁用按钮
        self.delete_button.config(state=tk.DISABLED)
        self.delete_backup_button.config(state=tk.DISABLED)
        self.manage_refresh_button.config(state=tk.DISABLED)
        
        # 重置进度条
        self.update_manage_progress(0)
        
        # 开始删除
        self.append_manage_log(f"准备删除服务器: {server_name} (数据库: {db_name})")
        
        # 在新线程中执行删除操作
        self.delete_thread = threading.Thread(
            target=self.delete_server, 
            args=(server_name, db_name, False),  # 传递备份标志
            daemon=True
        )
        self.delete_thread.start()
    
    def backup_database(self, db_name):
        """备份数据库到备份目录"""
        try:
            # 确保备份目录存在
            os.makedirs(self.DATABASE_BACKUP_DIR, exist_ok=True)
            
            # 生成备份文件名，包含时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.DATABASE_BACKUP_DIR, f"backup_{db_name}_{timestamp}.sql")
            
            self.append_manage_log(f"开始备份数据库 {db_name} 到 {backup_file}")
            
            # 构建 mysqldump 命令
            mysqldump_cmd = (
                f"mysqldump -h {self.current_config['host']} "
                f"-P {self.current_config['port']} "
                f"-u {self.current_config['user']} "
                f"-p{self.current_config['passwd']} "
                f"{db_name} > \"{backup_file}\""
            )
            
            # 执行备份命令
            result = os.system(mysqldump_cmd)
            
            if result == 0:
                self.append_manage_log(f"数据库 {db_name} 备份成功")
                return True, backup_file
            else:
                self.append_manage_log(f"数据库 {db_name} 备份失败，错误代码: {result}")
                return False, None
            
        except Exception as e:
            self.logger.error(f"备份数据库失败: {e}", exc_info=True)
            self.append_manage_log(f"备份数据库失败: {str(e)}")
            return False, None
    
    def delete_server(self, server_name, db_name, with_backup=False):
        """删除服务器数据库，可选备份"""
        try:
            backup_file = None
            
            # 如果需要备份，先执行备份
            if with_backup:
                self.update_manage_progress(10)
                self.append_manage_log("准备备份数据库...")
                success, backup_file = self.backup_database(db_name)
                
                if not success:
                    self.append_manage_log("备份失败，删除操作已取消")
                    self.after(0, lambda: messagebox.showerror("错误", "备份数据库失败，删除操作已取消"))
                    self.after(0, self.reset_manage_ui)
                    return
                
                self.update_manage_progress(30)
                self.append_manage_log(f"备份成功，文件: {os.path.basename(backup_file)}")
            else:
                self.update_manage_progress(10)
            
            # 连接到数据库服务器
            progress_start = 30 if with_backup else 10
            self.update_manage_progress(progress_start)
            self.append_manage_log("连接到数据库服务器...")
            
            conn = MySQLdb.connect(
                host=self.current_config['host'],
                port=int(self.current_config['port']),
                user=self.current_config['user'],
                passwd=self.current_config['passwd'],
                charset=self.current_config['charset']
            )
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            progress_step = 50 if with_backup else 30
            self.update_manage_progress(progress_step)
            self.append_manage_log(f"检查数据库 {db_name} 是否存在")
            
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            if not cursor.fetchone():
                self.logger.warning(f"数据库 {db_name} 不存在")
                cursor.close()
                conn.close()
                self.append_manage_log(f"错误: 数据库 {db_name} 不存在")
                self.after(0, lambda: messagebox.showerror("错误", f"数据库 {db_name} 不存在"))
                self.after(0, self.reset_manage_ui)
                return
            
            # 删除数据库
            progress_step = 70 if with_backup else 50
            self.update_manage_progress(progress_step)
            self.append_manage_log(f"正在删除数据库 {db_name}...")
            
            cursor.execute(f"DROP DATABASE `{db_name}`")
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # 从映射中移除
            progress_step = 85 if with_backup else 70
            self.update_manage_progress(progress_step)
            self.append_manage_log("更新服务器映射...")
            
            if db_name in self.server_name_map:
                del self.server_name_map[db_name]
                self.save_server_map()
            
            # 从服务器列表中移除
            progress_step = 95 if with_backup else 90
            self.update_manage_progress(progress_step)
            self.append_manage_log("更新服务器列表...")
            
            if db_name in self.servers:
                self.servers.remove(db_name)
            
            # 完成
            self.update_manage_progress(100)
            
            # 根据是否备份显示不同的成功消息
            if with_backup:
                success_msg = f"服务器 {server_name} 已成功删除，并已备份至 {os.path.basename(backup_file)}"
                self.append_manage_log(success_msg)
                self.logger.info(f"服务器 {server_name} (数据库: {db_name}) 已删除并备份")
                self.after(0, lambda: messagebox.showinfo("成功", success_msg))
            else:
                success_msg = f"服务器 {server_name} 已成功删除"
                self.append_manage_log(success_msg)
                self.logger.info(f"服务器 {server_name} (数据库: {db_name}) 已删除")
                self.after(0, lambda: messagebox.showinfo("成功", success_msg))
            
            # 刷新服务器列表
            self.after(0, self.refresh_all_servers)
            
            # 重置UI
            self.after(0, self.reset_manage_ui)
            
        except Exception as e:
            self.logger.error(f"删除服务器失败: {e}", exc_info=True)
            self.append_manage_log(f"错误: {str(e)}")
            self.after(0, lambda: messagebox.showerror("错误", f"删除服务器失败: {str(e)}"))
            self.after(0, self.reset_manage_ui)
    
    def reset_manage_ui(self):
        """重置管理服务器UI状态"""
        self.delete_button.config(state=tk.DISABLED)
        self.delete_backup_button.config(state=tk.DISABLED)
        self.manage_refresh_button.config(state=tk.NORMAL)
        self.selected_server = None
        
    def refresh_all_servers(self):
        """刷新所有标签页的服务器列表"""
        self.load_servers()
        self.refresh_server_list()  # 刷新管理标签页
        
        # 刷新切换标签页
        self.server_combobox['values'] = self.get_server_display_names()
        
        # 设置当前数据库为选中项
        current_db = self.current_config['db']
        current_display_name = self.server_name_map.get(current_db, current_db)
        
        display_names = self.get_server_display_names()
        if display_names:
            if current_display_name in display_names:
                self.server_combobox.set(current_display_name)
            else:
                self.server_combobox.current(0)
    
    def append_manage_log(self, message):
        """向管理服务器日志区域添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.manage_log_text.insert(tk.END, f"{timestamp} - {message}\n")
        self.manage_log_text.see(tk.END)  # 自动滚动到最新日志
        self.update_idletasks()  # 强制更新UI
    
    def update_manage_progress(self, value):
        """更新管理服务器进度条值"""
        self.manage_progress_var.set(value)
        self.update_idletasks()

    def validate_db_name(self, value):
        """验证数据库名称，只允许英文字母、数字和下划线"""
        return re.match(r'^[a-zA-Z0-9_]*$', value) is not None

    def center_window(self):
        """将对话框居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.parent.winfo_width() // 2) - (width // 2) + self.parent.winfo_x()
        y = (self.parent.winfo_height() // 2) - (height // 2) + self.parent.winfo_y()
        self.geometry(f"{width}x{height}+{x}+{y}")

    def refresh_servers(self):
        """刷新服务器列表"""
        self.append_switch_log("正在刷新服务器列表...")
        self.load_servers()
        self.server_combobox['values'] = self.get_server_display_names()
        
        # 设置当前数据库为选中项
        current_db = self.current_config['db']
        current_display_name = self.server_name_map.get(current_db, current_db)
        
        display_names = self.get_server_display_names()
        if display_names:
            if current_display_name in display_names:
                self.server_combobox.set(current_display_name)
            else:
                self.server_combobox.current(0)
        
        # 如果管理标签页已初始化，也刷新它的列表
        if hasattr(self, 'server_tree'):
            self.refresh_server_list()
                
        self.append_switch_log(f"服务器列表已更新，共找到 {len(self.servers)} 个服务器")

    def append_create_log(self, message):
        """向创建服务器日志区域添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.create_log_text.insert(tk.END, f"{timestamp} - {message}\n")
        self.create_log_text.see(tk.END)  # 自动滚动到最新日志
        self.update_idletasks()  # 强制更新UI

    def append_switch_log(self, message):
        """向切换服务器日志区域添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.switch_log_text.insert(tk.END, f"{timestamp} - {message}\n")
        self.switch_log_text.see(tk.END)  # 自动滚动到最新日志
        self.update_idletasks()  # 强制更新UI

    def update_create_progress(self, value):
        """更新创建服务器进度条值"""
        self.create_progress_var.set(value)
        self.update_idletasks()

    def update_switch_progress(self, value):
        """更新切换服务器进度条值"""
        self.switch_progress_var.set(value)
        self.update_idletasks()

    def confirm_create_server(self):
        """确认并创建服务器"""
        # 获取输入值
        server_name = self.server_name_var.get().strip()
        db_name = self.db_name_var.get().strip()
        
        # 验证输入
        if not server_name:
            messagebox.showerror("错误", "请输入服务器名称")
            return
            
        if not db_name:
            messagebox.showerror("错误", "请输入数据库名称")
            return
        
        # 验证数据库名格式
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            messagebox.showerror("错误", "数据库名称只能包含英文字母、数字和下划线")
            return
        
        # 确认操作
        confirm = messagebox.askyesno(
            "确认操作", 
            f"确定要创建新的游戏服务器吗？\n\n服务器名称: {server_name}\n数据库名称: {db_name}\n\n注意：这将创建一个新的数据库。"
        )
        
        if not confirm:
            return
        
        # 禁用按钮和输入框
        self.create_button.config(state=tk.DISABLED)
        self.server_name_entry.config(state=tk.DISABLED)
        self.db_name_entry.config(state=tk.DISABLED)
        
        # 重置进度条
        self.update_create_progress(0)
        
        # 清空日志
        self.create_log_text.delete(1.0, tk.END)
        
        # 开始创建
        self.append_create_log(f"开始创建新游戏服务器: {server_name}，数据库: {db_name}")
        
        # 在新线程中执行创建操作
        self.create_thread = threading.Thread(
            target=self.create_server, 
            args=(server_name, db_name),
            daemon=True
        )
        self.create_thread.start()

    def create_server(self, server_name, db_name):
        """创建新服务器数据库"""
        try:
            # 第1步：获取数据库配置
            self.update_create_progress(10)
            self.append_create_log("获取数据库配置...")
            
            config = self.db_manager.config
            
            # 第2步：连接到MySQL服务器（不指定数据库）
            self.update_create_progress(20)
            self.append_create_log(f"正在连接到MySQL服务器: {config['host']}:{config['port']}")
            
            conn = MySQLdb.connect(
                host=config['host'],
                port=int(config['port']),
                user=config['user'],
                passwd=config['passwd'],
                charset=config['charset']
            )
            cursor = conn.cursor()
            
            # 第3步：检查数据库是否已存在
            self.update_create_progress(30)
            self.append_create_log(f"检查数据库 {db_name} 是否已存在")
            
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            if cursor.fetchone():
                self.logger.warning(f"数据库 {db_name} 已存在")
                cursor.close()
                conn.close()
                self.append_create_log(f"错误: 数据库 {db_name} 已存在")
                self.after(0, lambda: messagebox.showerror("错误", f"数据库 {db_name} 已存在"))
                self.after(0, self.reset_create_ui)
                return
            
            # 第4步：创建新数据库
            self.update_create_progress(40)
            self.append_create_log(f"创建新数据库 {db_name}")
            
            cursor.execute(f"CREATE DATABASE `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            
            # 第5步：获取当前数据库的所有表
            self.update_create_progress(50)
            self.append_create_log(f"正在获取当前数据库 {config['db']} 的表结构")
            
            cursor.execute(f"USE `{config['db']}`")
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            # 第6步：切换到新数据库
            self.update_create_progress(60)
            self.append_create_log(f"切换到新数据库 {db_name}")
            
            cursor.execute(f"USE `{db_name}`")
            
            # 第7步：复制表结构
            total_tables = len(tables)
            for i, table in enumerate(tables):
                progress = 60 + (30 * (i + 1) / total_tables)
                self.update_create_progress(progress)
                self.append_create_log(f"创建表 {table}")
                
                cursor.execute(f"SHOW CREATE TABLE `{config['db']}`.`{table}`")
                create_table_sql = cursor.fetchone()[1]
                cursor.execute(create_table_sql)
            
            # 第8步：完成创建
            conn.commit()
            cursor.close()
            conn.close()
            
            self.update_create_progress(100)
            self.append_create_log(f"数据库 {db_name} 创建成功")
            
            # 保存服务器名称映射
            self.server_name_map[db_name] = server_name
            self.save_server_map()
            
            self.logger.info(f"数据库 {db_name} 创建成功，映射到服务器名称 {server_name}")
            self.after(0, lambda: messagebox.showinfo(
                "成功", 
                f"游戏服务器 {server_name} 创建成功！\n\n数据库 {db_name} 已创建，包含所有必要的表结构。"
            ))
            
            # 重新加载服务器列表
            self.after(0, self.refresh_servers)
            
            # 重置UI
            self.after(0, self.reset_create_ui)
            
        except Exception as e:
            self.logger.error(f"创建数据库失败: {e}", exc_info=True)
            self.append_create_log(f"错误: {str(e)}")
            self.after(0, lambda: messagebox.showerror("错误", f"创建数据库失败: {str(e)}"))
            self.after(0, self.reset_create_ui)
    
    def reset_create_ui(self):
        """重置创建服务器UI状态"""
        self.create_button.config(state=tk.NORMAL)
        self.server_name_entry.config(state=tk.NORMAL)
        self.db_name_entry.config(state=tk.NORMAL)

    def confirm_switch_server(self):
        """确认切换服务器"""
        selected_display_name = self.server_var.get()
        
        if not selected_display_name:
            messagebox.showerror("错误", "请选择要切换到的服务器")
            return
        
        # 从显示名称获取真实数据库名称
        selected_db = self.get_db_name_from_display(selected_display_name)
        
        # 服务器名称用于显示
        server_name = self.server_name_map.get(selected_db, selected_db)
            
        if selected_db == self.current_config['db']:
            messagebox.showinfo("提示", "您选择的服务器与当前连接的服务器相同")
            return
            
        # 确认操作
        confirm = messagebox.askyesno(
            "确认操作", 
            f"确定要切换到服务器 {server_name} 吗？\n\n注意：当前会话中的所有数据将被替换。"
        )
        
        if not confirm:
            return
            
        # 禁用按钮
        self.switch_button.config(state=tk.DISABLED)
        self.server_combobox.config(state=tk.DISABLED)
        self.refresh_button.config(state=tk.DISABLED)
        
        # 重置进度条
        self.update_switch_progress(0)
        
        # 清空日志
        self.switch_log_text.delete(1.0, tk.END)
        
        # 开始切换
        self.append_switch_log(f"开始切换到服务器: {server_name} (数据库: {selected_db})")
        
        # 在新线程中执行切换操作
        self.switch_thread = threading.Thread(target=self.switch_server, args=(selected_db,), daemon=True)
        self.switch_thread.start()

    def switch_server(self, target_db):
        """切换到目标服务器数据库"""
        # 获取服务器名称用于显示
        server_name = self.server_name_map.get(target_db, target_db)
        
        try:
            # 第1步：测试连接
            self.update_switch_progress(10)
            self.append_switch_log("测试目标数据库连接...")
            
            # 复制当前配置并修改数据库名
            new_config = self.current_config.copy()
            new_config['db'] = target_db
            
            # 测试连接
            success, message = self.db_manager.test_connection(new_config)
            if not success:
                self.append_switch_log(f"连接失败: {message}")
                self.after(0, lambda: messagebox.showerror("连接错误", f"无法连接到目标服务器: {message}"))
                self.after(0, self.reset_switch_ui)
                return
                
            self.update_switch_progress(30)
            self.append_switch_log("连接测试成功")
                
            # 第2步：验证表结构
            self.update_switch_progress(40)
            self.append_switch_log("验证数据库表结构...")
            
            # 检查必要的表是否存在
            required_tables = [
                'inventory', 'stock_in', 'stock_out', 'trade_monitor', 'operation_logs'
            ]
            
            conn = MySQLdb.connect(
                host=new_config['host'],
                port=int(new_config['port']),
                user=new_config['user'],
                passwd=new_config['passwd'],
                db=new_config['db'],
                charset=new_config['charset']
            )
            cursor = conn.cursor()
            
            missing_tables = []
            for table in required_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    missing_tables.append(table)
            
            cursor.close()
            conn.close()
            
            if missing_tables:
                self.append_switch_log(f"目标数据库缺少必要的表: {', '.join(missing_tables)}")
                self.after(0, lambda: messagebox.showerror("表结构错误", f"目标服务器缺少必要的表: {', '.join(missing_tables)}"))
                self.after(0, self.reset_switch_ui)
                return
                
            self.update_switch_progress(60)
            self.append_switch_log("表结构验证成功")
            
            # 第3步：保存新配置
            self.update_switch_progress(70)
            self.append_switch_log("保存新的数据库配置...")
            
            if not self.db_manager.save_db_config(new_config):
                self.append_switch_log("保存配置失败")
                self.after(0, lambda: messagebox.showerror("错误", "保存数据库配置失败"))
                self.after(0, self.reset_switch_ui)
                return
                
            self.update_switch_progress(80)
            self.append_switch_log("配置已保存")
                
            # 第4步：准备重启
            self.update_switch_progress(90)
            self.append_switch_log("准备重启应用程序...")
            
            # 记录操作日志
            if self.main_gui:
                self.main_gui.log_operation(
                    '切换数据库',
                    '系统',
                    {'db': target_db}
                )
            
            # 显示成功消息和重启提示
            self.update_switch_progress(100)
            self.append_switch_log("配置已更新，程序将重启!")
            
            # 弹出消息框告知用户
            self.after(0, lambda: self.confirm_restart(server_name))
            
        except Exception as e:
            self.logger.error(f"切换服务器失败: {e}", exc_info=True)
            self.append_switch_log(f"错误: {str(e)}")
            self.after(0, lambda: messagebox.showerror("错误", f"切换服务器失败: {str(e)}"))
            self.after(0, self.reset_switch_ui)
    
    def confirm_restart(self, server_name):
        """确认重启应用程序"""
        result = messagebox.showinfo(
            "切换成功", 
            f"已成功切换到服务器: {server_name}\n\n程序将自动重启以加载新数据库。"
        )
        
        # 无论用户点击什么，都执行重启
        self.restart_application()
    
    def restart_application(self):
        """重启应用程序"""
        try:
            self.logger.info("正在重启应用程序...")
            
            # 获取当前执行文件路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                application_path = sys.executable
                self.logger.info(f"使用打包的可执行文件路径重启: {application_path}")
                
                # 关闭当前窗口
                self.destroy()
                if self.main_gui:
                    self.main_gui.root.destroy()
                
                # 启动新进程
                subprocess.Popen([application_path])
                
                # 退出当前进程
                os._exit(0)
            else:
                # 如果是Python脚本
                application_path = sys.argv[0]
                self.logger.info(f"使用Python脚本路径重启: {application_path}")
                
                # 关闭当前窗口
                self.destroy()
                if self.main_gui:
                    self.main_gui.root.destroy()
                
                # 启动新进程
                python_executable = sys.executable
                subprocess.Popen([python_executable, application_path])
                
                # 退出当前进程
                os._exit(0)
                
        except Exception as e:
            self.logger.error(f"重启应用程序失败: {e}", exc_info=True)
            messagebox.showerror("重启失败", 
                f"无法自动重启应用程序: {str(e)}\n\n请手动关闭程序并重新启动。")
            
            # 恢复UI状态
            self.reset_switch_ui()

    def reset_switch_ui(self):
        """重置切换服务器UI状态"""
        self.switch_button.config(state=tk.NORMAL)
        self.server_combobox.config(state="readonly")
        self.refresh_button.config(state=tk.NORMAL) 