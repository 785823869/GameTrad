import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox, filedialog
import os
import threading
import time
from datetime import datetime
import logging
import subprocess

from src.utils.db_backup import DatabaseBackup

class BackupDialog(tk.Toplevel):
    """数据库备份与恢复对话框"""
    
    def __init__(self, parent):
        """初始化备份对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置窗口属性
        self.title("数据库备份与恢复")
        self.geometry("800x600")  # 增加窗口宽度以便显示更多内容
        self.minsize(800, 600)
        self.transient(parent)
        self.grab_set()
        
        # 记录原始主题
        self.parent = parent
        self.original_theme = tb.Style().theme.name
        
        # 为此对话框设置cosmo主题
        tb.Style().theme_use("cosmo")
        
        # 初始化备份工具
        self.backup_tool = DatabaseBackup()
        
        # 初始化操作状态
        self.is_operating = False
        
        # 创建界面元素
        self.create_widgets()
        
        # 加载备份列表
        self.refresh_backup_list()
        
        # 居中窗口
        self.center_window()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """关闭对话框前恢复原主题"""
        # 恢复原主题
        tb.Style().theme_use(self.original_theme)
        # 销毁窗口
        self.destroy()
    
    def create_widgets(self):
        """创建对话框控件"""
        # 创建主容器
        self.main_frame = tb.Frame(self, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题
        tb.Label(
            self.main_frame, 
            text="数据库备份与恢复",
            font=("Microsoft YaHei", 16, "bold"),
            bootstyle="primary",
        ).pack(pady=(0, 20))
        
        # 创建上半部分（备份设置）
        settings_frame = tb.LabelFrame(self.main_frame, text="备份设置", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 备份目录设置
        dir_frame = tb.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=(5, 10))
        
        tb.Label(dir_frame, text="备份目录:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.backup_dir_var = tk.StringVar(value=self.backup_tool.backup_dir)
        dir_entry = tb.Entry(dir_frame, textvariable=self.backup_dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tb.Button(dir_frame, text="浏览", command=self.browse_backup_dir)
        browse_btn.pack(side=tk.RIGHT)
        
        # 添加打开目录按钮
        open_dir_btn = tb.Button(
            dir_frame, 
            text="打开文件夹", 
            bootstyle="info", 
            command=self.open_backup_folder
        )
        open_dir_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建操作按钮区
        btn_frame = tb.Frame(settings_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 创建备份按钮
        self.backup_btn = tb.Button(
            btn_frame,
            text="立即备份",
            bootstyle="primary",
            width=15,
            command=self.perform_backup
        )
        self.backup_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建自动删除旧备份选项
        self.auto_delete_var = tk.BooleanVar(value=True)
        self.auto_delete_cb = tb.Checkbutton(
            btn_frame,
            text="自动删除30天前的备份",
            variable=self.auto_delete_var,
            bootstyle="primary"
        )
        self.auto_delete_cb.pack(side=tk.LEFT, padx=10)
        
        # 创建下半部分（备份列表）
        list_frame = tb.LabelFrame(self.main_frame, text="备份列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 创建表格
        columns = ('文件名', '备份时间', '大小', '路径')
        self.backup_tree = tb.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # 设置列宽和对齐方式
        self.backup_tree.column('文件名', width=150, anchor='w')
        self.backup_tree.column('备份时间', width=150, anchor='center')
        self.backup_tree.column('大小', width=100, anchor='center')
        self.backup_tree.column('路径', width=350, anchor='w')  # 增加路径列宽度
        
        # 设置表头
        for col in columns:
            self.backup_tree.heading(col, text=col)
            
        # 添加滚动条
        scrollbar_y = tb.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar_y.set)
        
        # 添加水平滚动条
        scrollbar_x = tb.Scrollbar(list_frame, orient="horizontal", command=self.backup_tree.xview)
        self.backup_tree.configure(xscrollcommand=scrollbar_x.set)
        
        # 放置表格和滚动条
        self.backup_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 添加表格样式
        self.backup_tree.tag_configure('evenrow', background='#f0f4fa')
        self.backup_tree.tag_configure('oddrow', background='#ffffff')
        
        # 绑定右键菜单
        self.backup_tree.bind("<Button-3>", self.show_context_menu)
        # 绑定双击事件
        self.backup_tree.bind("<Double-1>", lambda e: self.perform_restore())
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.backup_tree, tearoff=0)
        self.context_menu.add_command(label="恢复备份", command=self.perform_restore)
        self.context_menu.add_command(label="删除备份", command=self.delete_backup)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制路径", command=self.copy_path_to_clipboard)
        self.context_menu.add_command(label="打开所在文件夹", command=self.open_containing_folder)
        
        # 创建底部操作按钮
        bottom_btn_frame = tb.Frame(self.main_frame)
        bottom_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 恢复按钮
        self.restore_btn = tb.Button(
            bottom_btn_frame,
            text="恢复选中的备份",
            bootstyle="warning",
            width=18,
            command=self.perform_restore
        )
        self.restore_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮
        self.delete_btn = tb.Button(
            bottom_btn_frame,
            text="删除选中的备份",
            bootstyle="danger",
            width=18,
            command=self.delete_backup
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        self.refresh_btn = tb.Button(
            bottom_btn_frame,
            text="刷新列表",
            bootstyle="info",
            width=15,
            command=self.refresh_backup_list
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        self.close_btn = tb.Button(
            bottom_btn_frame,
            text="关闭",
            bootstyle="secondary",
            width=15,
            command=self.on_close
        )
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        status_frame = tb.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = tb.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
    
    def browse_backup_dir(self):
        """浏览并选择备份目录"""
        current_dir = self.backup_dir_var.get()
        dir_path = filedialog.askdirectory(initialdir=current_dir)
        
        if dir_path:
            self.backup_dir_var.set(dir_path)
            # 更新备份工具的目录设置
            self.backup_tool.backup_dir = dir_path
    
    def open_backup_folder(self):
        """打开备份目录"""
        backup_dir = self.backup_dir_var.get()
        if os.path.exists(backup_dir):
            if os.name == 'nt':  # Windows
                os.startfile(backup_dir)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', backup_dir])
        else:
            messagebox.showinfo("提示", "备份目录不存在")
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击位置
        iid = self.backup_tree.identify_row(event.y)
        if iid:
            # 选择点击的行
            self.backup_tree.selection_set(iid)
            # 显示菜单
            self.context_menu.tk_popup(event.x_root, event.y_root)
    
    def copy_path_to_clipboard(self):
        """复制备份文件路径到剪贴板"""
        selection = self.backup_tree.selection()
        if selection:
            item = self.backup_tree.item(selection[0])
            file_path = item["values"][3]
            self.clipboard_clear()
            self.clipboard_append(file_path)
            self.status_var.set("路径已复制到剪贴板")
    
    def open_containing_folder(self):
        """打开包含所选备份文件的文件夹"""
        selection = self.backup_tree.selection()
        if selection:
            item = self.backup_tree.item(selection[0])
            file_path = item["values"][3]
            
            if os.path.exists(file_path):
                dir_path = os.path.dirname(file_path)
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', file_path])
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.run(['open', '-R', file_path] if os.uname().sysname == 'Darwin' else ['xdg-open', dir_path])
            else:
                messagebox.showinfo("提示", "文件不存在")
    
    def refresh_backup_list(self):
        """刷新备份文件列表"""
        # 清空表格
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # 获取备份文件列表
        backups = self.backup_tool.list_backups()
        
        # 添加到表格
        for i, backup in enumerate(backups):
            values = (
                backup["filename"],
                backup["time"],
                backup["size"],
                backup["path"]
            )
            item_id = self.backup_tree.insert("", "end", values=values)
            
            # 添加间隔色
            if i % 2 == 0:
                self.backup_tree.item(item_id, tags=("evenrow",))
            else:
                self.backup_tree.item(item_id, tags=("oddrow",))
        
        # 更新状态
        self.status_var.set(f"已找到 {len(backups)} 个备份文件")
        
        # 如果没有备份文件，禁用恢复和删除按钮
        if not backups:
            self.restore_btn.config(state="disabled")
            self.delete_btn.config(state="disabled")
        else:
            self.restore_btn.config(state="normal")
            self.delete_btn.config(state="normal")
    
    def perform_backup(self):
        """执行备份操作"""
        if self.is_operating:
            messagebox.showinfo("提示", "正在进行操作，请等待完成")
            return
        
        # 更新状态
        self.status_var.set("正在备份数据库...")
        self.is_operating = True
        self.update_buttons_state("disabled")
        self.update()
        
        # 在后台线程执行备份
        def backup_thread():
            try:
                # 执行备份
                success, message, backup_path = self.backup_tool.backup_database(send_email=True)
                
                # 根据自动删除选项决定是否清理旧备份
                if success and self.auto_delete_var.get():
                    deleted_count, _ = self.backup_tool.auto_delete_old_backups(keep_days=30)
                    if deleted_count > 0:
                        message += f"\n已自动删除 {deleted_count} 个过期备份"
                
                # 更新UI
                self.after(0, lambda: self.backup_completed(success, message))
                
            except Exception as e:
                self.after(0, lambda: self.backup_completed(False, f"备份过程中出错: {str(e)}"))
        
        # 启动备份线程
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def backup_completed(self, success, message):
        """备份完成回调"""
        self.is_operating = False
        self.update_buttons_state("normal")
        
        if success:
            messagebox.showinfo("成功", message)
        else:
            messagebox.showerror("错误", message)
        
        # 刷新备份列表
        self.refresh_backup_list()
        self.status_var.set("就绪")
    
    def perform_restore(self):
        """执行恢复操作"""
        # 获取选中的备份文件
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要恢复的备份文件")
            return
        
        # 获取选中备份的信息
        item = self.backup_tree.item(selection[0])
        values = item["values"]
        backup_file = values[3]  # 获取完整路径
        
        # 确认恢复操作
        if not messagebox.askyesno("确认", f"确定要恢复备份 {values[0]} 吗？\n\n警告：此操作将覆盖当前数据库中的所有数据！"):
            return
        
        if self.is_operating:
            messagebox.showinfo("提示", "正在进行操作，请等待完成")
            return
        
        # 更新状态
        self.status_var.set("正在恢复数据库...")
        self.is_operating = True
        self.update_buttons_state("disabled")
        self.update()
        
        # 在后台线程执行恢复
        def restore_thread():
            try:
                # 执行恢复
                success, message = self.backup_tool.restore_database(backup_file)
                
                # 更新UI
                self.after(0, lambda: self.restore_completed(success, message))
                
            except Exception as e:
                self.after(0, lambda: self.restore_completed(False, f"恢复过程中出错: {str(e)}"))
        
        # 启动恢复线程
        threading.Thread(target=restore_thread, daemon=True).start()
    
    def restore_completed(self, success, message):
        """恢复完成回调"""
        self.is_operating = False
        self.update_buttons_state("normal")
        
        if success:
            messagebox.showinfo("成功", message)
        else:
            messagebox.showerror("错误", message)
        
        self.status_var.set("就绪")
    
    def delete_backup(self):
        """删除选中的备份文件"""
        # 获取选中的备份文件
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的备份文件")
            return
        
        # 获取选中备份的信息
        item = self.backup_tree.item(selection[0])
        values = item["values"]
        backup_file = values[3]  # 获取完整路径
        
        # 确认删除操作
        if not messagebox.askyesno("确认", f"确定要删除备份 {values[0]} 吗？"):
            return
        
        # 执行删除
        success, message = self.backup_tool.delete_backup(backup_file)
        
        if success:
            messagebox.showinfo("成功", message)
            # 刷新备份列表
            self.refresh_backup_list()
        else:
            messagebox.showerror("错误", message)
    
    def update_buttons_state(self, state):
        """更新按钮状态"""
        self.backup_btn.config(state=state)
        self.restore_btn.config(state=state)
        self.delete_btn.config(state=state)
        self.refresh_btn.config(state=state)
    
    def center_window(self):
        """使窗口在屏幕上居中"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y)) 