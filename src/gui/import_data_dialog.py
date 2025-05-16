import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import os
import sys
import threading
import pandas as pd
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.db_manager import DatabaseManager
from src.scripts.import_data_overwrite import read_csv_auto_encoding, backup_database, clear_stock_data, import_stock_in, import_stock_out
from src.utils.ui_manager import ModernDialog

class ImportDataDialog(ModernDialog):
    def __init__(self, parent):
        super().__init__(parent, "数据导入", 650, 600)
        
        # 创建变量
        self.stock_in_path = tk.StringVar()
        self.stock_out_path = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_text = tk.StringVar(value="准备导入数据...")
        
        # 创建界面组件
        self.create_dialog_content()
        
        # 添加底部按钮
        self.add_buttons([
            {'text': '开始导入', 'command': self.start_import, 'style': 'success'},
            {'text': '取消', 'command': self.dialog.destroy, 'style': 'secondary'}
        ])
        
        # 设置关闭窗口的处理
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
        
    def create_dialog_content(self):
        """创建对话框内容"""
        # 添加标题
        self.add_title("数据导入工具")
        
        # 说明文本
        desc_frame = tb.LabelFrame(self.content_frame, text="说明", padding=10, bootstyle="info")
        desc_frame.pack(fill='x', pady=(0, 15))
        
        tb.Label(desc_frame, text="此工具将清空当前所有库存数据，并从CSV文件导入新数据。\n"
                 "操作前会自动备份数据库，以便在需要时恢复。", 
                 wraplength=550, justify='left').pack()
        
        # 文件选择区域
        file_frame = tb.LabelFrame(self.content_frame, text="文件选择", padding=10, bootstyle="primary")
        file_frame.pack(fill='x', pady=(0, 15))
        
        # 入库文件
        in_frame = tb.Frame(file_frame)
        in_frame.pack(fill='x', pady=5)
        
        tb.Label(in_frame, text="入库文件:", width=10).pack(side='left')
        tb.Entry(in_frame, textvariable=self.stock_in_path, width=50, bootstyle="primary").pack(side='left', padx=5, fill='x', expand=True)
        tb.Button(in_frame, text="浏览...", command=self.browse_stock_in, bootstyle="outline").pack(side='left')
        
        # 出库文件
        out_frame = tb.Frame(file_frame)
        out_frame.pack(fill='x', pady=5)
        
        tb.Label(out_frame, text="出库文件:", width=10).pack(side='left')
        tb.Entry(out_frame, textvariable=self.stock_out_path, width=50, bootstyle="primary").pack(side='left', padx=5, fill='x', expand=True)
        tb.Button(out_frame, text="浏览...", command=self.browse_stock_out, bootstyle="outline").pack(side='left')
        
        # 日志区域
        log_frame = tb.LabelFrame(self.content_frame, text="导入日志", padding=10, bootstyle="secondary")
        log_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.log_area = tk.Text(log_frame, height=10, wrap='word')
        self.log_area.pack(side='left', fill='both', expand=True)
        
        scrollbar = tb.Scrollbar(log_frame, command=self.log_area.yview, bootstyle="primary-round")
        scrollbar.pack(side='right', fill='y')
        self.log_area.config(yscrollcommand=scrollbar.set)
        
        # 进度条
        progress_frame = tb.Frame(self.content_frame)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_bar = tb.Progressbar(progress_frame, variable=self.progress_var, length=100, mode='determinate', bootstyle="success-striped")
        self.progress_bar.pack(fill='x', side='top', pady=(0, 5))
        
        tb.Label(progress_frame, textvariable=self.status_text).pack(side='left')
        
    def browse_stock_in(self):
        """浏览选择入库文件"""
        file_path = filedialog.askopenfilename(
            title="选择入库数据CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.stock_in_path.set(file_path)
            
    def browse_stock_out(self):
        """浏览选择出库文件"""
        file_path = filedialog.askopenfilename(
            title="选择出库数据CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.stock_out_path.set(file_path)
            
    def log(self, message):
        """添加日志消息"""
        self.log_area.insert('end', f"{message}\n")
        self.log_area.see('end')  # 滚动到底部
        self.dialog.update()
            
    def start_import(self):
        """开始导入数据"""
        # 检查文件是否存在
        stock_in_path = self.stock_in_path.get().strip()
        stock_out_path = self.stock_out_path.get().strip()
        
        if not stock_in_path and not stock_out_path:
            messagebox.showerror("错误", "请至少选择一个文件进行导入！")
            return
        
        if stock_in_path and not os.path.exists(stock_in_path):
            messagebox.showerror("错误", f"入库文件不存在: {stock_in_path}")
            return
            
        if stock_out_path and not os.path.exists(stock_out_path):
            messagebox.showerror("错误", f"出库文件不存在: {stock_out_path}")
            return
            
        # 确认操作
        if not messagebox.askyesno("确认操作", "此操作将清空当前所有库存数据，并导入新数据。是否继续？"):
            return
            
        # 禁用按钮，防止重复操作
        for button in self.button_frame.winfo_children():
            if '开始导入' in button['text']:
                button.config(state='disabled')
                break
        
        # 在后台线程中执行导入操作
        threading.Thread(target=self.import_data_thread, daemon=True).start()
        
    def import_data_thread(self):
        """在后台线程中执行导入操作"""
        try:
            stock_in_path = self.stock_in_path.get().strip()
            stock_out_path = self.stock_out_path.get().strip()
            
            # 备份数据库
            self.progress_var.set(10)
            self.status_text.set("正在备份数据库...")
            self.log("正在备份数据库...")
            
            if not backup_database():
                self.log("数据库备份失败，操作已取消")
                self.status_text.set("操作已取消")
                # 恢复按钮状态
                for button in self.button_frame.winfo_children():
                    if '开始导入' in button['text']:
                        button.config(state='normal')
                        break
                return
                
            # 清空数据库
            self.progress_var.set(20)
            self.status_text.set("正在清空库存数据...")
            self.log("正在清空库存数据...")
            clear_stock_data()
            
            total_steps = 30  # 已完成20%，剩余80%分配给导入操作
            current_step = 20
            progress_increment = 80 / (2 if stock_in_path and stock_out_path else 1)
            
            # 导入入库数据
            if stock_in_path:
                self.status_text.set(f"正在导入入库数据: {os.path.basename(stock_in_path)}...")
                self.log(f"正在导入入库数据: {os.path.basename(stock_in_path)}...")
                
                # 读取CSV
                stock_in_df = read_csv_auto_encoding(stock_in_path)
                if stock_in_df is None or stock_in_df.empty:
                    self.log(f"无法读取入库文件或文件为空: {stock_in_path}")
                else:
                    # 处理每行，更新进度
                    total_rows = len(stock_in_df)
                    step_increment = progress_increment / total_rows
                    
                    self.log(f"共 {total_rows} 条入库记录")
                    
                    # 导入入库数据
                    import_stock_in(stock_in_df, 
                               progress_callback=lambda i: self.update_progress(
                                   current_step + step_increment * i,
                                   f"正在导入入库数据... ({i}/{total_rows})"
                               ))
                    
                    current_step += progress_increment
                    self.log("入库数据导入完成")
            
            # 导入出库数据
            if stock_out_path:
                self.status_text.set(f"正在导入出库数据: {os.path.basename(stock_out_path)}...")
                self.log(f"正在导入出库数据: {os.path.basename(stock_out_path)}...")
                
                # 读取CSV
                stock_out_df = read_csv_auto_encoding(stock_out_path)
                if stock_out_df is None or stock_out_df.empty:
                    self.log(f"无法读取出库文件或文件为空: {stock_out_path}")
                else:
                    # 处理每行，更新进度
                    total_rows = len(stock_out_df)
                    step_increment = progress_increment / total_rows
                    
                    self.log(f"共 {total_rows} 条出库记录")
                    
                    # 导入出库数据
                    import_stock_out(stock_out_df, 
                                progress_callback=lambda i: self.update_progress(
                                    current_step + step_increment * i,
                                    f"正在导入出库数据... ({i}/{total_rows})"
                                ))
                    
                    current_step += progress_increment
                    self.log("出库数据导入完成")
            
            # 完成导入
            self.progress_var.set(100)
            self.status_text.set("导入完成")
            self.log("数据导入完成！")
            messagebox.showinfo("成功", "数据导入成功！")
            
            # 自动刷新主界面数据
            self.parent.refresh_after_import()
            
            # 延迟关闭窗口
            self.dialog.after(2000, self.dialog.destroy)
            
        except Exception as e:
            self.log(f"导入过程中发生错误: {str(e)}")
            self.status_text.set("导入失败")
            messagebox.showerror("错误", f"导入失败: {str(e)}")
            
            # 恢复按钮状态
            for button in self.button_frame.winfo_children():
                if '开始导入' in button['text']:
                    button.config(state='normal')
                    break
    
    def update_progress(self, value, status=None):
        """更新进度条和状态文本"""
        self.progress_var.set(value)
        if status:
            self.status_text.set(status)
        self.dialog.update()

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")
    root.title("测试")
    root.geometry("300x200")
    
    def open_dialog():
        ImportDataDialog(root)
    
    tb.Button(root, text="打开导入对话框", command=open_dialog).pack(pady=20)
    
    root.mainloop() 