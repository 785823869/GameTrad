import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.style import Style
import platform
import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

class UIManager:
    def __init__(self, root):
        self.root = root
        self.style = tb.Style()
        self.setup_fonts()
        self.setup_colors()
        self.setup_styles()
        
    def setup_fonts(self):
        """设置全局字体"""
        system = platform.system()
        
        # 检测可用中文字体
        font_found = False
        if system == 'Windows':
            font_list = ['Microsoft YaHei', 'SimHei', 'SimSun']
        elif system == 'Darwin':  # macOS
            font_list = ['PingFang SC', 'Heiti SC', 'STHeiti']
        else:  # Linux等其他系统
            font_list = ['WenQuanYi Micro Hei', 'Droid Sans Fallback']
            
        # 查找可用字体
        for font_name in font_list:
            font_paths = fm.findSystemFonts(fontpaths=None)
            for path in font_paths:
                try:
                    if font_name.lower() in fm.FontProperties(fname=path).get_name().lower():
                        self.main_font = font_name
                        font_found = True
                        break
                except:
                    continue
            if font_found:
                break
                
        # 如果未找到，使用默认字体
        if not font_found:
            self.main_font = 'Microsoft YaHei'
        
        # 设置matplotlib字体
        plt.rcParams['font.sans-serif'] = [self.main_font, 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 定义字体大小组合
        self.small_font = (self.main_font, 10)
        self.medium_font = (self.main_font, 12)
        self.large_font = (self.main_font, 14)
        self.xlarge_font = (self.main_font, 16, "bold")
        self.title_font = (self.main_font, 18, "bold")
    
    def setup_colors(self):
        """设置全局配色方案"""
        self.colors = {
            'primary': '#2c3e50',     # 深蓝色，作为主要强调色
            'secondary': '#3498db',   # 浅蓝色
            'warning': '#f39c12',     # 橙色，更明亮
            'danger': '#e74c3c',      # 红色
            'info': '#2980b9',        # 蓝色
            'light': '#ecf0f1',       # 浅灰色
            'dark': '#2c3e50',        # 深色
            'bg_light': '#ffffff',    # 纯白背景色
            'bg_dark': '#34495e',     # 深背景色
            'text_primary': '#2c3e50', # 主文本颜色，深色更易读
            'text_secondary': '#7f8c8d' # 次要文本颜色
        }
    
    def setup_styles(self):
        """设置全局样式"""
        # 卡片样式
        self.style.configure("Card.TFrame", background=self.colors['light'])
        
        # 标题样式
        self.style.configure("Title.TLabel", 
                           font=self.title_font, 
                           foreground=self.colors['dark'])
        
        # 子标题样式
        self.style.configure("Subtitle.TLabel", 
                           font=self.large_font, 
                           foreground=self.colors['text_primary'])
        
        # 正常文本样式
        self.style.configure("TLabel", 
                           font=self.medium_font, 
                           foreground=self.colors['text_primary'])
        
        # 按钮样式
        self.style.configure("TButton", 
                           font=self.medium_font)
        
        # 表格样式 - 增强对比度
        self.style.configure("Treeview", 
                           font=self.medium_font,
                           rowheight=28,
                           background=self.colors['bg_light'],
                           fieldbackground=self.colors['bg_light'],
                           foreground=self.colors['dark'])
                           
        self.style.configure("Treeview.Heading", 
                           font=(self.main_font, 11, "bold"),
                           background=self.colors['light'],
                           foreground=self.colors['dark'])
        
        # 设置现代表格样式 - 高对比度
        self.style.configure(
            "Modern.Treeview",
            background=self.colors['bg_light'],
            foreground=self.colors['dark'],
            rowheight=30,
            fieldbackground=self.colors['bg_light'],
            borderwidth=0,
            font=self.medium_font
        )
        
        # 配置表头样式 - 突出显示
        self.style.configure(
            "Modern.Treeview.Heading",
            background="#e0e6ed",
            foreground="#2c3e50",
            relief="flat",
            font=(self.main_font, 11, "bold")
        )
        
        # 鼠标悬停效果 - 使用更明显的高亮色
        self.style.map(
            "Modern.Treeview",
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', '#ffffff')]
        )
                           
        # 其他控件样式
        self.style.configure("TEntry", font=self.medium_font)
        self.style.configure("TCombobox", font=self.medium_font)
        self.style.configure("TCheckbutton", font=self.medium_font)
        self.style.configure("TRadiobutton", font=self.medium_font)
        
    def create_card(self, parent, title, value="--", description="", icon=None):
        """创建信息卡片"""
        card = tb.Frame(parent, style="Card.TFrame", padding=15)
        
        # 标题行
        title_frame = tb.Frame(card, style="Card.TFrame")
        title_frame.pack(fill='x', anchor='w')
        
        tb.Label(title_frame, 
                text=title, 
                font=(self.main_font, 12),
                foreground=self.colors['text_secondary']).pack(side='left')
        
        if icon:
            tb.Label(title_frame, 
                    text=icon, 
                    font=("Segoe UI Symbol", 16),
                    foreground=self.colors['primary']).pack(side='right')
        
        # 值显示
        value_label = tb.Label(card,
                             text=value,
                             font=(self.main_font, 24, "bold"),
                             foreground=self.colors['primary'])
        value_label.pack(anchor='w', pady=(5, 2))
        
        # 描述
        if description:
            desc_label = tb.Label(card,
                               text=description,
                               font=self.small_font,
                               foreground=self.colors['text_secondary'])
            desc_label.pack(anchor='w')
            
        return card, value_label
    
    def create_modern_table(self, parent, columns, height=15):
        """创建现代风格的表格"""
        # 创建表格
        table = tb.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=height,
            style="Modern.Treeview"
        )
        
        # 设置列标题和宽度
        for i, col in enumerate(columns):
            table.heading(col, text=col, anchor='center')
            table.column(col, width=120, anchor='center')
        
        # 添加滚动条
        scrollbar = tb.Scrollbar(parent, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        
        # 设置交替行背景色
        table.tag_configure('evenrow', background='#f9f9f9')
        table.tag_configure('oddrow', background='#ffffff')
        
        return table, scrollbar
    
    def create_button_group(self, parent, buttons, orientation='horizontal'):
        """创建现代化的按钮组"""
        frame = tb.Frame(parent)
        
        for btn in buttons:
            button = tb.Button(
                frame,
                text=btn['text'],
                bootstyle=btn.get('style', 'primary'),
                command=btn.get('command', None),
                width=btn.get('width', 10)
            )
            
            if orientation == 'horizontal':
                button.pack(side='left', padx=5, pady=5)
            else:
                button.pack(fill='x', pady=5)
        
        return frame

    def create_search_bar(self, parent, search_command=None):
        """创建现代化的搜索栏"""
        search_frame = tb.Frame(parent)
        
        search_var = tb.StringVar()
        search_entry = tb.Entry(
            search_frame,
            textvariable=search_var,
            width=30,
            bootstyle="primary"
        )
        search_entry.pack(side='left', padx=(0, 5))
        
        search_button = tb.Button(
            search_frame,
            text="搜索",
            bootstyle="primary",
            command=lambda: search_command(search_var.get()) if search_command else None
        )
        search_button.pack(side='left')
        
        return search_frame, search_var

class ModernDialog:
    def __init__(self, parent, title, width=500, height=400):
        self.parent = parent
        # 检查parent是否有root属性，如果有使用parent.root作为对话框的父窗口
        if hasattr(parent, 'root'):
            self.dialog = tb.Toplevel(parent.root)
        else:
            self.dialog = tb.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        
        # 设置对话框样式
        self.style = tb.Style()
        
        # 设置基本样式
        self.content_frame = tb.Frame(self.dialog, padding=20)
        self.content_frame.pack(fill='both', expand=True)
        
        # 按钮区域
        self.button_frame = tb.Frame(self.dialog, padding=(0, 0, 0, 15))
        self.button_frame.pack(fill='x')
        
        # 中心对话框
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def add_buttons(self, buttons):
        """添加按钮到对话框底部"""
        for btn in buttons:
            tb.Button(
                self.button_frame,
                text=btn['text'],
                bootstyle=btn.get('style', 'primary'),
                command=btn.get('command', None),
                width=10
            ).pack(side='right', padx=5)
    
    def add_title(self, title):
        """添加对话框标题"""
        tb.Label(
            self.content_frame,
            text=title,
            font=('Microsoft YaHei', 16, 'bold')
        ).pack(pady=(0, 20), anchor='w') 