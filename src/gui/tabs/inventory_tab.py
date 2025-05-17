import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from datetime import datetime

class InventoryTab:
    def __init__(self, parent_frame, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.parent_frame = parent_frame
        
        # 初始化状态变量
        self.status_var = tk.StringVar(value="就绪")
        
        # 设置中文字体
        self.chinese_font = main_gui.chinese_font
        
        # 创建样式
        self.setup_styles()
        
        self.create_tab()

    def setup_styles(self):
        """设置自定义样式"""
        style = tb.Style()
        
        # 表格样式 - 增加行高，改进字体设置
        style.configure("Inventory.Treeview", 
                      rowheight=32,  # 增加行高
                      font=(self.chinese_font, 10),
                      background="#ffffff",
                      fieldbackground="#ffffff",
                      foreground="#2c3e50")
                      
        style.configure("Inventory.Treeview.Heading", 
                      font=(self.chinese_font, 10, "bold"),
                      background="#e0e6ed",
                      foreground="#2c3e50")
        
        # 移除表格行鼠标悬停效果的style.map设置，改为使用标签和事件处理
        style.map('Inventory.Treeview', 
                background=[('selected', '#3498db')])  # 只保留选中效果
        
        # 按钮样式
        style.configure("Inventory.TButton", 
                      font=(self.chinese_font, 10),
                      foreground="#ffffff")
        
        # 状态栏样式
        style.configure("Status.TLabel", 
                      font=(self.chinese_font, 9),
                      foreground="#555555")
        
        # 搜索框样式
        style.configure("Search.TLabel", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50")
        
        style.configure("Search.TEntry", 
                      font=(self.chinese_font, 10),
                      foreground="#2c3e50")

    def create_tab(self):
        # 使用ttkbootstrap的风格创建主框架
        main_frame = tb.Frame(self.parent_frame, bootstyle="light", padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # 顶部控制区域 - 使用card风格
        control_frame = tb.Frame(main_frame, bootstyle="light")
        control_frame.pack(fill='x', pady=(0, 10))
        
        # 创建搜索区域
        search_frame = tb.LabelFrame(control_frame, text="筛选库存", bootstyle="info", padding=10)
        search_frame.pack(side='left', padx=(0, 10), fill='y')
        
        # 使用ttkbootstrap的Grid布局使搜索区域更美观
        tb.Label(search_frame, text="搜索物品:", bootstyle="info").grid(row=0, column=0, padx=(0, 5), pady=5)
        
        self.search_var = tk.StringVar()
        search_entry = tb.Entry(search_frame, textvariable=self.search_var, width=20, bootstyle="info")
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.bind("<Return>", lambda e: self.filter_inventory())
        
        button_frame = tb.Frame(search_frame, bootstyle="light")
        button_frame.grid(row=0, column=2, padx=5, pady=5, columnspan=2)
        
        tb.Button(button_frame, text="搜索", 
                command=self.filter_inventory,
                bootstyle="info").pack(side='left', padx=2)
        
        tb.Button(button_frame, text="清除", 
                command=lambda: [self.search_var.set(""), self.filter_inventory()],
                bootstyle="secondary").pack(side='left', padx=2)
        
        # 创建操作按钮区域
        action_frame = tb.LabelFrame(control_frame, text="操作", bootstyle="success", padding=10)
        action_frame.pack(side='right', padx=5, fill='y')
        
        # 刷新按钮增加图标风格
        refresh_btn = tb.Button(action_frame, 
                              text="刷新数据", 
                              command=self.refresh_inventory,
                              bootstyle="success-outline")
        refresh_btn.pack(side='right', padx=5, ipady=2)
        
        # 导出按钮
        export_btn = tb.Button(action_frame, 
                             text="导出库存", 
                             command=self.export_inventory,
                             bootstyle="success-outline")
        export_btn.pack(side='right', padx=5, ipady=2)
        
        # 表格区域 - 使用ttkbootstrap风格
        table_frame = tb.Frame(main_frame, bootstyle="light")
        table_frame.pack(fill='both', expand=True)
        
        columns = ('物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值')
        
        # 使用ttkbootstrap的Treeview组件
        self.inventory_tree = tb.Treeview(table_frame, columns=columns, show='headings', 
                                       height=18, bootstyle="info", style="Inventory.Treeview")
        
        # 优化列宽和对齐方式
        column_widths = {
            '物品': 200,  # 加宽物品名称列
            '库存数': 90,
            '总入库均价': 110,
            '保本均价': 110,
            '总出库均价': 110,
            '利润': 100,
            '利润率': 90,
            '成交利润额': 130,
            '库存价值': 130  # 加宽库存价值列
        }
        
        # 列对齐方式设置
        column_aligns = {
            '物品': 'w',    # 文本左对齐
            '库存数': 'e',   # 数字右对齐
            '总入库均价': 'e',
            '保本均价': 'e',
            '总出库均价': 'e',
            '利润': 'e',
            '利润率': 'e',
            '成交利润额': 'e',
            '库存价值': 'e'
        }
        
        for col in columns:
            self.inventory_tree.heading(col, text=col, anchor='center')
            width = column_widths.get(col, 120)
            align = column_aligns.get(col, 'center')
            self.inventory_tree.column(col, width=width, anchor=align)
        
        # 使用ttkbootstrap的Scrollbar
        scrollbar = tb.Scrollbar(table_frame, orient="vertical", command=self.inventory_tree.yview, bootstyle="info-round")
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置交替行颜色和悬停高亮
        self.inventory_tree.tag_configure('evenrow', background='#f5f9fc')  # 更淡的蓝灰色
        self.inventory_tree.tag_configure('oddrow', background='#ffffff')
        self.inventory_tree.tag_configure('profit_positive', foreground='#27ae60')  # 深绿色
        self.inventory_tree.tag_configure('profit_negative', foreground='#c0392b')  # 深红色
        # 添加悬停高亮标签
        self.inventory_tree.tag_configure('hovering', background='#f0f7ff')  # 鼠标悬停效果
        
        # 绑定鼠标移动事件
        self.inventory_tree.bind("<Motion>", self.on_treeview_motion)
        # 记录上一个高亮的行
        self.last_hover_row = None
        
        # 右键菜单使用ttkbootstrap样式
        self.inventory_menu = tb.Menu(self.inventory_tree, tearoff=0)
        self.inventory_menu.add_command(label="删除物品", command=self.delete_inventory_item)
        self.inventory_menu.add_command(label="复制物品名", command=lambda: self.copy_item_name())
        self.inventory_tree.bind("<Button-3>", self.show_inventory_menu)
        
        # 支持Ctrl+A全选
        self.inventory_tree.bind('<Control-a>', lambda e: [self.inventory_tree.selection_set(self.inventory_tree.get_children()), 'break'])
        
        # 添加状态栏 - 使用ttkbootstrap的Meter组件展示加载状态
        status_frame = tb.Frame(main_frame, bootstyle="light")
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        # 状态栏增加更多信息
        status_label = tb.Label(status_frame, textvariable=self.status_var, bootstyle="secondary")
        status_label.pack(side='left')
        
        # 初始加载数据
        self.refresh_inventory()

    def filter_inventory(self):
        search_text = self.search_var.get().lower()
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
            
        self.refresh_inventory(search_text)

    def refresh_inventory(self, search_text=""):
        """刷新库存数据，支持搜索过滤"""
        # 清空现有数据
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
            
        try:
            # 确保从数据库获取最新数据
            inventory_data = self.db_manager.get_inventory()
            
            # 过滤数据
            filtered_data = []
            search_text = search_text.lower()
            for item in inventory_data:
                try:
                    # 使用星号解包处理前面的几个必要字段
                    item_id, item_name, quantity, avg_price, *other_fields = item
                    if search_text and search_text not in item_name.lower():
                        continue
                    filtered_data.append(item)
                except Exception as e:
                    print(f"过滤库存数据错误: {e}")
                    continue
            
            # 添加数据到表格
            for i, item in enumerate(filtered_data):
                try:
                    # 只提取前10个字段，忽略多余的字段
                    item_id, item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = item
                    
                    # 格式化数据
                    quantity_str = f"{int(quantity):,}" if quantity else "0"
                    avg_price_str = f"{float(avg_price):,.2f}" if avg_price else "0.00"
                    break_even_str = f"{float(break_even_price):,.2f}" if break_even_price else "0.00"
                    selling_price_str = f"{float(selling_price):,.2f}" if selling_price else "0.00"
                    profit_str = f"{float(profit):,.2f}" if profit else "0.00"
                    profit_rate_str = f"{float(profit_rate):,.2f}%" if profit_rate else "0.00%"
                    total_profit_str = f"{float(total_profit):,.2f}" if total_profit else "0.00"
                    inventory_value_str = f"{float(inventory_value):,.2f}" if inventory_value else "0.00"
                    
                    # 添加到表格，并设置多种标签
                    tags = []
                    
                    # 交替行颜色
                    if i % 2 == 0:
                        tags.append('evenrow')
                    else:
                        tags.append('oddrow')
                    
                    # 库存和利润标签
                    if int(quantity) <= 0:
                        tags.append('no_stock')
                    elif float(profit) < 0:
                        tags.append('profit_negative')
                    elif float(profit) > 0:
                        tags.append('profit_positive')
                        
                    self.inventory_tree.insert("", "end", values=(
                        item_name, quantity_str, avg_price_str, break_even_str, 
                        selling_price_str, profit_str, profit_rate_str, total_profit_str, inventory_value_str
                    ), tags=tags)
                    
                    # 绑定工具提示事件，显示完整信息
                    self.inventory_tree.bind("<Motion>", self.on_tree_motion)
                    
                except Exception as e:
                    print(f"添加库存数据到表格错误: {e}")
                    continue
            
            # 设置行标签样式
            self.inventory_tree.tag_configure("profit_positive", foreground="#28a745")  # 绿色代表盈利
            self.inventory_tree.tag_configure("profit_negative", foreground="#dc3545")  # 红色代表亏损
            self.inventory_tree.tag_configure("no_stock", foreground="#ff6000", background="#fff3e0")  # 橙色背景代表无库存/负库存
            
            # 更新状态栏
            self.status_var.set(f"共 {len(filtered_data)} 条记录  |  上次更新: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.status_var.set(f"刷新库存数据错误: {e}")
            import traceback
            traceback.print_exc()
    
    def on_tree_motion(self, event):
        """处理鼠标移动事件，显示工具提示"""
        # 识别当前鼠标位置的行和列
        row_id = self.inventory_tree.identify_row(event.y)
        col_id = self.inventory_tree.identify_column(event.x)
        
        if row_id and col_id:
            # 获取列索引
            col_index = int(col_id.replace('#', '')) - 1
            # 获取单元格内容
            cell_value = self.inventory_tree.item(row_id, 'values')[col_index]
            
            # 显示工具提示 - 仅当内容可能被截断时显示
            if col_index == 0 and len(str(cell_value)) > 20:  # 物品名称列
                self.show_tooltip(event, cell_value)
            elif col_index > 0 and len(str(cell_value)) > 10:  # 数字列
                self.show_tooltip(event, cell_value)
            else:
                self.hide_tooltip()
        else:
            self.hide_tooltip()
    
    def show_tooltip(self, event, text):
        """显示工具提示"""
        # 这里可以实现工具提示功能，但ttk没有内置的tooltip
        # 如果需要实现完整功能，需要单独实现一个tooltip类
        pass
        
    def hide_tooltip(self):
        """隐藏工具提示"""
        pass

    def export_inventory(self):
        import pandas as pd
        try:
            data = [self.inventory_tree.item(item)['values'] for item in self.inventory_tree.get_children()]
            columns = ['物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值']
            file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')], title='导出库存')
            if not file_path:
                return
            ext = file_path.split('.')[-1].lower()
            if ext == 'xlsx':
                pd.DataFrame(data, columns=columns).to_excel(file_path, index=False)
            elif ext == 'csv':
                pd.DataFrame(data, columns=columns).to_csv(file_path, index=False, encoding='utf-8-sig')
            messagebox.showinfo('成功', f'库存已导出到 {file_path}')
        except Exception as e:
            messagebox.showerror('错误', f'导出库存失败: {str(e)}')

    def show_inventory_menu(self, event):
        item = self.inventory_tree.identify_row(event.y)
        if item:
            if item not in self.inventory_tree.selection():
                self.inventory_tree.selection_set(item)
            self.inventory_menu.post(event.x_root, event.y_root)

    def delete_inventory_item(self):
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            return
        names = [self.inventory_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下库存物品吗？\n" + "，".join(str(n) for n in names)
        if messagebox.askyesno("确认删除", msg):
            for item in selected_items:
                self.inventory_tree.delete(item)
            self.refresh_inventory()
    
    def copy_item_name(self):
        """复制选中的物品名称到剪贴板"""
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            return
        
        item_name = self.inventory_tree.item(selected_items[0])['values'][0]
        self.parent_frame.clipboard_clear()
        self.parent_frame.clipboard_append(item_name)
        self.status_var.set(f"已复制: {item_name}")

    def on_treeview_motion(self, event):
        """处理鼠标在表格上的移动，动态应用悬停高亮效果"""
        # 识别当前鼠标位置的行
        row_id = self.inventory_tree.identify_row(event.y)
        
        # 如果鼠标离开了上一个高亮行，恢复其原始样式
        if self.last_hover_row and self.last_hover_row != row_id:
            # 获取行的当前标签
            current_tags = list(self.inventory_tree.item(self.last_hover_row, 'tags'))
            # 移除悬停标签
            if 'hovering' in current_tags:
                current_tags.remove('hovering')
                self.inventory_tree.item(self.last_hover_row, tags=current_tags)
                
        # 如果鼠标位于一个有效行上，应用悬停高亮效果
        if row_id and row_id != self.last_hover_row:
            # 获取行的当前标签
            current_tags = list(self.inventory_tree.item(row_id, 'tags'))
            # 添加悬停标签
            if 'hovering' not in current_tags:
                current_tags.append('hovering')
                self.inventory_tree.item(row_id, tags=current_tags)
                
        # 更新上一个高亮行的记录
        self.last_hover_row = row_id if row_id else None 