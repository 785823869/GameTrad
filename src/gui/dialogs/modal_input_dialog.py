import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox

class ModalInputDialog:
    """
    通用的模态输入对话框，用于统一风格的数据输入界面
    """
    def __init__(self, parent, title, fields, callback, initial_values=None, validators=None):
        """
        初始化模态输入对话框
        
        参数:
        - parent: 父窗口
        - title: 对话框标题
        - fields: 字段列表，格式为 [(label, field_name, field_type), ...]
                 field_type 可以是 'str', 'int', 'float' 或自定义验证函数
        - callback: 回调函数，接收字段值的字典作为参数
        - initial_values: 初始值字典，可选
        - validators: 额外的验证器字典，格式为 {field_name: validator_func, ...}
        """
        self.parent = parent
        self.title = title
        self.fields = fields
        self.callback = callback
        self.initial_values = initial_values or {}
        self.validators = validators or {}
        
        self.entries = {}
        self.error_labels = {}
        
        self.create_dialog()
        
    def create_dialog(self):
        """创建对话框界面"""
        # 创建模态窗口
        self.dialog = tb.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.minsize(420, 300)
        self.dialog.configure(bg='#f4f8fb')
        self.dialog.transient(self.parent)  # 设置为父窗口的临时窗口
        self.dialog.grab_set()  # 模态
        
        # 窗口居中
        w = 420
        h = max(300, 80 + len(self.fields) * 60)
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # 设置样式
        style = ttk.Style()
        style.configure('Dialog.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Dialog.TEntry', font=('微软雅黑', 11))
        style.configure('Dialog.TButton', font=('微软雅黑', 12, 'bold'), background='#3a4d54', foreground='#fff', padding=10)
        style.map('Dialog.TButton', background=[('active', '#4f686e')], foreground=[('active', '#ffffff')])
        
        # 主内容框架
        content_frame = ttk.Frame(self.dialog, style='Dialog.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=20, pady=20)
        
        # 添加字段
        for i, (label, field_name, field_type) in enumerate(self.fields):
            ttk.Label(content_frame, text=f"{label}:", style='Dialog.TLabel').grid(
                row=i*2, column=0, padx=12, pady=4, sticky='e'
            )
            
            # 设置输入验证
            vcmd = None
            if field_type == 'int':
                vcmd = (self.dialog.register(lambda s: s.isdigit() or s==''), '%P')
            elif field_type == 'float':
                vcmd = (self.dialog.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            
            # 创建输入框
            entry = ttk.Entry(
                content_frame, 
                validate='key', 
                validatecommand=vcmd, 
                style='Dialog.TEntry'
            ) if vcmd else ttk.Entry(content_frame, style='Dialog.TEntry')
            
            # 设置初始值
            if field_name in self.initial_values:
                entry.insert(0, str(self.initial_values[field_name]))
                
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='ew')
            self.entries[field_name] = entry
            
            # 错误提示标签
            err_label = ttk.Label(
                content_frame, 
                text="", 
                foreground="red", 
                background='#f4f8fb', 
                font=('微软雅黑', 10)
            )
            err_label.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            self.error_labels[field_name] = err_label
        
        # 设置列宽
        content_frame.columnconfigure(1, weight=1)
        
        # 按钮框架
        button_frame = ttk.Frame(self.dialog, style='Dialog.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        
        # 提交按钮
        ttk.Button(
            button_frame, 
            text="提交", 
            command=self.validate_and_submit, 
            style='Dialog.TButton'
        ).pack(side='right', padx=20, ipadx=20)
        
        # 取消按钮
        ttk.Button(
            button_frame, 
            text="取消", 
            command=self.dialog.destroy, 
            style='Dialog.TButton'
        ).pack(side='right', padx=5, ipadx=20)
    
    def validate_and_submit(self):
        """验证输入并提交数据"""
        # 清除所有错误信息
        for err_label in self.error_labels.values():
            err_label.config(text="")
        
        values = {}
        valid = True
        
        # 验证每个字段
        for label, field_name, field_type in self.fields:
            value = self.entries[field_name].get().strip()
            
            # 检查必填项
            if not value:
                self.error_labels[field_name].config(text=f"{label}不能为空")
                self.entries[field_name].focus_set()
                valid = False
                break
            
            # 根据类型验证并转换
            try:
                if field_type == 'int':
                    values[field_name] = int(value)
                elif field_type == 'float':
                    values[field_name] = float(value)
                elif callable(field_type):
                    # 使用自定义验证函数
                    result = field_type(value)
                    if result is not True:
                        self.error_labels[field_name].config(text=str(result))
                        self.entries[field_name].focus_set()
                        valid = False
                        break
                    values[field_name] = value
                else:
                    values[field_name] = value
            except ValueError:
                self.error_labels[field_name].config(text=f"{label}格式不正确")
                self.entries[field_name].focus_set()
                valid = False
                break
            
            # 应用额外的验证器
            if field_name in self.validators:
                result = self.validators[field_name](value)
                if result is not True:
                    self.error_labels[field_name].config(text=str(result))
                    self.entries[field_name].focus_set()
                    valid = False
                    break
        
        # 如果验证通过，调用回调函数并关闭对话框
        if valid:
            try:
                self.callback(values)
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", str(e)) 