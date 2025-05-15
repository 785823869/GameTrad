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
        """批量识别已添加的图片，弹出预览窗口，确认后批量导入（远程API识别）"""
        if not self._pending_ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
        import io, base64, requests
        all_data = []
        for img in self._pending_ocr_images:
            try:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                url = "http://sql.didiba.uk:1224/api/ocr"
                payload = {
                    "base64": img_b64,
                    "options": {
                        "data.format": "text"
                    }
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=20)
                resp.raise_for_status()
                ocr_result = resp.json()
                text = ocr_result.get('data')
                if not text:
                    continue
                data = self.parse_monitor_ocr_text(text)
                if isinstance(data, list):
                    all_data.extend(data)
                elif data:
                    all_data.append(data)
            except Exception as e:
                print(f"OCR识别失败: {e}")
        if all_data:
            # 预览窗口确认导入时，自动合并/更新物品
            def on_confirm(selected_data):
                # 先查已有监控表，构建物品名到记录的映射
                existing = {row[1]: row for row in self.db_manager.get_trade_monitor()}
                for row in selected_data:
                    item = row.get('item_name')
                    quantity = row.get('quantity')
                    price = row.get('market_price')
                    if not item:
                        continue
                    # 构造完整数据
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data = {
                        'item_name': item,
                        'monitor_time': now,
                        'quantity': quantity or 0,
                        'market_price': price or 0,
                        'target_price': 0,
                        'planned_price': 0,
                        'break_even_price': 0,
                        'profit': 0,
                        'profit_rate': 0,
                        'strategy': ''
                    }
                    # 已有则更新数量和一口价，否则新增
                    self.db_manager.save_trade_monitor(data)
                self.refresh_monitor()
                self.main_gui.log_operation('添加', '交易监控', selected_data)
            # 弹出预览窗口，columns和field_map适配交易监控
            self.main_gui.show_preview(
                all_data,
                columns=("物品", "数量", "一口价", "目标买入价", "计划卖出价", "保本卖出价", "利润", "利润率", "出库策略"),
                field_map={
                    "物品": "item_name",
                    "数量": "quantity",
                    "一口价": "market_price",
                    "目标买入价": "target_price",
                    "计划卖出价": "planned_price",
                    "保本卖出价": "break_even_price",
                    "利润": "profit",
                    "利润率": "profit_rate",
                    "出库策略": "strategy"
                },
                on_confirm=on_confirm
            )
        else:
            messagebox.showwarning("无有效数据", "未识别到有效的监控数据！")
        self._pending_ocr_images.clear()
        self.refresh_ocr_image_preview()

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
        """刷新OCR图片预览，风格与入库/出库一致"""
        for widget in self.ocr_image_preview_frame.winfo_children():
            widget.destroy()
        for idx, img in enumerate(self._pending_ocr_images):
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(thumb)
            lbl = ttk.Label(self.ocr_image_preview_frame, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=idx*2, padx=4, pady=2)
            btn = ttk.Button(self.ocr_image_preview_frame, text='删除', width=5, command=lambda i=idx: self.delete_ocr_image(i))
            btn.grid(row=1, column=idx*2, padx=4, pady=2)

    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            self._pending_ocr_images.pop(idx)
            self.refresh_ocr_image_preview()

    def parse_monitor_ocr_text(self, text):
        """
        交易监控OCR文本解析，严格用物品字典分割物品名，并与数量、一口价一一对应，缺失补空。
        若物品字典为空，自动弹窗提示。
        """
        import re
        try:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            # 1. 提取物品名行
            item_line = ''
            for idx, line in enumerate(lines):
                if line.startswith('物品'):
                    items_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['品质', '数量', '等级', '一口价']):
                            break
                        items_block.append(lines[j])
                    item_line = ''.join(items_block)
                    break
            # 2. 用物品字典分割物品名
            dict_items = self.main_gui.load_item_dict() if hasattr(self.main_gui, 'load_item_dict') else []
            if not dict_items:
                messagebox.showwarning(
                    "物品字典为空",
                    "物品字典未设置或内容为空，无法分割物品名。请在'物品字典管理'中添加物品名后重试。"
                )
                return []
            item_names = []
            pos = 0
            while pos < len(item_line):
                matched = False
                for name in sorted(dict_items, key=lambda x: -len(x)):
                    if item_line.startswith(name, pos):
                        item_names.append(name)
                        pos += len(name)
                        matched = True
                        break
                if not matched:
                    pos += 1
            # 3. 提取所有数量
            quantities = []
            for idx, line in enumerate(lines):
                if line.startswith('数量'):
                    qty_block = []
                    qty_block.append(line.replace('数量', '').strip())
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['一口价', '物品', '品质', '等级']):
                            break
                        qty_block.append(lines[j])
                    quantities = [int(x.replace(',', '')) for x in re.findall(r'[\d,]+', ' '.join(qty_block))]
                    break
            # 4. 提取所有一口价
            prices = []
            for idx, line in enumerate(lines):
                if line.startswith('一口价'):
                    price_block = []
                    price_block.append(line.replace('一口价', '').strip())
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['数量', '物品', '品质', '等级']):
                            break
                        price_block.append(lines[j])
                    prices = [int(x.replace(',', '')) for x in re.findall(r'[\d,]+', ' '.join(price_block))]
                    break
            n = len(item_names)
            result = []
            for i in range(n):
                result.append({
                    'item_name': item_names[i],
                    'quantity': quantities[i] if i < len(quantities) else '',
                    'market_price': prices[i] if i < len(prices) else '',
                    'note': 'OCR导入' if (i < len(quantities) and i < len(prices)) else '数据缺失'
                })
            if n == 0:
                messagebox.showwarning(
                    "数据不完整",
                    f"物品数：0，数量：{len(quantities)}，一口价：{len(prices)}。请检查OCR识别结果，部分数据可能丢失。"
                )
            elif not (n == len(quantities) == len(prices)):
                messagebox.showwarning(
                    "数据不完整",
                    f"物品数：{n}，数量：{len(quantities)}，一口价：{len(prices)}。请检查OCR识别结果，部分数据可能丢失。"
                )
            return result
        except Exception as e:
            print(f"解析交易监控OCR文本失败: {e}")
            return []

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