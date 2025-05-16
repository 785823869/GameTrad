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

class ImportDataDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tb.Toplevel(parent)
        self.dialog.title("导入数据")
        self.dialog.geometry("600x550")  # 进一步增加窗口高度
        self.dialog.minsize(600, 550)    # 设置最小大小
        self.dialog.resizable(True, True) # 允许调整大小
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 设置窗口图标和居中
        self.dialog.iconbitmap(default='')  # 可以设置图标
        self.center_window()
        
        # 创建变量
        self.stock_in_path = tk.StringVar()
        self.stock_out_path = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_text = tk.StringVar(value="准备导入数据...")
        self.log_text = tk.StringVar()
        
        # 创建界面
        self.create_widgets()
        
        # 设置关闭窗口的处理
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架，使用pack而不是grid，确保自动调整大小
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="数据导入工具", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 说明文本
        desc_frame = ttk.LabelFrame(main_frame, text="说明", padding=10)
        desc_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(desc_frame, text="此工具将清空当前所有库存数据，并从CSV文件导入新数据。\n"
                 "操作前会自动备份数据库，以便在需要时恢复。", 
                 wraplength=550, justify='left').pack()
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding=10)
        file_frame.pack(fill='x', pady=(0, 15))
        
        # 入库文件
        in_frame = ttk.Frame(file_frame)
        in_frame.pack(fill='x', pady=5)
        
        ttk.Label(in_frame, text="入库文件:", width=10).pack(side='left')
        ttk.Entry(in_frame, textvariable=self.stock_in_path, width=50).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(in_frame, text="浏览...", command=self.browse_stock_in).pack(side='left')
        
        # 出库文件
        out_frame = ttk.Frame(file_frame)
        out_frame.pack(fill='x', pady=5)
        
        ttk.Label(out_frame, text="出库文件:", width=10).pack(side='left')
        ttk.Entry(out_frame, textvariable=self.stock_out_path, width=50).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(out_frame, text="浏览...", command=self.browse_stock_out).pack(side='left')
        
        # 日志区域 - 减小高度以确保底部按钮可见
        log_frame = ttk.LabelFrame(main_frame, text="导入日志", padding=10)
        log_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.log_area = tk.Text(log_frame, height=5, wrap='word')
        self.log_area.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_area.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_area.config(yscrollcommand=scrollbar.set)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=(0, 15))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=100, mode='determinate')
        self.progress_bar.pack(fill='x', side='top', pady=(0, 5))
        
        ttk.Label(progress_frame, textvariable=self.status_text).pack(side='left')
        
        # 按钮区域 - 确保按钮可见，专门使用固定高度的Frame
        button_frame = ttk.Frame(main_frame, height=50)
        button_frame.pack(fill='x', pady=(10, 0))
        button_frame.pack_propagate(False)  # 防止子组件影响框架大小
        
        # 按钮放在底部，使用大按钮和明显的样式
        self.import_button = ttk.Button(
            button_frame, 
            text="开始导入", 
            command=self.start_import, 
            style='primary.TButton', 
            width=20
        )
        self.import_button.pack(side='right', padx=5, pady=10)
        
        ttk.Button(
            button_frame, 
            text="取消", 
            command=self.on_close, 
            width=15
        ).pack(side='right', padx=5, pady=10)
        
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
        self.import_button.config(state='disabled')
        
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
                self.import_button.config(state='normal')
                return
                
            self.log("数据库备份成功")
            
            # 清空库存数据
            self.progress_var.set(30)
            self.status_text.set("正在清空原有库存数据...")
            self.log("正在清空原有库存数据...")
            
            if not clear_stock_data():
                self.log("清空数据失败，操作已取消")
                self.status_text.set("操作已取消")
                self.import_button.config(state='normal')
                return
                
            self.log("原有库存数据已清空")
            
            # 导入入库数据
            success = True
            if stock_in_path:
                self.progress_var.set(50)
                self.status_text.set("正在导入入库数据...")
                self.log(f"正在导入入库数据: {stock_in_path}")
                
                if not import_stock_in(stock_in_path):
                    self.log("入库数据导入失败")
                    success = False
                else:
                    self.log("入库数据导入成功")
            
            # 导入出库数据
            if stock_out_path:
                self.progress_var.set(70)
                self.status_text.set("正在导入出库数据...")
                self.log(f"正在导入出库数据: {stock_out_path}")
                
                if not import_stock_out(stock_out_path):
                    self.log("出库数据导入失败")
                    success = False
                else:
                    self.log("出库数据导入成功")
            
            # 完成
            self.progress_var.set(100)
            
            if success:
                self.status_text.set("导入完成")
                self.log("数据导入完成！")
                messagebox.showinfo("成功", "数据导入完成！")
                
                # 刷新主窗口数据
                if hasattr(self.parent, 'refresh_after_import'):
                    self.parent.refresh_after_import()
            else:
                self.status_text.set("导入过程中出现错误")
                self.log("导入过程中出现错误，请检查日志。")
                messagebox.showwarning("警告", "导入过程中出现错误，请检查日志。")
            
        except Exception as e:
            self.log(f"导入过程中出现异常: {e}")
            self.status_text.set("导入失败")
            messagebox.showerror("错误", f"导入过程中出现异常: {e}")
        finally:
            # 恢复按钮状态
            self.import_button.config(state='normal')
            
    def on_close(self):
        """关闭窗口"""
        self.dialog.destroy()

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")
    root.title("测试")
    root.geometry("300x200")
    
    def open_dialog():
        ImportDataDialog(root)
    
    ttk.Button(root, text="打开导入对话框", command=open_dialog).pack(pady=20)
    
    root.mainloop() 