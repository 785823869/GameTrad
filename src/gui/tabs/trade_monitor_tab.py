import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
import threading
from datetime import datetime
from PIL import Image
import json

class TradeMonitorTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self._pending_ocr_images = []  # 存储待识别的图片
        self.create_tab()

    def create_tab(self):
        monitor_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(monitor_frame, text="交易监控")
        columns = ('物品', '当前时间', '数量', '一口价', '目标买入价', '计划卖出价', '保本卖出价', '利润', '利润率', '出库策略')
        self.monitor_tree = ttk.Treeview(monitor_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.monitor_tree.heading(col, text=col, anchor='center')
            self.monitor_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.monitor_tree.yview)
        self.monitor_tree.configure(yscrollcommand=scrollbar.set)
        self.monitor_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        right_panel = ttk.Frame(monitor_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        add_frame = ttk.LabelFrame(right_panel, text="添加监控", padding=10)
        add_frame.pack(fill='x', pady=8)
        ttk.Label(add_frame, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        self.monitor_item = ttk.Entry(add_frame)
        self.monitor_item.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        self.monitor_quantity = ttk.Entry(add_frame)
        self.monitor_quantity.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="一口价:").grid(row=2, column=0, padx=5, pady=5)
        self.monitor_price = ttk.Entry(add_frame)
        self.monitor_price.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="目标买入价:").grid(row=3, column=0, padx=5, pady=5)
        self.monitor_target_price = ttk.Entry(add_frame)
        self.monitor_target_price.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="计划卖出价:").grid(row=4, column=0, padx=5, pady=5)
        self.monitor_planned_price = ttk.Entry(add_frame)
        self.monitor_planned_price.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="入库策略:").grid(row=5, column=0, padx=5, pady=5)
        self.monitor_strategy = ttk.Entry(add_frame)
        self.monitor_strategy.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        add_frame.columnconfigure(1, weight=1)
        ttk.Button(add_frame, text="添加监控", command=self.add_monitor).grid(row=6, column=0, columnspan=2, pady=10, sticky='ew')
        ttk.Button(right_panel, text="刷新监控", command=self.refresh_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动识别导入", command=self.upload_ocr_import_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        self.ocr_image_preview_frame = ttk.Frame(right_panel)
        self.ocr_image_preview_frame.pack(fill='x', pady=5)
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_monitor)
        self.monitor_tree.bind("<Double-1>", self.edit_monitor_item)
        self.monitor_menu = tb.Menu(self.monitor_tree, tearoff=0)
        self.monitor_menu.add_command(label="删除", command=self.delete_monitor_item)
        self.monitor_tree.bind("<Button-3>", self.show_monitor_menu)

    def upload_ocr_import_monitor(self):
        """上传图片进行OCR识别导入"""
        file_paths = fd.askopenfilenames(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_paths:
            return
        try:
            count = 0
            for file_path in file_paths:
                img = Image.open(file_path)
                self._pending_ocr_images.append(img)
                count += 1
            self.refresh_ocr_image_preview()
            messagebox.showinfo("已添加", f"已添加{count}张图片，点击批量识别可统一导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def batch_ocr_import_monitor(self):
        """批量识别已添加的图片"""
        if not self._pending_ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
        try:
            import pytesseract
            success = False
            monitor_count = 0
            for img in self._pending_ocr_images:
                text = pytesseract.image_to_string(img, lang='chi_sim')
                data = self.parse_monitor_ocr_text(text)
                if data:
                    self.db_manager.save_trade_monitor(data)
                    monitor_count += 1
                    success = True
            if success:
                messagebox.showinfo("成功", f"成功导入{monitor_count}条监控记录")
                self.refresh_monitor()
            self._pending_ocr_images.clear()
            self.refresh_ocr_image_preview()
        except Exception as e:
            messagebox.showerror("错误", f"OCR识别失败: {e}")

    def paste_ocr_import_monitor(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._pending_ocr_images.append(img)
                self.refresh_ocr_image_preview()
                messagebox.showinfo("已添加", "已添加剪贴板图片，点击批量识别可统一导入。")
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴图片失败: {e}")

    def refresh_ocr_image_preview(self):
        """刷新OCR图片预览"""
        for widget in self.ocr_image_preview_frame.winfo_children():
            widget.destroy()
        if not self._pending_ocr_images:
            return
        preview_frame = ttk.LabelFrame(self.ocr_image_preview_frame, text="待识别图片", padding=5)
        preview_frame.pack(fill='x', pady=5)
        for i, img in enumerate(self._pending_ocr_images):
            frame = ttk.Frame(preview_frame)
            frame.pack(fill='x', pady=2)
            ttk.Label(frame, text=f"图片{i+1}").pack(side='left')
            ttk.Button(frame, text="删除", command=lambda idx=i: self.delete_ocr_image(idx)).pack(side='right')

    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            self._pending_ocr_images.pop(idx)
            self.refresh_ocr_image_preview()

    def parse_monitor_ocr_text(self, text):
        """解析OCR识别的文本为监控数据"""
        try:
            lines = text.split('\n')
            data = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if '物品' in line:
                    data['item_name'] = line.split('物品')[-1].strip()
                elif '数量' in line:
                    data['quantity'] = int(line.split('数量')[-1].strip())
                elif '一口价' in line:
                    data['market_price'] = float(line.split('一口价')[-1].strip())
                elif '目标买入价' in line:
                    data['target_price'] = float(line.split('目标买入价')[-1].strip())
                elif '计划卖出价' in line:
                    data['planned_price'] = float(line.split('计划卖出价')[-1].strip())
                elif '出库策略' in line:
                    data['strategy'] = line.split('出库策略')[-1].strip()
            if 'item_name' in data and 'quantity' in data and 'market_price' in data:
                data['monitor_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data['break_even_price'] = data.get('target_price', 0) * 1.05
                data['profit'] = data['market_price'] - data.get('target_price', 0)
                data['profit_rate'] = (data['profit'] / data.get('target_price', 1)) * 100
                return data
        except Exception as e:
            messagebox.showerror("错误", f"解析OCR文本失败: {e}")
        return None

    def show_monitor_menu(self, event):
        """显示右键菜单"""
        item = self.monitor_tree.identify_row(event.y)
        if not item:
            return
        if item not in self.monitor_tree.selection():
            self.monitor_tree.selection_set(item)
        self.monitor_menu.post(event.x_root, event.y_root)

    def delete_monitor_item(self):
        """删除选中的监控记录"""
        selected_items = self.monitor_tree.selection()
        if not selected_items:
            return
        names = [self.monitor_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下监控记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                values = self.monitor_tree.item(item)['values']
                self.db_manager.delete_trade_monitor(values[0], values[1])
                deleted_data.append(values)
            self.refresh_monitor()
            self.main_gui.log_operation('删除', '交易监控', deleted_data)

    def edit_monitor_item(self, event):
        """编辑监控记录"""
        item_id = self.monitor_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.monitor_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑监控记录")
        edit_win.minsize(480, 400)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "数量", "一口价", "目标买入价", "计划卖出价", "出库策略"]
        types = [str, int, float, float, float, str]
        entries = []
        error_labels = []
        edit_indices = [0, 2, 3, 4, 5, 9]  # 对应表格字段索引
        for i, (label, idx, typ) in enumerate(zip(labels, edit_indices, types)):
            ttk.Label(content_frame, text=label+":", style='Edit.TLabel').grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            entry = ttk.Entry(content_frame, validate='key', validatecommand=vcmd, style='Edit.TEntry') if vcmd else ttk.Entry(content_frame, style='Edit.TEntry')
            entry.insert(0, values[idx])
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='w')
            entries.append(entry)
            err = ttk.Label(content_frame, text="", foreground="red", background='#f4f8fb', font=('微软雅黑', 10))
            err.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            error_labels.append(err)

        def save():
            new_vals = [e.get() for e in entries]
            valid = True
            for idx, (val, typ, err_lbl) in enumerate(zip(new_vals, types, error_labels)):
                err_lbl.config(text="")
                if typ is int:
                    if not val.isdigit():
                        err_lbl.config(text="请输入正整数")
                        entries[idx].focus_set()
                        valid = False
                        break
                elif typ is float:
                    try:
                        float(val)
                    except Exception:
                        err_lbl.config(text="请输入数字")
                        entries[idx].focus_set()
                        valid = False
                        break
            if not valid:
                return
            try:
                self.db_manager.delete_trade_monitor(values[0], values[1])
                self.db_manager.save_trade_monitor({
                    'item_name': new_vals[0],
                    'monitor_time': values[1],  # 时间不变
                    'quantity': int(new_vals[1]),
                    'market_price': float(new_vals[2]),
                    'target_price': float(new_vals[3]),
                    'planned_price': float(new_vals[4]),
                    'break_even_price': float(values[6]),  # 保本卖出价公式自动算
                    'profit': float(values[7]),            # 利润公式自动算
                    'profit_rate': float(str(values[8]).replace('%','')), # 利润率公式自动算
                    'strategy': new_vals[5]
                })
                self.refresh_monitor()
                edit_win.destroy()
            except Exception as e:
                error_labels[0].config(text=f"保存失败: {e}")

        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def add_monitor(self):
        """添加监控记录"""
        try:
            item = self.monitor_item.get()
            quantity = int(self.monitor_quantity.get())
            price = float(self.monitor_price.get())
            target_price = float(self.monitor_target_price.get())
            planned_price = float(self.monitor_planned_price.get())
            strategy = self.monitor_strategy.get()
            break_even_price = target_price * 1.05
            profit = price - target_price
            profit_rate = (profit / target_price) * 100
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db_manager.save_trade_monitor({
                'item_name': item,
                'monitor_time': now,
                'quantity': quantity,
                'market_price': price,
                'target_price': target_price,
                'planned_price': planned_price,
                'break_even_price': break_even_price,
                'profit': profit,
                'profit_rate': profit_rate,
                'strategy': strategy
            })
            self.refresh_monitor()
            self.monitor_item.delete(0, 'end')
            self.monitor_quantity.delete(0, 'end')
            self.monitor_price.delete(0, 'end')
            self.monitor_target_price.delete(0, 'end')
            self.monitor_planned_price.delete(0, 'end')
            self.monitor_strategy.delete(0, 'end')
            self.main_gui.log_operation('修改', '交易监控')
            messagebox.showinfo("成功", "监控记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def refresh_monitor(self):
        """刷新监控数据"""
        threading.Thread(target=self._fetch_and_draw_monitor, daemon=True).start()

    def _fetch_and_draw_monitor(self):
        """获取并绘制监控数据"""
        monitor_data = self.db_manager.get_trade_monitor()
        table_data = []
        formula_dict = {}
        try:
            import json
            import os
            if os.path.exists("field_formulas.json"):
                with open("field_formulas.json", "r", encoding="utf-8") as f:
                    formula_json = json.load(f)
                    formula_dict = formula_json.get("交易监控", {})
        except Exception as e:
            formula_dict = {}
        for item in monitor_data:
            try:
                _, item_name, monitor_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = item
                ctx = {
                    '物品': item_name,
                    '当前时间': monitor_time,
                    '数量': quantity,
                    '一口价': float(market_price),
                    '目标买入价': float(target_price),
                    '计划卖出价': float(planned_price),
                    '保本卖出价': float(break_even_price),
                    '利润': float(profit),
                    '利润率': float(profit_rate),
                    '出库策略': strategy
                }
                def calc_field(field, default_value):
                    formula = None
                    if field in formula_dict:
                        formulas = formula_dict[field]
                        if formulas:
                            formula = list(formulas.values())[0]
                    if not formula:
                        return default_value
                    try:
                        return eval(formula, {}, ctx)
                    except Exception:
                        return default_value
                break_even_price_val = calc_field('保本卖出价', float(break_even_price))
                profit_val = calc_field('利润', float(profit))
                profit_rate_val = calc_field('利润率', float(profit_rate))
                table_data.append((
                    item_name,
                    monitor_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(monitor_time, 'strftime') else str(monitor_time),
                    int(quantity),
                    str(int(round(float(market_price)))),
                    str(int(round(float(target_price)))),
                    str(int(round(float(planned_price)))),
                    str(int(round(float(break_even_price_val)))),
                    f"{profit_val:.2f}",
                    f"{profit_rate_val:.2f}%",
                    strategy
                ))
            except Exception as e:
                messagebox.showerror("数据结构异常", f"监控数据结构异常: {e}\n请检查表结构与代码字段一致性。\nitem={item}")
                continue
        self.main_gui.root.after(0, lambda: self._draw_monitor(table_data))

    def _draw_monitor(self, table_data):
        """绘制监控数据到表格"""
        for item in self.monitor_tree.get_children():
            self.monitor_tree.delete(item)
        for row in table_data:
            self.monitor_tree.insert('', 'end', values=row) 