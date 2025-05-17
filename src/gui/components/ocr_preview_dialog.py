import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk, messagebox

class OCRPreviewDialog:
    """
    通用OCR识别结果预览对话框组件
    用于在所有具有OCR功能的标签页中显示统一风格的预览窗口
    支持表格显示、数据编辑和确认导入
    """
    def __init__(self, parent, title="OCR识别数据预览", chinese_font=None):
        """
        初始化OCR预览对话框
        
        参数:
            parent: 父窗口
            title: 对话框标题
            chinese_font: 中文字体
        """
        self.parent = parent
        self.title = title
        self.chinese_font = chinese_font or "SimHei"
        self.window = None
        self.callback = None
        self.tree = None
        self.tree_data = {}
        self.edit_entry = None
        self.edit_frame = None
        self.current_edit = {
            'item_id': None,
            'column': None,
            'column_index': None
        }
    
    def show(self, data_list, columns, column_widths=None, column_aligns=None, 
             callback=None, bootstyle="warning"):
        """
        显示OCR预览对话框
        
        参数:
            data_list: 要显示的数据列表
            columns: 列名元组，如 ('物品名称', '数量', '单价', '手续费', '总金额')
            column_widths: 列宽字典，如 {'物品名称': 180, '数量': 90}
            column_aligns: 列对齐方式字典，如 {'物品名称': 'w', '数量': 'e'}
            callback: 确认导入后的回调函数，接收确认后的数据列表作为参数
            bootstyle: 对话框样式，如 "warning", "primary", "info"
        """
        self.callback = callback
        
        # 创建预览窗口
        self.window = tb.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.minsize(650, 450)
        self.window.geometry("750x550")
        
        # 设置窗口图标
        if hasattr(self.parent, 'iconbitmap') and callable(self.parent.iconbitmap):
            self.window.iconbitmap(self.parent.iconbitmap())
        
        # 创建主框架
        main_frame = tb.Frame(self.window, bootstyle="light")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 标题标签
        tb.Label(
            main_frame, 
            text="请确认OCR识别结果，可以在导入前修改数据（双击单元格可编辑）", 
            font=(self.chinese_font, 12, "bold"),
            bootstyle=bootstyle
        ).pack(pady=(0, 10))
        
        # 创建表格框架，限制高度
        table_container = tb.Frame(main_frame, bootstyle="light", height=350)
        table_container.pack(fill='both', expand=True, pady=(0, 15))
        table_container.pack_propagate(False)  # 防止子组件影响容器大小
        
        # 创建表格框架
        table_frame = tb.Frame(table_container, bootstyle="light")
        table_frame.pack(fill='both', expand=True)
        
        # 设置默认列宽和对齐方式
        if not column_widths:
            column_widths = {col: 120 for col in columns}
        
        if not column_aligns:
            column_aligns = {col: 'center' for col in columns}
            # 通常第一列是名称，左对齐
            if len(columns) > 0:
                column_aligns[columns[0]] = 'w'
            # 通常数字列右对齐
            for col in columns:
                if '数量' in col or '价格' in col or '单价' in col or '金额' in col or '费' in col:
                    column_aligns[col] = 'e'
        
        # 创建表格
        self.tree = tb.Treeview(table_frame, columns=columns, show='headings', 
                               height=10, bootstyle=bootstyle)
        
        for col in columns:
            self.tree.heading(col, text=col, anchor='center')
            width = column_widths.get(col, 120)
            align = column_aligns.get(col, 'center')
            self.tree.column(col, width=width, anchor=align)
        
        # 滚动条
        scrollbar = tb.Scrollbar(table_frame, orient="vertical", command=self.tree.yview, 
                               bootstyle=f"{bootstyle}-round")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置表格样式
        self.tree.tag_configure('evenrow', background='#fdf7f0')
        self.tree.tag_configure('oddrow', background='#ffffff')
        
        # 清空树数据
        self.tree_data = {}
        
        # 添加数据到表格
        self._populate_tree(data_list)
        
        # 创建编辑框
        self.edit_frame = tb.Frame(self.window)
        self.edit_entry = tb.Entry(self.edit_frame, bootstyle=bootstyle)
        
        # 绑定事件
        self.tree.bind('<Double-1>', self._edit_cell)
        self.edit_entry.bind('<Return>', self._save_edit)
        self.edit_entry.bind('<FocusOut>', self._save_edit)
        
        # 按钮区域 - 使用固定高度的框架
        button_container = tb.Frame(main_frame, bootstyle="light", height=60)
        button_container.pack(side='bottom', fill='x')
        button_container.pack_propagate(False)  # 防止子组件影响容器大小
        
        # 按钮框架
        button_frame = tb.Frame(button_container)
        button_frame.pack(expand=True, fill='both')
        
        # 取消按钮
        tb.Button(
            button_frame, 
            text="取消", 
            command=self.window.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side='left', padx=40, pady=5, ipady=8, ipadx=15)
        
        # 导入按钮
        tb.Button(
            button_frame, 
            text="确认导入", 
            command=self._import_data,
            bootstyle=bootstyle,
            width=15
        ).pack(side='right', padx=40, pady=5, ipady=8, ipadx=15)
        
        # 设置模态
        self.window.transient(self.parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)
    
    def _populate_tree(self, data_list):
        """将数据填充到表格中"""
        for i, data in enumerate(data_list):
            # 设置交替行颜色
            row_tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            
            # 获取所有值
            values = []
            for col in self.tree['columns']:
                # 尝试从数据中获取值，如果不存在则使用空字符串
                if isinstance(data, dict):
                    # 将列名转换为可能的键名
                    key = col.lower().replace(' ', '_')
                    value = data.get(key, data.get(col, ''))
                else:
                    # 如果数据不是字典，假设是列表或元组
                    try:
                        idx = self.tree['columns'].index(col)
                        value = data[idx] if idx < len(data) else ''
                    except:
                        value = ''
                
                # 格式化数字
                if isinstance(value, (int, float)) and ('花费' in col or '费' in col):
                    # 花费和费用类数据显示为整数，无小数
                    value = f"{int(value):,}"
                elif isinstance(value, (int, float)) and '金额' in col:
                    value = f"{int(value):,}"  # 金额也显示为整数
                elif isinstance(value, (int, float)):
                    value = f"{value:,}"
                
                values.append(value)
            
            # 插入数据
            item_id = self.tree.insert('', 'end', values=values, tags=row_tags)
            
            # 存储原始数据
            self.tree_data[item_id] = data
    
    def _edit_cell(self, event):
        """处理双击编辑单元格"""
        # 获取点击的单元格
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item_id or not column:
            return
        
        # 获取列索引（从#1开始）
        column_index = int(column[1:]) - 1
        
        # 不允许编辑某些列（如总金额列）
        if self.tree['columns'][column_index] == '总金额':
            return
        
        # 获取单元格区域
        bbox = self.tree.bbox(item_id, column)
        if not bbox:
            return
        
        # 配置编辑框
        self.edit_entry.delete(0, 'end')
        current_value = self.tree.item(item_id, 'values')[column_index]
        self.edit_entry.insert(0, current_value)
        
        # 放置编辑框
        self.edit_frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.edit_entry.pack(fill='both', expand=True)
        self.edit_entry.focus_set()
        
        # 更新当前编辑信息
        self.current_edit['item_id'] = item_id
        self.current_edit['column'] = column
        self.current_edit['column_index'] = column_index
    
    def _save_edit(self, event=None):
        """保存编辑结果"""
        if not self.current_edit['item_id']:
            return
        
        item_id = self.current_edit['item_id']
        column_index = self.current_edit['column_index']
        column_name = self.tree['columns'][column_index]
        new_value = self.edit_entry.get()
        
        # 获取当前行的值
        values = list(self.tree.item(item_id, 'values'))
        
        # 更新值
        values[column_index] = new_value
        
        # 更新树数据
        data = self.tree_data[item_id]
        if isinstance(data, dict):
            # 将列名转换为键名
            key = column_name.lower().replace(' ', '_')
            
            # 尝试转换为适当的类型
            try:
                if '数量' in column_name:
                    data[key] = int(new_value)
                elif '价格' in column_name or '单价' in column_name or '费' in column_name:
                    data[key] = float(new_value)
                else:
                    data[key] = new_value
            except ValueError:
                # 如果转换失败，保持原值
                pass
            
            # 如果存在总金额列，更新总金额
            if '总金额' in self.tree['columns']:
                total_index = self.tree['columns'].index('总金额')
                # 计算总金额（通常是数量 * 单价 - 手续费）
                if '数量' in data and ('单价' in data or '价格' in data) and '手续费' in data:
                    quantity = data.get('数量', data.get('quantity', 0))
                    price = data.get('单价', data.get('unit_price', data.get('价格', 0)))
                    fee = data.get('手续费', data.get('fee', 0))
                    total = quantity * price - fee
                    data['总金额'] = total
                    data['total_amount'] = total
                    values[total_index] = f"{int(total):,}"  # 显示为整数
        
        # 更新表格
        self.tree.item(item_id, values=values)
        
        # 隐藏编辑框
        self.edit_frame.place_forget()
        self.current_edit['item_id'] = None
    
    def _import_data(self):
        """导入按钮的回调函数"""
        confirmed_data = []
        
        for item_id in self.tree.get_children():
            data = self.tree_data[item_id]
            
            # 数据验证
            if isinstance(data, dict):
                # 检查必要字段
                required_fields = ['物品名称', '数量', '单价']
                required_keys = ['item_name', 'quantity', 'unit_price']
                
                # 检查字典中是否有必要的键
                has_required = any(key in data for key in required_keys)
                
                if not has_required:
                    messagebox.showerror("输入错误", f"数据无效，请检查")
                    return
            
            confirmed_data.append(data)
        
        # 关闭预览窗口
        self.window.destroy()
        
        # 调用回调函数
        if self.callback:
            self.callback(confirmed_data) 