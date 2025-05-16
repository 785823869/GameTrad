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
        
        self.create_tab()

    def create_tab(self):
        main_frame = ttk.Frame(self.parent_frame, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # 顶部控制区
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        # 创建搜索区域
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side='left')
        
        ttk.Label(search_frame, text="搜索:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=(0, 5))
        search_entry.bind("<Return>", lambda e: self.filter_inventory())
        
        ttk.Button(search_frame, text="搜索", 
                 command=self.filter_inventory,
                 bootstyle="primary-outline").pack(side='left')
        
        ttk.Button(search_frame, text="清除", 
                 command=lambda: [self.search_var.set(""), self.filter_inventory()],
                 bootstyle="secondary-outline").pack(side='left', padx=5)
        
        # 创建刷新按钮
        refresh_btn = ttk.Button(control_frame, 
                               text="刷新数据", 
                               command=self.refresh_inventory,
                               bootstyle="info")
        refresh_btn.pack(side='right', padx=5)
        
        # 表格区域
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True)
        
        columns = ('物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值')
        
        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=18, style="Modern.Treeview")
        
        for col in columns:
            self.inventory_tree.heading(col, text=col, anchor='center')
            self.inventory_tree.column(col, width=120, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.inventory_tree.yview, bootstyle="primary-round")
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置交替行颜色和悬停高亮
        self.inventory_tree.tag_configure('evenrow', background='#f9f9f9')
        self.inventory_tree.tag_configure('oddrow', background='#ffffff')
        self.inventory_tree.tag_configure('profit_positive', foreground='#27ae60')  # 深绿色
        self.inventory_tree.tag_configure('profit_negative', foreground='#c0392b')  # 深红色
        
        self.inventory_menu = tb.Menu(self.inventory_tree, tearoff=0)
        self.inventory_menu.add_command(label="删除", command=self.delete_inventory_item)
        self.inventory_tree.bind("<Button-3>", self.show_inventory_menu)
        
        self.inventory_tree.bind('<Control-a>', lambda e: [self.inventory_tree.selection_set(self.inventory_tree.get_children()), 'break'])
        
        # 添加状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side='left')
        
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
            for item in filtered_data:
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
                    
                    # 添加到表格，并根据库存和利润添加标签
                    if int(quantity) <= 0:
                        tag = "no_stock"
                    elif float(profit) < 0:
                        tag = "negative"
                    elif float(profit) > 0:
                        tag = "positive"
                    else:
                        tag = ""
                        
                    self.inventory_tree.insert("", "end", values=(
                        item_name, quantity_str, avg_price_str, break_even_str, 
                        selling_price_str, profit_str, profit_rate_str, total_profit_str, inventory_value_str
                    ), tags=(tag,))
                    
                except Exception as e:
                    print(f"添加库存数据到表格错误: {e}")
                    continue
            
            # 设置行标签样式
            self.inventory_tree.tag_configure("positive", foreground="#28a745")  # 绿色代表盈利
            self.inventory_tree.tag_configure("negative", foreground="#dc3545")  # 红色代表亏损
            self.inventory_tree.tag_configure("no_stock", foreground="#ff6000", background="#fff3e0")  # 橙色背景代表无库存/负库存
            
            # 更新状态栏
            self.status_var.set(f"共 {len(filtered_data)} 条记录")
        except Exception as e:
            self.status_var.set(f"刷新库存数据错误: {e}")
            import traceback
            traceback.print_exc()

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
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                self.inventory_tree.delete(item)
            self.refresh_inventory() 