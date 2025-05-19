import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox
import os

class ModalInputDialog:
    """
    通用的模态输入对话框，用于统一风格的数据输入界面
    """
    def __init__(self, parent, title, fields, callback, initial_values=None, validators=None, explanation=None):
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
        - explanation: 说明文本，显示在字段上方，可选
        """
        self.parent = parent
        self.title = title
        self.fields = fields
        self.callback = callback
        self.initial_values = initial_values or {}
        self.validators = validators or {}
        self.explanation = explanation
        
        self.entries = {}
        self.error_labels = {}
        self.field_labels = {}  # 保存字段标签的引用
        
        self.create_dialog()
        
    def create_dialog(self):
        """创建对话框界面"""
        # 创建模态窗口
        self.dialog = tb.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.minsize(450, 350)  # 增加最小高度确保按钮可见
        self.dialog.configure(bg='#f4f8fb')
        self.dialog.transient(self.parent)  # 设置为父窗口的临时窗口
        self.dialog.grab_set()  # 模态
        
        # 设置对话框图标
        icon_path = os.path.join("data", "icon.ico")
        if os.path.exists(icon_path):
            self.dialog.iconbitmap(icon_path)
        elif hasattr(self.parent, 'iconbitmap') and callable(getattr(self.parent, 'iconbitmap', None)):
            try:
                self.dialog.iconbitmap(self.parent.iconbitmap())
            except:
                pass  # 如果继承失败，忽略错误
        
        # 窗口居中
        w = 480  # 增大默认宽度
        h = max(320, 100 + len(self.fields) * 60)
        
        # 如果有说明文本，增加窗口高度
        if self.explanation:
            lines = self.explanation.count('\n') + 1
            explanation_height = max(60, lines * 20 + 10)
            h += explanation_height + 20  # 动态调整窗口高度
            
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # 设置样式
        style = tb.Style()
        style.configure('Dialog.TFrame', background='#f4f8fb')
        style.configure('Dialog.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Dialog.TEntry', font=('微软雅黑', 11))
        style.configure('Dialog.TButton', font=('微软雅黑', 11), padding=(8, 6))
        style.map('Dialog.TButton', background=[('active', '#4f686e')], foreground=[('active', '#ffffff')])
        
        # 创建主容器框架，使用place布局
        main_container = tb.Frame(self.dialog, style='Dialog.TFrame')
        main_container.place(x=0, y=0, relwidth=1, relheight=1)
        
        # 添加说明文本（如果有）
        y_offset = 20
        if self.explanation:
            # 计算文本大约需要的高度：每行约20像素，加上一些额外空间
            lines = self.explanation.count('\n') + 1
            explanation_height = max(60, lines * 20 + 10)  # 最小高度60，根据行数动态调整
            
            explanation_label = tb.Label(
                main_container,
                text=self.explanation,
                justify="left",
                style='Dialog.TLabel',
                bootstyle="primary",
                wraplength=w-60  # 设置文本自动换行宽度
            )
            explanation_label.place(x=20, y=y_offset, width=w-40, height=explanation_height)
            y_offset += explanation_height + 20  # 增加额外间距
        
        # 主内容框架
        content_frame = tb.Frame(main_container, style='Dialog.TFrame')
        content_frame.place(x=20, y=y_offset, relwidth=0.95, height=h-y_offset-80)
        
        # 添加字段
        for i, (label, field_name, field_type) in enumerate(self.fields):
            # 使用place布局来精确定位每个元素
            label_y = i * 60 + 10
            
            # 标签 - 使用ttkbootstrap标签
            label_widget = tb.Label(
                content_frame, 
                text=f"{label}:", 
                style='Dialog.TLabel',
                anchor='e'  # 右对齐文本
            )
            label_widget.place(x=10, y=label_y, width=80, height=30)
            self.field_labels[field_name] = label_widget  # 保存标签引用
            
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
                
            # 放置输入框，确保宽度足够
            entry.place(x=100, y=label_y, relwidth=0.7, height=30)
            self.entries[field_name] = entry
            
            # 错误提示标签
            err_label = tb.Label(
                content_frame, 
                text="", 
                foreground="red", 
                style='Dialog.TLabel',
                font=('微软雅黑', 10)
            )
            err_label.place(x=100, y=label_y+32, relwidth=0.7, height=20)
            self.error_labels[field_name] = err_label
        
        # 按钮区域
        button_container = tb.Frame(main_container, style='Dialog.TFrame')
        button_container.place(x=0, rely=1.0, relwidth=1, height=80, anchor='sw')
        
        # 使用place布局来精确放置按钮
        # 取消按钮 - 增加宽度从100到120
        cancel_button = tb.Button(
            button_container, 
            text="取消", 
            command=self.dialog.destroy, 
            style='Dialog.TButton'
        )
        cancel_button.place(relx=0.35, rely=0.5, width=120, height=36, anchor='center')
        
        # 提交按钮 - 改文字为"确定"，增加宽度从100到120
        submit_button = tb.Button(
            button_container, 
            text="确定", 
            command=self.validate_and_submit, 
            style='Dialog.TButton'
        )
        submit_button.place(relx=0.65, rely=0.5, width=120, height=36, anchor='center')
        
        # 确保窗口大小变化时按钮位置也相应调整
        def on_resize(event):
            # 窗口大小变化时重新计算按钮位置
            button_container.place_configure(height=80)
            cancel_button.place_configure(relx=0.35, rely=0.5, anchor='center')
            submit_button.place_configure(relx=0.65, rely=0.5, anchor='center')
            
        self.dialog.bind("<Configure>", on_resize)
    
    def set_field_style(self, field_name, style_name, bootstyle=None):
        """
        设置特定字段标签的样式
        
        参数:
        - field_name: 字段名称
        - style_name: 样式名称
        - bootstyle: 引导样式名称（可选）
        """
        if field_name in self.field_labels:
            label_widget = self.field_labels[field_name]
            if style_name:
                label_widget.configure(style=style_name)
            if bootstyle:
                label_widget.configure(bootstyle=bootstyle)
    
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
            
            # 允许备注字段为空
            if not value and field_name.lower() != "note" and label != "备注":
                self.error_labels[field_name].config(text=f"{label}不能为空")
                self.entries[field_name].focus_set()
                valid = False
                break
            
            # 根据类型验证并转换
            try:
                if not value and (field_name.lower() == "note" or label == "备注"):
                    # 备注字段可以为空
                    values[field_name] = ""
                elif field_type == 'int':
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