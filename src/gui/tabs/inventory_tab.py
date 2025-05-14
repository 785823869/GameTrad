import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from datetime import datetime

class InventoryTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self.create_tab()

    def create_tab(self):
        inventory_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(inventory_frame, text="库存管理")
        columns = ('物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值')
        self.inventory_tree = ttk.Treeview(inventory_frame, columns=columns, show='headings', height=18)
        for col in columns:
            self.inventory_tree.heading(col, text=col, anchor='center')
            self.inventory_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(inventory_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        self.inventory_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        right_panel = ttk.Frame(inventory_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        ttk.Button(right_panel, text="刷新库存", command=self.refresh_inventory).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="导出库存", command=self.export_inventory).pack(fill='x', pady=(0, 10), ipady=4)
        self.inventory_menu = tb.Menu(self.inventory_tree, tearoff=0)
        self.inventory_menu.add_command(label="删除", command=self.delete_inventory_item)
        self.inventory_tree.bind("<Button-3>", self.show_inventory_menu)

    def refresh_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        stock_in_data = self.db_manager.get_stock_in()
        stock_out_data = self.db_manager.get_stock_out()
        inventory_dict = {}
        for row in stock_in_data:
            try:
                _, item_name, _, qty, cost, *_ = row
            except Exception as e:
                messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrow={row}")
                continue
            if item_name not in inventory_dict:
                inventory_dict[item_name] = {
                    'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                }
            inventory_dict[item_name]['in_qty'] += qty
            inventory_dict[item_name]['in_amount'] += cost
        for row in stock_out_data:
            try:
                _, item_name, _, qty, unit_price, fee, deposit, total_amount, note, *_ = row
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrow={row}")
                continue
            amount = unit_price * qty - fee
            if item_name not in inventory_dict:
                inventory_dict[item_name] = {
                    'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                }
            inventory_dict[item_name]['out_qty'] += qty
            inventory_dict[item_name]['out_amount'] += amount
        for item, data in inventory_dict.items():
            remain_qty = data['in_qty'] - data['out_qty']
            in_avg = data['in_amount'] / data['in_qty'] if data['in_qty'] else 0
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] else 0
            profit = (out_avg - in_avg) * data['out_qty'] if data['out_qty'] else 0
            profit_rate = ((out_avg - in_avg) / in_avg * 100) if in_avg else 0
            total_profit = (out_avg - in_avg) * data['out_qty'] if data['out_qty'] else 0
            value = remain_qty * in_avg
            self.inventory_tree.insert('', 'end', values=(
                item,
                int(remain_qty),
                str(int(round(in_avg))),
                str(int(round(in_avg))),
                str(int(round(out_avg))),
                f"{int(profit/10000)}万",
                f"{int(round(profit_rate))}%",
                f"{int(total_profit/10000)}万",
                f"{value/10000:.2f}万"
            ))

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