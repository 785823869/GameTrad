import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
from PIL import ImageGrab, ImageTk
import io, base64, requests
from datetime import datetime
import tkinter as tk

class StockOutTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self._pending_ocr_images_out = []
        self.create_tab()

    def create_tab(self):
        stock_out_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(stock_out_frame, text="出库管理")
        columns = ('物品', '当前时间', '数量', '单价', '手续费', '总金额', '备注')
        self.stock_out_tree = ttk.Treeview(stock_out_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.stock_out_tree.heading(col, text=col, anchor='center')
            self.stock_out_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(stock_out_frame, orient="vertical", command=self.stock_out_tree.yview)
        self.stock_out_tree.configure(yscrollcommand=scrollbar.set)
        self.stock_out_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        self.stock_out_tree.tag_configure('total', background='#ffe066', font=('微软雅黑', 11, 'bold'))
        right_panel = ttk.Frame(stock_out_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        self.stock_out_filter_var = tb.StringVar()
        filter_row = ttk.Frame(right_panel)
        filter_row.pack(fill='x', pady=2)
        ttk.Label(filter_row, text="物品筛选:").pack(side='left')
        filter_entry = ttk.Entry(filter_row, textvariable=self.stock_out_filter_var, width=12)
        filter_entry.pack(side='left', padx=2)
        ttk.Button(filter_row, text="筛选", command=self.refresh_stock_out).pack(side='left', padx=2)
        add_frame = ttk.LabelFrame(right_panel, text="添加出库", padding=10)
        add_frame.pack(fill='x', pady=8)
        ttk.Label(add_frame, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        self.stock_out_item = ttk.Entry(add_frame)
        self.stock_out_item.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        self.stock_out_quantity = ttk.Entry(add_frame)
        self.stock_out_quantity.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="单价:").grid(row=2, column=0, padx=5, pady=5)
        self.stock_out_price = ttk.Entry(add_frame)
        self.stock_out_price.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="手续费:").grid(row=3, column=0, padx=5, pady=5)
        self.stock_out_fee = ttk.Entry(add_frame)
        self.stock_out_fee.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="总金额:").grid(row=4, column=0, padx=5, pady=5)
        self.stock_out_total = ttk.Entry(add_frame)
        self.stock_out_total.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="备注:").grid(row=5, column=0, padx=5, pady=5)
        self.stock_out_note = ttk.Entry(add_frame)
        self.stock_out_note.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        add_frame.columnconfigure(1, weight=1)
        ttk.Button(add_frame, text="添加出库", command=self.add_stock_out).grid(row=6, column=0, columnspan=2, pady=10, sticky='ew')
        ttk.Button(right_panel, text="刷新出库记录", command=self.refresh_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动识别导入", command=self.upload_ocr_import_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        self.ocr_image_preview_frame_out = ttk.Frame(right_panel)
        self.ocr_image_preview_frame_out.pack(fill='x', pady=5)
        self.stock_out_menu = tb.Menu(self.stock_out_tree, tearoff=0)
        self.stock_out_menu.add_command(label="删除", command=self.delete_stock_out_item)
        self.stock_out_tree.bind("<Button-3>", self.show_stock_out_menu)
        self.stock_out_tree.bind('<Control-a>', lambda e: [self.stock_out_tree.selection_set(self.stock_out_tree.get_children()), 'break'])
        self.stock_out_tree.bind("<Double-1>", self.edit_stock_out_item)

    def add_stock_out(self):
        try:
            item = self.stock_out_item.get()
            quantity = int(self.stock_out_quantity.get())
            price = float(self.stock_out_price.get())
            fee = float(self.stock_out_fee.get())
            note = self.stock_out_note.get()
            total_amount = quantity * price - fee
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 自动减少库存
            success = self.db_manager.decrease_inventory(item, quantity)
            if not success:
                messagebox.showerror("错误", f"库存不足，无法出库 {item} 数量 {quantity}")
                return
            self.db_manager.save_stock_out({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'unit_price': price,
                'fee': fee,
                'deposit': 0.0,
                'total_amount': total_amount,
                'note': note if note is not None else ''
            })
            self.refresh_stock_out()
            self.main_gui.refresh_inventory()
            # 清空输入框
            self.stock_out_item.delete(0, 'end')
            self.stock_out_quantity.delete(0, 'end')
            self.stock_out_price.delete(0, 'end')
            self.stock_out_fee.delete(0, 'end')
            self.stock_out_note.delete(0, 'end')
            # 记录操作日志
            self.main_gui.log_operation('修改', '出库管理')
            messagebox.showinfo("成功", "出库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def refresh_stock_out(self):
        for item in self.stock_out_tree.get_children():
            self.stock_out_tree.delete(item)
        records = self.db_manager.get_stock_out()
        filter_text = self.stock_out_filter_var.get().strip().lower() if hasattr(self, 'stock_out_filter_var') else ''
        keywords = filter_text.split()
        filtered = []
        for record in records:
            try:
                _, item_name, transaction_time, quantity, unit_price, fee, deposit, total_amount, note, *_ = record
                name_lc = str(item_name).lower()
                if keywords and not all(k in name_lc for k in keywords):
                    continue
                values = (
                    item_name,
                    transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                    int(quantity),
                    int(float(unit_price)),
                    int(float(fee)),
                    int(float(total_amount)),
                    note if note is not None else ''
                )
                filtered.append(values)
                self.stock_out_tree.insert('', 'end', values=values)
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\nrecord={record}")
                continue
        # 合计行
        if filter_text and filtered:
            total_qty = sum(int(row[2]) for row in filtered)
            total_fee = sum(int(row[4]) for row in filtered)
            total_amount = sum(int(row[5]) for row in filtered)
            self.stock_out_tree.insert('', 'end', values=(
                '合计', '', total_qty, '', total_fee, total_amount, ''
            ), tags=('total',))

    def edit_stock_out_item(self, event):
        item_id = self.stock_out_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.stock_out_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑出库记录")
        edit_win.minsize(440, 440)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "时间", "数量", "单价", "手续费", "总金额", "备注"]
        types = [str, str, int, float, float, float, str]
        entries = []
        error_labels = []
        for i, (label, val, typ) in enumerate(zip(labels, values, types)):
            ttk.Label(content_frame, text=label+":", style='Edit.TLabel').grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            entry = ttk.Entry(content_frame, validate='key', validatecommand=vcmd, style='Edit.TEntry') if vcmd else ttk.Entry(content_frame, style='Edit.TEntry')
            entry.insert(0, val)
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
                new_vals[2] = int(new_vals[2])
                new_vals[3] = float(new_vals[3])
                new_vals[4] = float(new_vals[4])
                new_vals[5] = float(new_vals[5])
            except Exception:
                error_labels[2].config(text="数量/单价/手续费/总金额必须为数字")
                entries[2].focus_set()
                return
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
            self.db_manager.delete_stock_out(values[0], values[1])
            self.db_manager.save_stock_out({
                'item_name': new_vals[0],
                'transaction_time': new_vals[1],
                'quantity': new_vals[2],
                'unit_price': new_vals[3],
                'fee': new_vals[4],
                'deposit': 0.0,
                'total_amount': new_vals[5],
                'note': new_vals[6]
            })
            self.refresh_stock_out()
            edit_win.destroy()
            self.main_gui.log_operation('修改', '出库管理', {'old': values, 'new': new_vals})
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def refresh_ocr_image_preview_out(self):
        for widget in self.ocr_image_preview_frame_out.winfo_children():
            widget.destroy()
        for idx, img in enumerate(self._pending_ocr_images_out):
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            photo = ImageTk.PhotoImage(thumb)
            lbl = ttk.Label(self.ocr_image_preview_frame_out, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=idx*2, padx=4, pady=2)
            btn = ttk.Button(self.ocr_image_preview_frame_out, text='删除', width=5, command=lambda i=idx: self.delete_ocr_image_out(i))
            btn.grid(row=1, column=idx*2, padx=4, pady=2)

    def delete_ocr_image_out(self, idx):
        del self._pending_ocr_images_out[idx]
        self.refresh_ocr_image_preview_out()

    def paste_ocr_import_stock_out(self, event=None):
        img = ImageGrab.grabclipboard()
        if isinstance(img, list):
            img = img[0] if img else None
        if img is None or not hasattr(img, 'save'):
            messagebox.showwarning("粘贴失败", "剪贴板中没有图片")
            return
        self._pending_ocr_images_out.append(img)
        self.refresh_ocr_image_preview_out()
        messagebox.showinfo("已添加", f"已添加{len(self._pending_ocr_images_out)}张图片，点击批量识别可统一导入。")

    def batch_ocr_import_stock_out(self):
        if not self._pending_ocr_images_out:
            messagebox.showwarning("无图片", "请先粘贴图片")
            return
        all_preview_data = []
        for img in self._pending_ocr_images_out:
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
                parsed_data = self.parse_stock_out_ocr_text(text)
                if parsed_data:
                    all_preview_data.append(parsed_data)
            except Exception as e:
                print(f"OCR识别失败: {e}")
        if all_preview_data:
            self.main_gui.show_ocr_preview(
                all_preview_data,
                columns=('物品', '数量', '单价', '手续费', '总金额', '备注'),
                field_map=['item_name', 'quantity', 'unit_price', 'fee', 'total_amount', 'note']
            )
        else:
            messagebox.showwarning("无有效数据", "未识别到有效的出库数据！")
        self._pending_ocr_images_out.clear()
        self.refresh_ocr_image_preview_out()

    def show_stock_out_menu(self, event):
        item = self.stock_out_tree.identify_row(event.y)
        if item:
            if item not in self.stock_out_tree.selection():
                self.stock_out_tree.selection_set(item)
            self.stock_out_menu.post(event.x_root, event.y_root)

    def delete_stock_out_item(self):
        selected_items = self.stock_out_tree.selection()
        if not selected_items:
            return
        names = [self.stock_out_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下出库记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                values = self.stock_out_tree.item(item)['values']
                self.db_manager.delete_stock_out(values[0], values[1])
                deleted_data.append(values)
            self.refresh_stock_out()
            self.main_gui.log_operation('删除', '出库管理', deleted_data)

    def upload_ocr_import_stock_out(self):
        file_paths = fd.askopenfilenames(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_paths:
            return
        try:
            from PIL import Image
            count = 0
            for file_path in file_paths:
                img = Image.open(file_path)
                self._pending_ocr_images_out.append(img)
                count += 1
            self.refresh_ocr_image_preview_out()
            messagebox.showinfo("已添加", f"已添加{count}张图片，点击批量识别可统一导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def parse_stock_out_ocr_text(self, text):
        import re
        try:
            item_match = re.search(r'已成功售出([^（(]+)[（(](\d+)[）)]', text)
            if not item_match:
                return None
            item_name = item_match.group(1).strip()
            quantity = int(item_match.group(2))
            price_match = re.search(r'售出单价[:： ]*([0-9]+)银两', text)
            price = int(price_match.group(1)) if price_match else 0
            fee_match = re.search(r'手续费[:： ]*([0-9]+)银两', text)
            fee = int(fee_match.group(1)) if fee_match else 0
            total_amount = quantity * price - fee
            return {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': int(price),
                'fee': int(fee),
                'deposit': 0.0,
                'total_amount': int(total_amount),
                'note': 'OCR导入'
            }
        except Exception as e:
            print(f"解析出库OCR文本失败: {e}")
            return None

    # 其余方法：add_stock_out, refresh_stock_out, edit_stock_out_item, delete_stock_out_item, OCR相关等
    # ...（后续补全所有出库管理相关方法）... 