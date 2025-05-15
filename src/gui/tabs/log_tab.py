import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, StringVar
import tkinter as tk
import json

class LogTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self.log_page = 1
        self.log_page_size = 20
        self.log_total_pages = 1
        self.filter_type = StringVar(value="全部")
        self.filter_tab = StringVar(value="全部")
        self.filter_reverted = StringVar(value="全部")
        self.log_search_var = StringVar()
        self.log_jump_var = StringVar()
        self._init_ui()

    def _init_ui(self):
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text="操作日志")
        columns = ("操作类型", "标签页", "操作时间", "数据")
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show='headings', height=18)
        for col in columns:
            self.log_tree.heading(col, text=col, anchor='center')
            self.log_tree.column(col, width=160, anchor='center')
        self.log_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        filter_frame = ttk.Frame(log_frame, padding=4)
        filter_frame.pack(side='top', fill='x')
        ttk.Label(filter_frame, text="操作类型:").pack(side='left')
        ttk.Combobox(filter_frame, textvariable=self.filter_type, values=["全部", "添加", "修改", "删除", "推送"], width=8, state='readonly').pack(side='left', padx=2)
        ttk.Label(filter_frame, text="标签页:").pack(side='left')
        ttk.Combobox(filter_frame, textvariable=self.filter_tab, values=["全部", "入库管理", "出库管理", "交易监控"], width=10, state='readonly').pack(side='left', padx=2)
        ttk.Label(filter_frame, text="已回退:").pack(side='left')
        ttk.Combobox(filter_frame, textvariable=self.filter_reverted, values=["全部", "是", "否"], width=6, state='readonly').pack(side='left', padx=2)
        ttk.Label(filter_frame, text="关键字:").pack(side='left')
        ttk.Entry(filter_frame, textvariable=self.log_search_var, width=12).pack(side='left', padx=2)
        btn_frame = ttk.Frame(log_frame, padding=8)
        btn_frame.pack(side='bottom', fill='x', pady=8)
        ttk.Button(btn_frame, text="搜索", command=self._log_search).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="上一页", command=self.log_prev_page).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="下一页", command=self.log_next_page).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="导出日志", command=self.export_log_csv).pack(side='left', padx=2)
        self.log_page_label = ttk.Label(btn_frame, text="第1/1页")
        self.log_page_label.pack(side='left', padx=4)
        ttk.Entry(btn_frame, textvariable=self.log_jump_var, width=4).pack(side='left')
        ttk.Button(btn_frame, text="跳转", command=self.log_jump_page).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="回退当前操作", command=self.main_gui.undo_last_operation).pack(side='right', padx=8)
        ttk.Button(btn_frame, text="前进(撤销回退)", command=self.main_gui.redo_last_operation).pack(side='right', padx=8)
        ttk.Button(btn_frame, text="批量删除", command=self.delete_log_items).pack(side='left', padx=2)
        self.log_tree.bind('<Double-1>', self.show_log_detail)
        self.log_tree.bind('<Control-a>', lambda e: [self.log_tree.selection_set(self.log_tree.get_children()), 'break'])
        self.refresh_log_tab()

    def _log_search(self):
        self.log_page = 1
        self.refresh_log_tab()

    def log_prev_page(self):
        if self.log_page > 1:
            self.log_page -= 1
            self.refresh_log_tab()

    def log_next_page(self):
        self.log_page += 1
        self.refresh_log_tab()

    def log_jump_page(self):
        try:
            page = int(self.log_jump_var.get())
            if 1 <= page <= self.log_total_pages:
                self.log_page = page
                self.refresh_log_tab()
            else:
                messagebox.showwarning("提示", f"页码范围：1~{self.log_total_pages}")
        except Exception:
            messagebox.showwarning("提示", "请输入有效的页码")

    def refresh_log_tab(self):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        logs = self.db_manager.get_operation_logs(
            tab_name=None,
            op_type=None,
            keyword=None,
            reverted=None,
            page=1,
            page_size=100
        )
        for log in logs:
            is_reverted = bool(log['已回退'])
            self.log_tree.insert('', 'end', values=(
                log['操作类型'] + ("（已回退）" if is_reverted else ""),
                log['标签页'],
                log['操作时间'],
                json.dumps(log['数据'], ensure_ascii=False)
            ))

    def export_log_csv(self):
        import pandas as pd
        import os
        from tkinter import filedialog
        try:
            logs = self.db_manager.get_operation_logs(
                tab_name=None,
                op_type=None,
                keyword=None,
                reverted=None,
                page=1,
                page_size=10000
            )
            columns = ["操作类型", "标签页", "操作时间", "数据"]
            data = [[log['操作类型'], log['标签页'], log['操作时间'], json.dumps(log['数据'], ensure_ascii=False)] for log in logs]
            file_path = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')],
                title='导出日志'
            )
            if not file_path:
                return
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xlsx':
                pd.DataFrame(data, columns=columns).to_excel(file_path, index=False)
                messagebox.showinfo('成功', f'日志已导出到 {file_path}')
            elif ext == '.csv':
                pd.DataFrame(data, columns=columns).to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo('成功', f'日志已导出为csv文件 {file_path}')
            else:
                messagebox.showerror('错误', '不支持的文件格式')
        except Exception as e:
            messagebox.showerror('错误', f'导出日志失败: {str(e)}')

    def delete_log_items(self):
        selected_items = self.log_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要删除的日志记录！")
            return
        if not messagebox.askyesno("确认", f"确定要删除选中的 {len(selected_items)} 条日志记录吗？此操作不可恢复。"):
            return
        deleted_count = 0
        for item in selected_items:
            values = self.log_tree.item(item)['values']
            op_type = values[0].replace("（已回退）", "")
            tab = values[1]
            op_time = values[2]
            try:
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM operation_logs WHERE operation_type=%s AND tab_name=%s AND operation_time=%s",
                    (op_type, tab, op_time)
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"删除数据库日志失败: {e}")
            self.log_tree.delete(item)
            deleted_count += 1
        messagebox.showinfo("成功", f"已删除 {deleted_count} 条日志记录！")
        self.refresh_log_tab()

    def show_log_detail(self, event):
        item = self.log_tree.identify_row(event.y)
        if not item:
            return
        values = self.log_tree.item(item)['values']
        if not values:
            return
        op_type, tab_name, timestamp, data = values
        detail_window = tk.Toplevel(self.main_gui.root)
        detail_window.title("操作详情")
        detail_window.geometry("1200x600")
        main_frame = ttk.Frame(detail_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, text=f"操作类型：{op_type}", font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Label(info_frame, text=f"标签页：{tab_name}", font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Label(info_frame, text=f"操作时间：{timestamp}", font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        try:
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, (list, dict)):
                ttk.Label(tree_frame, text="（无数据）", font=('Microsoft YaHei', 10)).pack(pady=20)
                return
            # 先根据tab_name赋值columns和field_map
            if tab_name == "入库管理":
                columns = ["物品名", "入库时间", "入库数量", "入库花费", "入库均价", "备注"]
                field_map = {
                    "物品名": "item_name",
                    "入库时间": "transaction_time",
                    "入库数量": "quantity",
                    "入库花费": "cost",
                    "入库均价": "avg_cost",
                    "备注": "note"
                }
            elif tab_name == "出库管理":
                columns = ["物品名", "出库时间", "出库数量", "单价", "手续费", "保证金", "总金额", "备注"]
                field_map = {
                    "物品名": "item_name",
                    "出库时间": "transaction_time",
                    "出库数量": "quantity",
                    "单价": "unit_price",
                    "手续费": "fee",
                    "保证金": "deposit",
                    "总金额": "total_amount",
                    "备注": "note"
                }
            elif tab_name == "交易监控":
                columns = ["物品名", "数量", "一口价", "目标买入价", "计划卖出价", "保本卖出价", "利润", "利润率", "出库策略"]
                field_map = {
                    "物品名": "item_name",
                    "数量": "quantity",
                    "一口价": "market_price",
                    "目标买入价": "target_price",
                    "计划卖出价": "planned_price",
                    "保本卖出价": "break_even_price",
                    "利润": "profit",
                    "利润率": "profit_rate",
                    "出库策略": "strategy"
                }
            else:
                if isinstance(data, dict) and 'old' in data and 'new' in data:
                    sample = data['old'] if data['old'] else data['new']
                    if isinstance(sample, dict):
                        columns = list(sample.keys())
                        field_map = {col: col for col in columns}
                    elif isinstance(sample, (list, tuple)):
                        columns = [f"列{i+1}" for i in range(len(sample))]
                        field_map = {col: i for i, col in enumerate(columns)}
                    else:
                        columns = []
                        field_map = {}
                elif isinstance(data, dict):
                    columns = list(data.keys())
                    field_map = {col: col for col in columns}
                elif isinstance(data, list) and data and isinstance(data[0], dict):
                    columns = list(data[0].keys())
                    field_map = {col: col for col in columns}
                elif isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
                    columns = [f"列{i+1}" for i in range(len(data[0]))]
                    field_map = {col: i for i, col in enumerate(columns)}
                else:
                    columns = []
                    field_map = {}
            # 新增：处理修改日志结构 {'old':..., 'new':...}
            if isinstance(data, dict) and 'old' in data and 'new' in data:
                old_data = data['old']
                new_data = data['new']
                # 先显示"修改前"
                ttk.Label(main_frame, text="修改前：", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w', padx=10)
                tree_old = ttk.Treeview(tree_frame, columns=columns, show='headings', height=1)
                for col in columns:
                    tree_old.heading(col, text=col)
                    tree_old.column(col, width=120, anchor='center')
                if isinstance(old_data, (list, tuple)):
                    tree_old.insert('', 'end', values=[str(x) for x in old_data])
                elif isinstance(old_data, dict):
                    tree_old.insert('', 'end', values=[str(old_data.get(field_map.get(col, col), "")) for col in columns])
                tree_old.pack(fill=tk.X, padx=10)
                # 再显示"修改后"，高亮显示
                ttk.Label(main_frame, text="修改后：", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w', padx=10, pady=(10,0))
                style = ttk.Style()
                style.configure('Highlight.Treeview', background='#fffbe6')  # 淡黄色
                tree_new = ttk.Treeview(tree_frame, columns=columns, show='headings', height=1, style='Highlight.Treeview')
                for col in columns:
                    tree_new.heading(col, text=col)
                    tree_new.column(col, width=120, anchor='center')
                if isinstance(new_data, (list, tuple)):
                    tree_new.insert('', 'end', values=[str(x) for x in new_data])
                elif isinstance(new_data, dict):
                    tree_new.insert('', 'end', values=[str(new_data.get(field_map.get(col, col), "")) for col in columns])
                tree_new.pack(fill=tk.X, padx=10)
                return
            if isinstance(data, dict):
                data = [data]
            for row in data:
                if isinstance(row, dict):
                    values = []
                    for col in columns:
                        key = field_map.get(col, col)
                        val = row.get(key, "")
                        try:
                            if isinstance(val, (int, float)):
                                if "率" in col:
                                    val = f"{val:.2f}%"
                                elif "价" in col or "金额" in col or "花费" in col or "利润" in col:
                                    val = f"{val:,.2f}"
                                else:
                                    val = f"{int(val):,}"
                            elif isinstance(val, str) and val.replace(".", "").isdigit():
                                if "率" in col:
                                    val = f"{float(val):.2f}%"
                                elif "价" in col or "金额" in col or "花费" in col or "利润" in col:
                                    val = f"{float(val):,.2f}"
                                else:
                                    val = f"{int(float(val)):,}"
                        except (ValueError, TypeError):
                            pass
                        values.append(str(val))
                else:
                    values = []
                    for i, val in enumerate(row):
                        try:
                            if isinstance(val, (int, float)):
                                if "率" in columns[i]:
                                    val = f"{val:.2f}%"
                                elif any(keyword in columns[i] for keyword in ["价", "金额", "花费", "利润"]):
                                    val = f"{val:,.2f}"
                                else:
                                    val = f"{int(val):,}"
                            elif isinstance(val, str) and val.replace(".", "").isdigit():
                                if "率" in columns[i]:
                                    val = f"{float(val):.2f}%"
                                elif any(keyword in columns[i] for keyword in ["价", "金额", "花费", "利润"]):
                                    val = f"{float(val):,.2f}"
                                else:
                                    val = f"{int(float(val)):,}"
                        except (ValueError, TypeError):
                            pass
                        values.append(str(val))
                tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=120, anchor='center')
                tree.insert('', 'end', values=values)
                scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        except Exception as e:
            # print(f"显示日志详情失败: {e}")
            ttk.Label(tree_frame, text=f"显示数据失败: {str(e)}", font=('Microsoft YaHei', 10)).pack(pady=20)
        ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10) 