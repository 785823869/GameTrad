import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
from PIL import ImageGrab, ImageTk
import io, base64, requests
from datetime import datetime
import tkinter as tk

class StockInTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self._pending_ocr_images = []
        self.create_tab()

    def create_tab(self):
        stock_in_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(stock_in_frame, text="入库管理")
        columns = ('物品', '当前时间', '入库数量', '入库花费', '入库均价', '备注')
        self.stock_in_tree = ttk.Treeview(stock_in_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.stock_in_tree.heading(col, text=col, anchor='center')
            self.stock_in_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(stock_in_frame, orient="vertical", command=self.stock_in_tree.yview)
        self.stock_in_tree.configure(yscrollcommand=scrollbar.set)
        self.stock_in_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        self.stock_in_tree.tag_configure('total', background='#ffe066', font=('微软雅黑', 11, 'bold'))
        right_panel = ttk.Frame(stock_in_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        self.stock_in_filter_var = tb.StringVar()
        filter_row = ttk.Frame(right_panel)
        filter_row.pack(fill='x', pady=2)
        ttk.Label(filter_row, text="物品筛选:").pack(side='left')
        filter_entry = ttk.Entry(filter_row, textvariable=self.stock_in_filter_var, width=12)
        filter_entry.pack(side='left', padx=2)
        ttk.Button(filter_row, text="筛选", command=self.refresh_stock_in).pack(side='left', padx=2)
        add_frame = ttk.LabelFrame(right_panel, text="添加入库记录", padding=10)
        add_frame.pack(fill='x', pady=8)
        ttk.Label(add_frame, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        self.stock_in_item = ttk.Entry(add_frame)
        self.stock_in_item.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        self.stock_in_quantity = ttk.Entry(add_frame)
        self.stock_in_quantity.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="花费:").grid(row=2, column=0, padx=5, pady=5)
        self.stock_in_cost = ttk.Entry(add_frame)
        self.stock_in_cost.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="备注:").grid(row=3, column=0, padx=5, pady=5)
        self.stock_in_note = ttk.Entry(add_frame)
        self.stock_in_note.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        add_frame.columnconfigure(1, weight=1)
        ttk.Button(add_frame, text="添加入库", command=self.add_stock_in).grid(row=4, column=0, columnspan=2, pady=10, sticky='ew')
        ttk.Button(right_panel, text="刷新入库记录", command=self.refresh_stock_in).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动入库", command=self.upload_ocr_import_stock_in).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_in).pack(fill='x', pady=(0, 10), ipady=4)
        self.ocr_image_preview_frame = ttk.Frame(right_panel)
        self.ocr_image_preview_frame.pack(fill='x', pady=5)
        self.stock_in_menu = tb.Menu(self.stock_in_tree, tearoff=0)
        self.stock_in_menu.add_command(label="删除", command=self.delete_stock_in_item)
        self.stock_in_tree.bind("<Button-3>", self.show_stock_in_menu)
        self.stock_in_tree.bind('<Control-a>', lambda e: [self.stock_in_tree.selection_set(self.stock_in_tree.get_children()), 'break'])
        self.stock_in_tree.bind("<Double-1>", self.edit_stock_in_item)

    def refresh_stock_in(self):
        for item in self.stock_in_tree.get_children():
            self.stock_in_tree.delete(item)
        stock_in_data = self.db_manager.get_stock_in()
        filter_text = self.stock_in_filter_var.get().strip()
        filtered = []
        for item in stock_in_data:
            try:
                _, item_name, transaction_time, quantity, cost, avg_cost, note, *_ = item
            except Exception as e:
                messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nitem={item}")
                continue
            if not filter_text or filter_text in str(item_name):
                filtered.append((item_name, transaction_time, quantity, cost, avg_cost, note))
        total = [0, 0, 0]  # 数量、花费、均价合计
        for item_name, transaction_time, quantity, cost, avg_cost, note in filtered:
            self.stock_in_tree.insert('', 'end', values=(
                item_name,
                transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                int(quantity),
                int(round(cost)),
                int(round(avg_cost)),
                note if note is not None else ''
            ))
            try:
                total[0] += int(quantity)
                total[1] += int(round(cost))
                total[2] += int(round(avg_cost))
            except:
                pass
        # 合计行
        if filter_text and filtered:
            self.stock_in_tree.insert('', 'end', values=(
                '合计', '', total[0], total[1], total[2]//len(filtered), ''
            ), tags=('total',))

    def add_stock_in(self):
        try:
            item = self.stock_in_item.get()
            quantity = int(self.stock_in_quantity.get())
            cost = float(self.stock_in_cost.get())
            note = self.stock_in_note.get()
            avg_cost = cost / quantity
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db_manager.save_stock_in({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'cost': cost,
                'avg_cost': avg_cost,
                'deposit': 0.00,
                'note': note if note is not None else ''
            })
            self.db_manager.increase_inventory(item, quantity, avg_cost)
            self.refresh_stock_in()
            self.main_gui.refresh_inventory()
            self.stock_in_item.delete(0, 'end')
            self.stock_in_quantity.delete(0, 'end')
            self.stock_in_cost.delete(0, 'end')
            self.stock_in_note.delete(0, 'end')
            self.main_gui.log_operation('修改', '入库管理')
            messagebox.showinfo("成功", "入库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def edit_stock_in_item(self, event):
        item_id = self.stock_in_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.stock_in_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑入库记录")
        edit_win.minsize(420, 420)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "时间", "数量", "花费", "均价", "备注"]
        types = [str, str, int, float, float, str]
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
            except Exception:
                error_labels[2].config(text="数量/花费/均价必须为数字")
                entries[2].focus_set()
                return
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
            self.db_manager.delete_stock_in(values[0], values[1])
            self.db_manager.save_stock_in({
                'item_name': new_vals[0],
                'transaction_time': new_vals[1],
                'quantity': new_vals[2],
                'cost': new_vals[3],
                'avg_cost': new_vals[4],
                'note': new_vals[5]
            })
            self.refresh_stock_in()
            edit_win.destroy()
            self.main_gui.log_operation('修改', '入库管理', {'old': values, 'new': new_vals})
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def delete_stock_in_item(self):
        selected_items = self.stock_in_tree.selection()
        if not selected_items:
            return
        names = [self.stock_in_tree.item(item)['values'][0] for item in selected_items]
        times = [self.stock_in_tree.item(item)['values'][1] for item in selected_items]
        msg = "确定要删除以下入库记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item, name, t in zip(selected_items, names, times):
                values = self.stock_in_tree.item(item)['values']
                deleted_data.append(values)
                self.db_manager.delete_stock_in(name, t)
            self.refresh_stock_in()
            self.main_gui.log_operation('删除', '入库管理', deleted_data)
            messagebox.showinfo("成功", "已删除所选入库记录！")

    def refresh_ocr_image_preview(self):
        for widget in self.ocr_image_preview_frame.winfo_children():
            widget.destroy()
        for idx, img in enumerate(self._pending_ocr_images):
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            photo = ImageTk.PhotoImage(thumb)
            lbl = ttk.Label(self.ocr_image_preview_frame, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=idx*2, padx=4, pady=2)
            btn = ttk.Button(self.ocr_image_preview_frame, text='删除', width=5, command=lambda i=idx: self.delete_ocr_image(i))
            btn.grid(row=1, column=idx*2, padx=4, pady=2)

    def delete_ocr_image(self, idx):
        del self._pending_ocr_images[idx]
        self.refresh_ocr_image_preview()

    def upload_ocr_import_stock_in(self):
        file_paths = filedialog.askopenfilenames(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_paths:
            return
        try:
            from PIL import Image
            count = 0
            for file_path in file_paths:
                img = Image.open(file_path)
                self._pending_ocr_images.append(img)
                count += 1
            self.refresh_ocr_image_preview()
            messagebox.showinfo("已添加", f"已添加{count}张图片，点击批量识别可统一导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def batch_ocr_import_stock_in(self):
        if not self._pending_ocr_images:
            messagebox.showwarning("无图片", "请先粘贴图片")
            return
        all_preview_data = []
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
                parsed_data = self.parse_stock_in_ocr_text(text)
                if parsed_data:
                    if isinstance(parsed_data, list):
                        all_preview_data.extend(parsed_data)
                    else:
                        all_preview_data.append(parsed_data)
            except Exception as e:
                print(f"OCR识别失败: {e}")
        if all_preview_data:
            self.main_gui.show_preview(
                all_preview_data,
                columns=('物品', '入库数量', '入库花费', '入库均价', '备注'),
                field_map={
                    '物品': 'item_name',
                    '入库数量': 'quantity',
                    '入库花费': 'cost',
                    '入库均价': 'avg_cost',
                    '备注': 'note'
                }
            )
        else:
            messagebox.showwarning("无有效数据", "未识别到有效的入库数据！")
        self._pending_ocr_images.clear()
        self.refresh_ocr_image_preview()

    def parse_stock_in_ocr_text(self, text):
        import re
        try:
            total_cost = 0
            for cost_match in re.finditer(r'失去了银两[×xX*＊ ]*(\d+)', text):
                total_cost += int(cost_match.group(1))
            item_dict = {}
            for m in re.finditer(r'([\u4e00-\u9fa5a-zA-Z0-9]+)[×xX*＊ ]*(\d+)', text):
                item_name = m.group(1).strip()
                quantity = int(m.group(2))
                if item_name == "银两" or item_name.startswith("失去了银两"):
                    continue
                item_dict[item_name] = item_dict.get(item_name, 0) + quantity
            if not item_dict or total_cost == 0:
                return None
            if len(item_dict) == 1:
                item_name, quantity = list(item_dict.items())[0]
            else:
                item_name = '+'.join(item_dict.keys())
                quantity = sum(item_dict.values())
            avg_cost = int(round(total_cost / quantity)) if quantity else 0
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {
                'item_name': str(item_name),
                'transaction_time': now,
                'quantity': int(quantity),
                'cost': int(total_cost),
                'avg_cost': int(avg_cost),
                'note': 'OCR导入'
            }
        except Exception as e:
            print(f"解析入库OCR文本失败: {e}")
            return None

    def show_stock_in_menu(self, event):
        item = self.stock_in_tree.identify_row(event.y)
        if item:
            if item not in self.stock_in_tree.selection():
                self.stock_in_tree.selection_set(item)
            self.stock_in_menu.post(event.x_root, event.y_root)

    def paste_ocr_import_stock_in(self, event=None):
        img = ImageGrab.grabclipboard()
        if isinstance(img, list):
            img = img[0] if img else None
        if img is None or not hasattr(img, 'save'):
            messagebox.showwarning("粘贴失败", "剪贴板中没有图片")
            return
        self._pending_ocr_images.append(img)
        self.refresh_ocr_image_preview()
        messagebox.showinfo("已添加", f"已添加{len(self._pending_ocr_images)}张图片，点击批量识别可统一导入。")
    # ...后续补全所有入库管理相关方法... 